---
slug: automatic-pauses
title: Why Acme automatically pauses an integration
product_area: configuration
version: "2.3"
status: current
published_at: 2026-05-15
---

# Why Acme automatically pauses an integration

## Overview

Acme automatically pauses an integration after twenty consecutive permanent failures to protect the destination and customer quota. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The audit actor is system:auto-pause and the preceding runs share a permanent authentication or configuration error. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Permanent failures cannot recover through backoff, so the circuit breaker stops new work until an operator intervenes. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Resolve the underlying permanent error, acknowledge the pause, resume the integration, and send one test event. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The integration remains connected and the consecutive permanent-failure counter returns to zero. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
