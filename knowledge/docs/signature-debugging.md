---
slug: signature-debugging
title: Signature debugging checklist
product_area: authentication
version: "1.8"
status: current
published_at: 2026-05-15
---

# Signature debugging checklist

## Overview

Debug signature failures by preserving raw bytes, timestamp header, endpoint ID, and key fingerprint. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

Framework body parsers are a common source of byte changes. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

HMAC equality requires identical bytes and secret. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Log hashes rather than secrets and compare each input independently. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

A local reproduction matches the request header. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
