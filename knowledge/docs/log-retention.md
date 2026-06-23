---
slug: log-retention
title: Log retention by plan
product_area: retention
version: "4.1"
status: current
published_at: 2026-05-15
---

# Log retention by plan

## Overview

Starter retains seven days, Growth thirty days, Scale ninety days, and Enterprise three hundred sixty-five days of run logs. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Older logs disappear exactly at the plan boundary while aggregate usage remains available. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Detailed payload and execution logs are deleted according to the current organization plan, not the plan at run creation. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Confirm the organization plan and retention boundary, then use scheduled log export when longer external retention is required. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The earliest visible log aligns with the documented plan boundary in UTC. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
