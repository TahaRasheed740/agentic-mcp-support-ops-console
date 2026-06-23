---
slug: transient-delivery-errors
title: Handling intermittent 502 delivery errors
product_area: reliability
version: "3.4"
status: current
published_at: 2026-05-15
---

# Handling intermittent 502 delivery errors

## Overview

A small number of HTTP 502 responses followed by successful retries indicate a transient destination or network error rather than a payload defect. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Identical payloads succeed on retry, failures span unrelated events, and destination execution is otherwise healthy. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

A gateway or upstream service temporarily fails before the destination application processes the request. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Correlate failures by time and region, inspect incident status, allow automatic retries, and escalate only if the error rate or retry exhaustion threshold is reached. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

Automatic retries succeed and the rolling 502 rate returns below one percent. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
