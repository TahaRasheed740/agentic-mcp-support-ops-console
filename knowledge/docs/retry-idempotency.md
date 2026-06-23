---
slug: retry-idempotency
title: Preventing duplicate records during retries
product_area: data_integrity
version: "2.5"
status: current
published_at: 2026-05-15
---

# Preventing duplicate records during retries

## Overview

Acme preserves its delivery ID across automatic retries, but a manual replay creates a new delivery unless the destination uses the event id as an idempotency key. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Downstream duplicates have different delivery IDs but the same source event ID after a manual replay. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Replays are intentional new delivery attempts and cannot guarantee downstream deduplication without destination support. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Compare source event and delivery IDs, stop further replays, deduplicate downstream, and configure the event ID as the destination idempotency key. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Replaying a controlled event leaves one downstream record and records the duplicate request as already processed. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
