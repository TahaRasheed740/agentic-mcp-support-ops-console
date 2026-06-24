# TraceDesk Visual System Map

This document explains TraceDesk visually: the main entities, the objects they
touch, and the flow through the whole system. It is written for someone who
wants to understand the project without reading the source code first.

## 1. One-Page System View

TraceDesk is a simulated AI support operations console. A support engineer opens
a ticket, starts an investigation, and the backend coordinates Claude, MCP tools,
retrieval, synthetic data, evidence capture, and human approvals.

```mermaid
flowchart LR
    User["Support engineer<br/>uses browser UI"]
    Web["Next.js web app<br/>support queue, cases, investigations, replays"]
    API["FastAPI backend<br/>sessions, cases, investigations, approvals"]
    Claude["Claude API<br/>router, specialists, investigator, synthesis"]
    DB[("PostgreSQL + pgvector<br/>synthetic product data, embeddings, events")]

    KMCP["Knowledge MCP<br/>docs, PDFs, hybrid search"]
    OMCP["Operations MCP<br/>integrations, runs, logs, incidents"]
    SMCP["Support MCP<br/>cases, personas, ticket overlays, approved writes"]

    User --> Web
    Web --> API
    API --> Claude
    API --> KMCP
    API --> OMCP
    API --> SMCP
    API --> DB
    KMCP --> DB
    OMCP --> DB
    SMCP --> DB
```

## 2. Main Entities And Objects

The project uses synthetic Acme Automations data. No company data or customer
data is used.

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ INTEGRATION : owns
    ORGANIZATION ||--o{ TICKET : opens
    INTEGRATION ||--o{ JOB_RUN : produces
    JOB_RUN ||--o{ LOG_ENTRY : contains
    ORGANIZATION ||--o{ INCIDENT : affected_by
    PLAN ||--o{ ORGANIZATION : assigned_to

    KNOWLEDGE_DOCUMENT ||--o{ KNOWLEDGE_CHUNK : chunked_into
    KNOWLEDGE_CHUNK ||--|| EMBEDDING : indexed_as

    DEMO_SESSION ||--o{ TICKET_OVERLAY : isolates_changes
    INVESTIGATION ||--o{ INVESTIGATION_EVENT : streams
    INVESTIGATION ||--o{ EVIDENCE : captures
    INVESTIGATION ||--o{ SPECIALIST_REPORT : includes
    INVESTIGATION ||--o{ PROPOSED_ACTION : queues

    TICKET ||--o{ INVESTIGATION : investigated_by
    EVIDENCE ||--o{ DIAGNOSIS : cited_by
```

In plain English:

- Organizations, users, integrations, tickets, runs, logs, and incidents make up
  the fake SaaS product.
- Knowledge documents are split into chunks and embedded for retrieval.
- Investigations store every event, evidence item, specialist report, diagnosis,
  and approval request.
- Session overlays let demo users approve/reject actions without changing the
  canonical seeded data.

## 3. Container And Service Layout

Docker Compose runs six main services.

```mermaid
flowchart TB
    subgraph Browser["Your browser"]
        UI["TraceDesk UI<br/>localhost:3000"]
    end

    subgraph Docker["Docker Compose stack"]
        Web["web<br/>Next.js"]
        API["api<br/>FastAPI"]
        Postgres[("postgres<br/>PostgreSQL 17 + pgvector")]
        Knowledge["knowledge-mcp<br/>documentation tools"]
        Operations["operations-mcp<br/>integration/log/incident tools"]
        Support["support-mcp<br/>case and approval tools"]
    end

    UI --> Web
    Web --> API
    API --> Knowledge
    API --> Operations
    API --> Support
    API --> Postgres
    Knowledge --> Postgres
    Operations --> Postgres
    Support --> Postgres
```

Service purpose:

| Container | Purpose |
| --- | --- |
| `web` | Browser UI for support queue, investigations, replays, knowledge search, tools, and evaluations. |
| `api` | Main coordinator: REST endpoints, sessions, investigations, SSE streaming, approvals, evaluation report access. |
| `postgres` | Stores synthetic data, embeddings, investigation events, evidence, actions, and traces. |
| `knowledge-mcp` | MCP server for `search_knowledge` and `get_document`. |
| `operations-mcp` | MCP server for integrations, recent runs, logs, and incidents. |
| `support-mcp` | MCP server for cases, personas, and approval-gated ticket writes. |

## 4. Support Engineer Flow

This is the normal product flow from the UI.

```mermaid
flowchart TD
    A["Open support queue"] --> B["Open a ticket"]
    B --> C["Review case details<br/>customer, integration, recent runs, incidents"]
    C --> D{"Need AI investigation?"}
    D -- No --> E["Use manual context and knowledge search"]
    D -- Yes --> F["Enter live access code if required<br/>then click Investigate with Claude"]
    F --> G["Live investigation workspace opens"]
    G --> H["Watch streamed agent timeline"]
    H --> I["Review evidence and citations"]
    I --> J["Review diagnosis and drafted response"]
    J --> K{"Any proposed action?"}
    K -- No --> L["Use diagnosis for support response"]
    K -- Yes --> M["Approve or reject action"]
    M --> N["Approved write updates session overlay only"]
```

## 5. Live Investigation Flow

This is the most important internal flow. Claude does not get direct database
access. It can only use scoped tools exposed by MCP.

```mermaid
sequenceDiagram
    participant UI as Web UI
    participant API as FastAPI
    participant Router as Claude Router
    participant Specs as Claude Specialists
    participant Inv as Claude Investigator
    participant MCP as MCP Services
    participant DB as PostgreSQL

    UI->>API: Start investigation for ticket with optional live access code
    API->>API: Check ANTHROPIC_API_KEY and production access-code gate
    alt Live access denied
        API-->>UI: Return protected-live-mode error
    else Live access allowed
    API->>MCP: support.get_case
    MCP->>DB: Read ticket and session overlay
    DB-->>MCP: Case context
    MCP-->>API: Case context

    API->>Router: Classify ticket and create plan
    Router-->>API: Category, urgency, allowed tools, steps
    API->>DB: Save classification, plan, event
    API-->>UI: Stream event over SSE

    par Documentation specialist
        API->>Specs: Docs-only investigation
        Specs->>MCP: search_knowledge / get_document
        MCP->>DB: Retrieve chunks and docs
        MCP-->>Specs: Evidence result
    and Account specialist
        API->>Specs: Account-only investigation
        Specs->>MCP: get_integration
        MCP->>DB: Read integration context
        MCP-->>Specs: Account result
    and Reliability specialist
        API->>Specs: Reliability-only investigation
        Specs->>MCP: incidents, runs, logs
        MCP->>DB: Read operations data
        MCP-->>Specs: Operations result
    end

    API->>DB: Store evidence and specialist reports
    API->>Inv: General investigation with allowed tools
    Inv->>MCP: Read-only MCP tool calls
    MCP-->>Inv: Tool results
    API->>DB: Store events, tool calls, evidence

    API->>Inv: Final synthesis with allowed evidence IDs
    Inv-->>API: Diagnosis, citations, proposed actions
    API->>DB: Validate citations and save result
    API-->>UI: Stream completed investigation
    end
```

## 6. Retrieval And Evidence Flow

TraceDesk uses hybrid retrieval: semantic search plus keyword search.

```mermaid
flowchart TD
    Docs["Markdown docs + generated PDFs"] --> Parse["Parse and chunk documents"]
    Parse --> Chunks["Knowledge chunks"]
    Chunks --> Embed["Local BGE embeddings"]
    Embed --> PGVector[("pgvector index")]
    Chunks --> BM25["BM25 lexical index"]

    Query["User or agent query"] --> Semantic["Semantic search"]
    Query --> Lexical["Keyword/BM25 search"]
    Semantic --> RRF["Reciprocal-rank fusion"]
    Lexical --> RRF
    RRF --> Results["Ranked evidence results"]
    Results --> Evidence["Captured evidence<br/>E1, E2, E3..."]
    Evidence --> Diagnosis["Diagnosis cites only captured IDs"]
```

Why this matters:

- Keyword search catches exact terms like `401`, `OAuth`, or `webhook`.
- Semantic search catches meaning even when wording differs.
- The final diagnosis can cite only captured evidence IDs.

## 7. Safety And Approval Flow

The system is designed so AI cannot directly mutate support state.

```mermaid
flowchart TD
    Agent["Claude agent proposes action"] --> Proposal["Create proposed action<br/>pending status"]
    Proposal --> UI["Show action in approval queue"]
    UI --> Decision{"Human decision"}
    Decision -- Reject --> Rejected["Mark rejected<br/>no write happens"]
    Decision -- Approve --> Token["API creates trusted approval context"]
    Token --> Tool["Support MCP write tool<br/>add note or update status"]
    Tool --> Guard{"Approval ID + scope + idempotency valid?"}
    Guard -- No --> Block["Block write"]
    Guard -- Yes --> Overlay["Write session overlay only"]
    Overlay --> Result["Persist action result and stream event"]
```

Important guardrails:

- Model-visible schemas remove trusted authorization fields.
- Write tools require approval context that only the backend can create.
- Writes affect isolated demo overlays, not canonical seed data.
- Replayed idempotency keys return stored results instead of duplicating writes.

## 8. Replay Mode Versus Live Mode

Replay mode is what should be public. Live mode costs API money and should be
protected.

```mermaid
flowchart LR
    Visitor["Visitor / recruiter"] --> Replay["Recorded replay mode"]
    Replay --> Frozen["Frozen investigation data<br/>no Claude call, no writes, no cost"]

    Reviewer["Trusted reviewer"] --> LiveGate{"Valid live access code<br/>and API key available?"}
    LiveGate -- No --> Replay
    LiveGate -- Yes --> Live["Live Claude investigation"]
    Live --> Cost["Uses Anthropic API key<br/>token cost and rate limits apply"]
```

Recommended deployment stance:

- Public: replay mode, docs, evaluation report, screenshots, demo video.
- Protected: live Claude investigations behind an access code or kept local.
- Never expose unrestricted live mode with a personal API key.

## 9. Evaluation And Hardening Flow

Evaluation is split into deterministic CI-safe grading and optional token-spending
model review.

```mermaid
flowchart TD
    Benchmarks["Benchmark cases<br/>expected category, evidence, root cause, tools, actions"] --> Eval["Deterministic evaluator"]
    Adversarial["Adversarial tickets<br/>prompt injection, fake citations, secret requests"] --> Eval
    Eval --> Metrics["Metrics"]
    Metrics --> Report["reports/evaluations/latest.md"]
    Eval --> SafeDefault["CI default<br/>no Claude call, no token spend"]

    Metrics --> A["classification accuracy"]
    Metrics --> B["required evidence recall"]
    Metrics --> C["citation validity"]
    Metrics --> D["tool-choice accuracy"]
    Metrics --> E["citation robustness"]
    Metrics --> F["unauthorized write prevention"]
    Metrics --> G["prompt-injection defense"]

    LiveRuns["Live investigation report"] --> Report
    ModelJudge["Optional Claude-as-judge<br/>manual --model-judge run"] --> Report
    Previous["Previous latest.json"] --> Regression["Regression comparison"]
    Regression --> Report
```

Current deterministic gates:

| Metric | Target |
| --- | ---: |
| Classification accuracy | 90%+ |
| Required evidence recall | 85%+ |
| Citation validity | 90%+ |
| Diagnosis acceptability | 80%+ |
| Tool-choice accuracy | 90%+ |
| Citation robustness | 100% |
| Unauthorized write prevention | 100% |

Optional model-based grading:

- Runs only when `--model-judge` is passed.
- Uses Claude to review benchmark outputs for helpfulness, grounding, citation
  quality, and action safety.
- Is intentionally manual so CI and public demos do not spend Anthropic tokens.

## 10. End-To-End Mental Model

```mermaid
flowchart TD
    Ticket["Synthetic support ticket"] --> Plan["Router classifies and plans"]
    Plan --> Tools["Specialists and investigator use MCP tools"]
    Tools --> Evidence["Evidence is captured with stable IDs"]
    Evidence --> Diagnosis["Final diagnosis cites captured evidence"]
    Diagnosis --> Action["Optional proposed actions"]
    Action --> Approval["Human approval required"]
    Approval --> Overlay["Approved writes go to session overlay"]
    Diagnosis --> Eval["Evaluation checks quality and safety"]
    Eval --> Portfolio["Replay + report + docs for portfolio"]
```

The shortest explanation:

> TraceDesk is not just a chatbot. It is a full support investigation system
> where Claude can use controlled tools, collect evidence, cite sources, propose
> safe actions, and get evaluated against benchmark cases.
