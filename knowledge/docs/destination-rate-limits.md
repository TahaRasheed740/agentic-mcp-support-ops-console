---
slug: destination-rate-limits
title: Destination rate limits and retry backoff
product_area: rate_limits
version: "3.3"
status: current
published_at: 2026-05-15
---

# Destination rate limits and retry backoff

## Overview

HTTP 429 responses are retried with exponential backoff and jitter, honoring Retry-After when it is valid. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Runs show RATE_LIMITED, attempts are spaced progressively farther apart, and the destination supplies a quota response. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

The downstream service is accepting fewer requests than the integration currently emits. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Inspect Retry-After, reduce concurrency or batch size, and do not manually retry while an automatic retry is scheduled. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Later attempts succeed without overlapping manual retries and destination quota metrics remain below the limit. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
