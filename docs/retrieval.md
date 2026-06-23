# Knowledge retrieval

## Purpose

Iteration 2 gives TraceDesk an inspectable evidence layer before an agent is
introduced. Every diagnosis in later iterations must cite a source returned by
this layer instead of relying only on model memory.

The corpus is entirely fictional and contains no employer or customer data.
Its source catalog lives in `knowledge/catalog.yaml`; benchmark truth lives in
`knowledge/benchmarks/v1.yaml`.

## Corpus

The generator creates 38 versioned Markdown documents and two two-page PDFs.
The sources cover authentication, delivery, scheduling, billing, data mapping,
rate limits, reliability, retention, and support operations. Five Markdown
documents are deliberately superseded so ranking and evidence displays can
distinguish current guidance from plausible distractors.

Documents are parsed into chunks targeting 300 to 600 estimated tokens. The
current compact articles each fit in one chunk. The same parser creates
multiple chunks automatically when longer documents are added.

## Retrieval pipeline

1. `BAAI/bge-small-en-v1.5` creates 384-dimensional embeddings locally through
   FastEmbed. No ticket or document text is sent to an external model.
2. pgvector ranks chunks by cosine distance.
3. BM25 ranks the same chunks by lexical relevance.
4. Reciprocal-rank fusion combines both rankings. Superseded sources receive a
   penalty but remain visible when they are relevant.
5. The API returns the fused score and contributing ranks so retrieval is
   explainable in the UI and evaluation report.

## Benchmark contract

The 15 benchmark cases bind existing deterministic tickets to an expected
category and root cause, one or more required sources, allowed tools, expected
actions, and prohibited claims. Evaluation queries use the actual seeded ticket
subject and description rather than benchmark-only phrasing.

The Iteration 2 gate is at least 90% of cases finding all required sources in
the top eight hybrid results. `reports/retrieval/latest.json` records every
retrieved source rather than only the aggregate score.

## Current boundaries

- Retrieval is evidence discovery, not a diagnosis. Agent planning, synthesis,
  and citation validation begin in Iteration 4.
- Corpus sources currently resolve to stable source identifiers and paths; a
  dedicated document viewer is part of the later product-experience work.
- The API currently owns retrieval directly. Iteration 3 moves simulated-system
  access behind typed MCP services.
- The embedding model needs network access on its first run. Docker caches the
  downloaded files in the `embedding_model_cache` volume afterward.
