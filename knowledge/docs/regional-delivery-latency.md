---
slug: regional-delivery-latency
title: Investigating region-specific delivery latency
product_area: reliability
version: "3.0"
status: current
published_at: 2026-05-15
---

# Investigating region-specific delivery latency

## Overview

Latency isolated to one region with healthy destinations should be correlated with the regional incident timeline before changing customer configuration. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Queue time rises while execution time stays normal, multiple organizations are affected, and another region remains healthy. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

A regional worker or queue degradation delays dispatch without changing payload processing. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Compare queue and execution duration, check incidents for the organization region, preserve failed-run evidence, and avoid unnecessary endpoint changes. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Queue latency returns to baseline as the incident recovers and untouched customer endpoints resume normal delivery. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
