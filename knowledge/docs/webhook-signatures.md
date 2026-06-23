---
slug: webhook-signatures
title: Debugging webhook signature verification
product_area: authentication
version: "3.2"
status: current
published_at: 2026-05-15
---

# Debugging webhook signature verification

## Overview

Signatures cover the exact raw request body and endpoint-specific secret; parsing or re-encoding JSON before verification changes the bytes. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

One endpoint fails while another succeeds, and the failing service verifies a parsed body or uses the wrong endpoint secret. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Whitespace, character encoding, body decompression, or secret selection differs before the HMAC comparison. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Capture raw bytes before parsing, select the secret for that endpoint, compute HMAC-SHA256, and compare in constant time. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The locally computed signature matches the header for the unchanged raw payload. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
