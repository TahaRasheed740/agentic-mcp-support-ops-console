---
slug: legacy-sso-scale
title: Legacy Scale plan SSO preview
product_area: plan_access
version: "0.8"
status: superseded
published_at: 2026-05-15
superseded_by: sso-entitlements
---

# Legacy Scale plan SSO preview

> **Superseded guidance.** This page is retained for retrieval testing and historical context. Do not use it for a current customer recommendation.

## Overview

A limited preview temporarily exposed SSO to selected Scale organizations. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The page mentions preview enrollment and has no current entitlement table. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

The preview ended before general availability on Enterprise. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Use the current SSO availability page. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Current entitlement is Enterprise only. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
