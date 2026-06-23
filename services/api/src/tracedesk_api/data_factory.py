from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

SEED = 20260622
REFERENCE_TIME = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class SeedDataset:
    plans: list[dict[str, Any]]
    organizations: list[dict[str, Any]]
    users: list[dict[str, Any]]
    integrations: list[dict[str, Any]]
    incidents: list[dict[str, Any]]
    job_runs: list[dict[str, Any]]
    log_entries: list[dict[str, Any]]
    tickets: list[dict[str, Any]]
    personas: list[dict[str, Any]]

    def counts(self) -> dict[str, int]:
        return {
            "plans": len(self.plans),
            "organizations": len(self.organizations),
            "users": len(self.users),
            "integrations": len(self.integrations),
            "incidents": len(self.incidents),
            "job_runs": len(self.job_runs),
            "log_entries": len(self.log_entries),
            "tickets": len(self.tickets),
            "personas": len(self.personas),
        }


PLAN_DATA = [
    ("starter", "Starter", 10_000, 7, "standard"),
    ("growth", "Growth", 100_000, 30, "priority"),
    ("scale", "Scale", 1_000_000, 90, "priority"),
    ("enterprise", "Enterprise", 10_000_000, 365, "dedicated"),
]

COMPANY_PREFIXES = [
    "Northstar",
    "Bluebird",
    "Cedar",
    "Juniper",
    "Copper",
    "Beacon",
    "Summit",
    "Harbor",
    "Atlas",
    "Lattice",
    "Mosaic",
    "Evergreen",
    "Pioneer",
    "Quartz",
    "Orbit",
]
COMPANY_SUFFIXES = ["Labs", "Systems", "Health", "Commerce"]
FIRST_NAMES = ["Ava", "Noah", "Maya", "Ethan", "Zara", "Owen", "Lina", "Caleb"]
LAST_NAMES = ["Shah", "Morgan", "Chen", "Patel", "Reyes", "Kim", "Ali", "Foster"]
INTEGRATION_KINDS = ["webhook", "salesforce", "stripe", "slack", "s3", "http_api"]

TICKET_SCENARIOS = [
    (
        "Webhook deliveries failing with 401 responses",
        "authentication",
        "high",
        "Our production webhook started returning 401 responses after yesterday's credential rotation. No payloads have reached the destination since 09:20 UTC.",
    ),
    (
        "Scheduled export did not run this morning",
        "scheduling",
        "normal",
        "The daily customer export normally runs at 08:00 local time, but there is no run for today. The schedule still appears enabled in the dashboard.",
    ),
    (
        "OAuth connection shows as expired",
        "authentication",
        "high",
        "Our Salesforce connection is marked expired and retries are failing. We reauthorized it last week and need to know why it disconnected again.",
    ),
    (
        "Monthly automation quota reached unexpectedly",
        "billing",
        "normal",
        "The workspace says it exhausted its monthly run quota, although our usage report appears substantially lower than the plan allowance.",
    ),
    (
        "Payload mapping changed after schema update",
        "data_mapping",
        "high",
        "New events contain a nested customer object and the existing mapping now writes empty email fields. Historical payloads still process correctly.",
    ),
    (
        "Integration is paused but no one paused it",
        "configuration",
        "normal",
        "A production integration changed to paused overnight. Our audit view does not show a team member making that change.",
    ),
    (
        "High latency on EU webhook deliveries",
        "reliability",
        "urgent",
        "Webhook delivery latency in the EU region increased from seconds to more than twelve minutes. US deliveries appear normal.",
    ),
    (
        "Destination returns rate limit errors",
        "rate_limits",
        "high",
        "Runs are failing with 429 errors from the destination. We need to confirm whether TraceDesk retries these automatically and at what interval.",
    ),
    (
        "Duplicate records created after retry",
        "data_integrity",
        "urgent",
        "A failed batch was retried and created duplicate invoices downstream. Please help identify which runs were replayed and whether idempotency keys were preserved.",
    ),
    (
        "Logs disappeared sooner than expected",
        "retention",
        "normal",
        "We can only view seven days of run logs, but our team expected thirty days based on the workspace plan shown in billing.",
    ),
    (
        "Signature verification fails for one endpoint",
        "authentication",
        "high",
        "One endpoint reports invalid HMAC signatures while another endpoint using the same workspace secret succeeds. Failures began after changing the endpoint URL.",
    ),
    (
        "Test events are reaching production",
        "configuration",
        "urgent",
        "Events sent from the sandbox integration appear in our production destination. The connection labels look correct, so we need help tracing the route.",
    ),
    (
        "CSV export contains the wrong timezone",
        "scheduling",
        "normal",
        "Timestamps in downloaded exports are UTC even though the workspace timezone is configured for America/New_York.",
    ),
    (
        "Intermittent 502 errors from delivery workers",
        "reliability",
        "high",
        "Roughly one in twenty webhook runs failed with a 502 during the last hour. Manual retries succeeded without changing the payload.",
    ),
    (
        "Cannot enable enterprise SSO settings",
        "plan_access",
        "low",
        "The security page advertises SSO, but the enable control is disabled for workspace administrators. Please confirm whether our current plan includes it.",
    ),
]


def build_seed_dataset(seed: int = SEED) -> SeedDataset:
    rng = random.Random(seed)
    plans = [
        {
            "id": plan_id,
            "name": name,
            "monthly_run_limit": limit,
            "retention_days": retention,
            "support_tier": support,
        }
        for plan_id, name, limit, retention, support in PLAN_DATA
    ]

    organizations: list[dict[str, Any]] = []
    users: list[dict[str, Any]] = []
    for index in range(60):
        org_number = index + 1
        name = f"{COMPANY_PREFIXES[index % 15]} {COMPANY_SUFFIXES[index // 15]}"
        org_id = f"org_{org_number:03d}"
        organizations.append(
            {
                "id": org_id,
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "plan_id": PLAN_DATA[(index * 7) % 4][0],
                "region": ["us-east", "us-west", "eu-west", "ap-south"][index % 4],
                "status": "active" if index not in {17, 42} else "past_due",
                "created_at": REFERENCE_TIME - timedelta(days=240 + index * 9),
            }
        )
        for user_index, role in enumerate(("owner", "admin", "developer", "viewer")):
            first = FIRST_NAMES[(index + user_index) % len(FIRST_NAMES)]
            last = LAST_NAMES[(index * 3 + user_index) % len(LAST_NAMES)]
            users.append(
                {
                    "id": f"usr_{org_number:03d}_{user_index + 1}",
                    "organization_id": org_id,
                    "name": f"{first} {last}",
                    "email": f"{first}.{last}.{org_number}@example.test".lower(),
                    "role": role,
                    "status": "active",
                }
            )

    integrations: list[dict[str, Any]] = []
    for index in range(150):
        integration_number = index + 1
        org_number = (index % 60) + 1
        kind = INTEGRATION_KINDS[index % len(INTEGRATION_KINDS)]
        integrations.append(
            {
                "id": f"int_{integration_number:03d}",
                "organization_id": f"org_{org_number:03d}",
                "name": f"{kind.replace('_', ' ').title()} {1 + index // 60}",
                "kind": kind,
                "status": "degraded" if index % 29 == 0 else "connected",
                "environment": "sandbox" if index % 7 == 0 else "production",
                "last_seen_at": REFERENCE_TIME - timedelta(minutes=index * 3),
            }
        )

    incidents = _build_incidents()
    job_runs, log_entries = _build_telemetry(rng, integrations)
    tickets = _build_tickets(integrations)
    personas = [
        {
            "id": "persona_maya",
            "name": "Maya Chen",
            "role": "Senior Support Engineer",
            "initials": "MC",
            "specialty": "APIs and authentication",
        },
        {
            "id": "persona_jordan",
            "name": "Jordan Lee",
            "role": "Reliability Specialist",
            "initials": "JL",
            "specialty": "Incidents and delivery infrastructure",
        },
        {
            "id": "persona_samira",
            "name": "Samira Khan",
            "role": "Customer Operations Engineer",
            "initials": "SK",
            "specialty": "Plans, configuration, and workflows",
        },
    ]
    return SeedDataset(
        plans,
        organizations,
        users,
        integrations,
        incidents,
        job_runs,
        log_entries,
        tickets,
        personas,
    )


def _build_incidents() -> list[dict[str, Any]]:
    titles = [
        "Elevated EU delivery latency",
        "Intermittent webhook worker errors",
        "Delayed scheduled jobs",
        "Salesforce token refresh failures",
        "US East log ingestion delay",
        "S3 export queue backlog",
        "Dashboard status lag",
        "Stripe connector degradation",
        "API rate limiter instability",
        "Email notification delay",
    ]
    incidents: list[dict[str, Any]] = []
    for index, title in enumerate(titles):
        started_at = REFERENCE_TIME - timedelta(days=index * 4 + 1, hours=index)
        active = index == 0
        incidents.append(
            {
                "id": f"inc_{index + 1:03d}",
                "title": title,
                "status": "monitoring" if active else "resolved",
                "severity": "sev2" if index in {0, 1, 3} else "sev3",
                "region": ["eu-west", "global", "us-east", "ap-south"][index % 4],
                "started_at": started_at,
                "resolved_at": None if active else started_at + timedelta(hours=2 + index),
                "summary": f"Acme Automations identified {title.lower()} and applied mitigation while monitoring recovery.",
            }
        )
    return incidents


def _build_telemetry(
    rng: random.Random, integrations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    job_runs: list[dict[str, Any]] = []
    log_entries: list[dict[str, Any]] = []
    error_codes = ["DESTINATION_401", "RATE_LIMITED", "UPSTREAM_502", "SCHEMA_MISMATCH"]
    for index in range(6_000):
        run_number = index + 1
        integration = integrations[index % len(integrations)]
        failed = index % 17 == 0 or (integration["status"] == "degraded" and index % 5 == 0)
        error_code = error_codes[index % len(error_codes)] if failed else None
        started_at = REFERENCE_TIME - timedelta(minutes=index * 8)
        run_id = f"run_{run_number:05d}"
        job_runs.append(
            {
                "id": run_id,
                "integration_id": integration["id"],
                "status": "failed" if failed else "succeeded",
                "started_at": started_at,
                "duration_ms": rng.randint(180, 15_000),
                "error_code": error_code,
                "records_processed": 0 if failed else rng.randint(1, 5_000),
            }
        )
        log_entries.append(
            {
                "id": f"log_{run_number:05d}_1",
                "job_run_id": run_id,
                "occurred_at": started_at,
                "level": "info",
                "message": f"Started {integration['kind']} delivery for {integration['environment']} environment.",
            }
        )
        if index < 3_000:
            log_entries.append(
                {
                    "id": f"log_{run_number:05d}_2",
                    "job_run_id": run_id,
                    "occurred_at": started_at + timedelta(milliseconds=500),
                    "level": "error" if failed else "info",
                    "message": f"Delivery failed with {error_code}."
                    if failed
                    else "Delivery completed successfully.",
                }
            )
    return job_runs, log_entries


def _build_tickets(integrations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tickets: list[dict[str, Any]] = []
    statuses = ["open", "open", "pending", "investigating", "resolved"]
    for index in range(75):
        scenario = TICKET_SCENARIOS[index % len(TICKET_SCENARIOS)]
        integration = integrations[(index * 11) % len(integrations)]
        org_number = int(integration["organization_id"].split("_")[1])
        created_at = REFERENCE_TIME - timedelta(hours=index * 5 + 1)
        tickets.append(
            {
                "id": f"TKT-{1001 + index}",
                "organization_id": integration["organization_id"],
                "integration_id": integration["id"],
                "requester_id": f"usr_{org_number:03d}_{(index % 4) + 1}",
                "subject": scenario[0],
                "description": scenario[3],
                "status": statuses[index % len(statuses)],
                "priority": scenario[2],
                "category": scenario[1],
                "created_at": created_at,
                "updated_at": created_at + timedelta(minutes=20 + index),
            }
        )
    return tickets
