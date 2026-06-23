---
slug: export-timezones
title: Time zones in CSV exports
product_area: scheduling
version: "2.2"
status: current
published_at: 2026-05-15
---

# Time zones in CSV exports

## Overview

Machine-readable CSV exports always encode timestamps in UTC with an explicit offset; workspace time zone affects the dashboard only. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Export timestamps end in Z while dashboard timestamps are converted to the workspace zone. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

UTC makes exports stable across daylight saving changes and downstream systems. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Parse the ISO-8601 offset and convert downstream when local presentation is required; do not alter the workspace zone to change CSV output. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Converting the UTC timestamp yields the same instant shown in the dashboard. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
