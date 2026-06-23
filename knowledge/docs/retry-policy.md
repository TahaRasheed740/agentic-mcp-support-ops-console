---
slug: retry-policy
title: Retry classification policy
product_area: reliability
version: "2.8"
status: current
published_at: 2026-05-15
---

# Retry classification policy

## Overview

Timeouts, 429, and most 5xx responses are transient; authentication and validation 4xx responses are permanent. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The run records a retry classification and next-attempt time. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Retrying permanent errors wastes quota and increases destination load. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Resolve permanent errors before manual replay and allow automatic handling for transient errors. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The chosen action matches the recorded classification. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
