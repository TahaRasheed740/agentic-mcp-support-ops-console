from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from tracedesk_api.config import get_settings
from tracedesk_api.data_factory import SeedDataset, build_seed_dataset
from tracedesk_api.database import create_engine
from tracedesk_api.models import (
    DemoSession,
    Incident,
    Integration,
    JobRun,
    LogEntry,
    Organization,
    Plan,
    SupportPersona,
    Ticket,
    TicketOverlay,
    User,
)

CANONICAL_DELETE_ORDER: Sequence[type[Any]] = (
    TicketOverlay,
    DemoSession,
    LogEntry,
    Ticket,
    JobRun,
    Integration,
    User,
    Organization,
    Incident,
    SupportPersona,
    Plan,
)


async def seed_database(*, force: bool = False) -> tuple[bool, dict[str, int]]:
    dataset = build_seed_dataset()
    engine = create_engine(get_settings())
    try:
        async with engine.begin() as connection:
            existing = await connection.scalar(select(func.count()).select_from(Organization))
            if existing and not force:
                return False, dataset.counts()
            if force:
                await _clear_seed_data(connection)
            await _insert_dataset(connection, dataset)
        return True, dataset.counts()
    finally:
        await engine.dispose()


async def _clear_seed_data(connection: AsyncConnection) -> None:
    for model in CANONICAL_DELETE_ORDER:
        await connection.execute(delete(model))


async def _insert_dataset(connection: AsyncConnection, dataset: SeedDataset) -> None:
    inserts: Sequence[tuple[type[Any], list[dict[str, Any]]]] = (
        (Plan, dataset.plans),
        (Organization, dataset.organizations),
        (User, dataset.users),
        (Integration, dataset.integrations),
        (Incident, dataset.incidents),
        (JobRun, dataset.job_runs),
        (LogEntry, dataset.log_entries),
        (Ticket, dataset.tickets),
        (SupportPersona, dataset.personas),
    )
    for model, rows in inserts:
        await connection.execute(insert(model), rows)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the deterministic Acme Automations dataset.")
    parser.add_argument("--force", action="store_true", help="Replace canonical and demo data.")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable result.")
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    changed, counts = await seed_database(force=args.force)
    result = {"seeded": changed, "counts": counts}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        action = "Seeded" if changed else "Skipped existing"
        print(f"{action} Acme Automations dataset: {counts}")


if __name__ == "__main__":
    asyncio.run(_main())
