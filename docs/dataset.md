# Acme Automations dataset

## Purpose

The synthetic dataset makes TraceDesk independently reproducible and gives
future retrieval and agent evaluations known evidence. It contains no company
data, real customer data, or real email addresses.

## Canonical records

| Entity | Count |
| --- | ---: |
| Plans | 4 |
| Organizations | 60 |
| Users | 240 |
| Integrations | 150 |
| Job runs | 6,000 |
| Log entries | 9,000 |
| Tickets | 75 |
| Incidents | 10 |
| Support personas | 3 |

The fixed seed is `20260622` and the reference time is June 15, 2026 at 12:00
UTC. Tests pin both entity counts and a stable content fingerprint.

## Support scenarios

Tickets cover authentication, scheduling, billing, mappings, configuration,
reliability, rate limits, data integrity, retention, and plan access. Repeated
scenario families appear across different organizations and operational
contexts so future investigations cannot rely only on a ticket subject.

## Session isolation

Canonical records are shared and read-only during demonstrations. A demo
session is selected through a signed, HTTP-only cookie. Future ticket changes
are stored in `ticket_overlays`, keyed by session and ticket. Resetting a
session deletes only its overlays and records the reset time.

Running the seed command with `--force` is an administrative development action
that replaces canonical data and removes all demo sessions.

