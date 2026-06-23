---
slug: csv-export-guide
title: Consuming CSV exports
product_area: exports
version: "1.7"
status: current
published_at: 2026-05-15
---

# Consuming CSV exports

## Overview

CSV timestamps are ISO-8601 UTC and identifiers must be treated as strings. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Spreadsheet software may reformat timestamps or long identifiers. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

CSV has no native schema metadata. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Import with explicit column types and convert time zones downstream. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Row IDs and instants match the API representation. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
