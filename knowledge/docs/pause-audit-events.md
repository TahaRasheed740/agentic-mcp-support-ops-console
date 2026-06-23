---
slug: pause-audit-events
title: Reading pause audit events
product_area: configuration
version: "1.9"
status: current
published_at: 2026-05-15
---

# Reading pause audit events

## Overview

Audit events distinguish user actions, API actions, system auto-pause, and policy enforcement. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Actor, reason code, and correlation ID identify the trigger. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Display timestamps alone cannot establish who initiated a pause. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Inspect actor and reason before resuming. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The resolved cause matches preceding run failures. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
