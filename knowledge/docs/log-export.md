---
slug: log-export
title: Exporting logs for long-term retention
product_area: retention
version: "1.3"
status: current
published_at: 2026-05-15
---

# Exporting logs for long-term retention

## Overview

Scheduled exports can send redacted run metadata to customer-controlled storage before plan retention expires. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Export jobs show the destination bucket and most recent checkpoint. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Acme retention controls primary logs, not customer copies. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Configure a least-privilege destination and test retrieval. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Exported records remain accessible after Acme retention expires. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
