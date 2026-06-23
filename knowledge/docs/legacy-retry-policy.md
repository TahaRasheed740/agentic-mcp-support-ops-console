---
slug: legacy-retry-policy
title: Legacy fixed retry timing
product_area: reliability
version: "1.0"
status: superseded
published_at: 2026-05-15
superseded_by: destination-rate-limits
---

# Legacy fixed retry timing

> **Superseded guidance.** This page is retained for retrieval testing and historical context. Do not use it for a current customer recommendation.

## Overview

This retired policy used a fixed five-minute retry interval for all retryable responses. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The page describes behavior before exponential backoff was introduced. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Fixed retries caused synchronized load and ignored Retry-After. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Do not use this page for current investigations; follow Destination rate limits and retry backoff. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Current runs display variable retry intervals. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
