---
slug: legacy-log-retention
title: Legacy thirty-day log retention
product_area: retention
version: "1.1"
status: superseded
published_at: 2026-05-15
superseded_by: log-retention
---

# Legacy thirty-day log retention

> **Superseded guidance.** This page is retained for retrieval testing and historical context. Do not use it for a current customer recommendation.

## Overview

This retired policy stated that every organization retained logs for thirty days. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

It does not mention plan-specific retention. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Retention became plan-based after storage policy changes. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Use the current Log retention by plan page. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The organization plan determines the boundary. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
