---
slug: incident-correlation
title: Correlating support cases with incidents
product_area: reliability
version: "2.1"
status: current
published_at: 2026-05-15
---

# Correlating support cases with incidents

## Overview

Correlation requires overlapping time, region, affected component, and matching failure mode. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

A nearby incident is not evidence when the customer region or error differs. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Broad incident timelines create tempting but false associations. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Validate all four correlation dimensions before citing an incident. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Incident scope directly explains the observed runs. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
