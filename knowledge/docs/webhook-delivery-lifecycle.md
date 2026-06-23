---
slug: webhook-delivery-lifecycle
title: Webhook delivery lifecycle
product_area: delivery
version: "2.6"
status: current
published_at: 2026-05-15
---

# Webhook delivery lifecycle

## Overview

A delivery moves through queued, dispatched, acknowledged, retrying, and terminal states. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Queue duration and execution duration identify whether delay happened inside Acme or at the destination. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Lifecycle stages separate scheduling, worker dispatch, and destination response handling. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Compare timestamps before interpreting an overall duration. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The stage with abnormal duration matches logs and metrics. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
