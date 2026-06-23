---
slug: api-key-rotation
title: API key rotation without downtime
product_area: authentication
version: "1.4"
status: current
published_at: 2026-05-15
---

# API key rotation without downtime

## Overview

API keys support an overlap window, unlike webhook signing-secret rotation, so clients can migrate before revocation. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Requests identify the old key fingerprint while both keys remain active. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Key rotation is designed as a staged client migration. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Create a second key, deploy it, verify usage, then revoke the old fingerprint. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

No requests use the old key before revocation. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
