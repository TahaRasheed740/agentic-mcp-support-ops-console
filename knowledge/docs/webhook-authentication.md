---
slug: webhook-authentication
title: Webhook authentication failures after secret rotation
product_area: authentication
version: "2.2"
status: current
published_at: 2026-05-15
---

# Webhook authentication failures after secret rotation

## Overview

A 401 immediately after credential rotation usually means the destination still validates the previous shared secret. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Repeated DESTINATION_401 results begin at the rotation timestamp while network delivery remains healthy. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Acme activates a new signing secret immediately; destinations must update the matching secret and cannot retrieve its plaintext later. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Confirm the integration and endpoint, compare the first failed run with the audit event, update the destination secret, then replay one failed delivery. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

A new test delivery returns a 2xx response and its signature validates with the new secret. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
