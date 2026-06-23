import hashlib
import json

from tracedesk_api.data_factory import SEED, build_seed_dataset


def _fingerprint() -> str:
    dataset = build_seed_dataset(SEED)
    payload = {
        "counts": dataset.counts(),
        "organizations": dataset.organizations,
        "integrations": dataset.integrations,
        "tickets": dataset.tickets,
        "last_run": dataset.job_runs[-1],
        "last_log": dataset.log_entries[-1],
    }
    serialized = json.dumps(payload, default=str, sort_keys=True).encode()
    return hashlib.sha256(serialized).hexdigest()


def test_seed_dataset_has_agreed_scale() -> None:
    dataset = build_seed_dataset()

    assert dataset.counts() == {
        "plans": 4,
        "organizations": 60,
        "users": 240,
        "integrations": 150,
        "incidents": 10,
        "job_runs": 6_000,
        "log_entries": 9_000,
        "tickets": 75,
        "personas": 3,
    }


def test_seed_dataset_is_deterministic() -> None:
    assert _fingerprint() == "6db3e04163acb17ec66a9f636cad9872f103a77bd228479377034aa54ce5649c"


def test_seed_references_are_valid() -> None:
    dataset = build_seed_dataset()
    organization_ids = {row["id"] for row in dataset.organizations}
    user_ids = {row["id"] for row in dataset.users}
    integration_ids = {row["id"] for row in dataset.integrations}
    run_ids = {row["id"] for row in dataset.job_runs}

    assert all(row["organization_id"] in organization_ids for row in dataset.users)
    assert all(row["organization_id"] in organization_ids for row in dataset.integrations)
    assert all(row["integration_id"] in integration_ids for row in dataset.job_runs)
    assert all(row["job_run_id"] in run_ids for row in dataset.log_entries)
    assert all(row["requester_id"] in user_ids for row in dataset.tickets)
    assert all(row["integration_id"] in integration_ids for row in dataset.tickets)
