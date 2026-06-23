---
slug: deduplication-keys
title: Designing destination deduplication keys
product_area: data_integrity
version: "1.6"
status: current
published_at: 2026-05-15
---

# Designing destination deduplication keys

## Overview

Stable source event IDs are better deduplication keys than delivery attempt IDs. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Multiple deliveries share one event ID during replay or redrive workflows. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Attempt identifiers deliberately change for separately requested deliveries. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Persist the source event ID with a uniqueness rule at the destination. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Duplicate attempts return the original result without another write. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
