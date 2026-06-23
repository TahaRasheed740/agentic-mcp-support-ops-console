---
slug: usage-quotas
title: Monthly run quotas and usage calculation
product_area: billing
version: "4.0"
status: current
published_at: 2026-05-15
---

# Monthly run quotas and usage calculation

## Overview

Quota usage counts every started production run, including failed and manually retried runs; sandbox runs do not count. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Billing usage exceeds a customer-created success report because failed starts and retries were omitted from that report. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Monthly allowance is metered at run start to provide consistent enforcement across destinations. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Compare the billing period, include failed and retried production runs, and confirm the organization plan rather than an integration label. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The reconstructed production-run count matches the usage meter within the documented processing delay. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
