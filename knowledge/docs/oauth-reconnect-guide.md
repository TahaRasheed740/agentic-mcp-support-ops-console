---
slug: oauth-reconnect-guide
title: Safe OAuth reconnection
product_area: authentication
version: "1.7"
status: current
published_at: 2026-05-15
---

# Safe OAuth reconnection

## Overview

Reconnection replaces stored tokens but retains mappings and integration identity. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The provider consent screen displays the account that will own future runs. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Acme never asks operators to paste provider refresh tokens manually. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Pause new work, reconnect the intended account, validate scopes, then resume. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

A scoped test request succeeds for the intended tenant. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
