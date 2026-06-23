---
slug: mapping-schema-changes
title: Diagnosing mappings after an upstream schema change
product_area: data_mapping
version: "2.4"
status: current
published_at: 2026-05-15
---

# Diagnosing mappings after an upstream schema change

## Overview

Existing mappings return empty values when a field moves into a nested object unless the mapping path is updated. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Historical payloads succeed while newer payloads show null mapped fields and a different schema fingerprint. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

Mapping paths are explicit and are not silently rewritten when the source schema changes. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Compare one successful and one affected payload in test mode, update the field path, preview the mapped output, and publish a new mapping version. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

The preview contains the expected value and a new production event completes without a mapping warning. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
