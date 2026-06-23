---
slug: environment-routing
title: Keeping sandbox and production routes isolated
product_area: configuration
version: "2.1"
status: current
published_at: 2026-05-15
---

# Keeping sandbox and production routes isolated

## Overview

Environment belongs to the integration, while destinations are independent objects that can accidentally be attached to both environments. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Sandbox events reach a production URL even though the integration badge is sandbox. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

The production destination was selected on the sandbox route or copied during integration duplication. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Inspect the route destination ID rather than its display name, detach the production destination, and attach a sandbox-only endpoint. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

A labeled sandbox test event appears only at the sandbox destination. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
