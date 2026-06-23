---
slug: sso-entitlements
title: SSO availability and administrator permissions
product_area: plan_access
version: "2.0"
status: current
published_at: 2026-05-15
---

# SSO availability and administrator permissions

## Overview

SAML SSO is available only on Enterprise plans and can be configured by organization owners, not workspace administrators. This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

The SSO control is visible but disabled for a non-owner or for an organization on Starter, Growth, or Scale. Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

SSO is an organization-level Enterprise entitlement with owner-only security permissions. Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

Confirm the organization plan and requester role, then involve an owner or upgrade through the normal billing process. Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

An Enterprise organization owner can open configuration and validate IdP metadata. If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
