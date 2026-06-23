---
slug: schedule-troubleshooting
title: Schedule troubleshooting checklist
product_area: scheduling
version: "1.8"
status: current
published_at: 2026-05-15
---

# Schedule troubleshooting checklist

## Overview

Missing schedules should be checked for pause state, next-run preview, time zone, and recent deployment changes. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

A schedule can be healthy even when no UTC run appears on the expected UTC date. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Most reports result from local-time interpretation or an intentional pause. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Work through state, calendar, time zone, and history in that order. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The expected next run is visible and a test schedule fires. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
