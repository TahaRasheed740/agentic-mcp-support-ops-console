from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "knowledge" / "catalog.yaml"
DOCS_DIR = ROOT / "knowledge" / "docs"
PDF_DIR = ROOT / "output" / "pdf"


def main() -> None:
    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    documents: list[dict[str, Any]] = catalog["documents"]
    _replace_generated_directory(DOCS_DIR)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    for document in documents:
        path = DOCS_DIR / f"{document['slug']}.md"
        path.write_text(_render_markdown(document), encoding="utf-8", newline="\n")
    _build_incident_review(PDF_DIR / "acme-incident-review-eu-latency.pdf")
    _build_handbook(PDF_DIR / "acme-support-troubleshooting-handbook.pdf")
    digest = hashlib.sha256(
        "".join(
            path.read_text(encoding="utf-8") for path in sorted(DOCS_DIR.glob("*.md"))
        ).encode()
    ).hexdigest()
    print(
        f"Generated {len(documents)} Markdown documents and 2 PDFs. Corpus SHA256: {digest}"
    )


def _replace_generated_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _render_markdown(document: dict[str, Any]) -> str:
    superseded = ""
    if document.get("superseded_by"):
        superseded = f"superseded_by: {document['superseded_by']}\n"
    warning = ""
    if document["status"] == "superseded":
        warning = (
            "> **Superseded guidance.** This page is retained for retrieval testing and historical "
            "context. Do not use it for a current customer recommendation.\n\n"
        )
    return f"""---
slug: {document["slug"]}
title: {document["title"]}
product_area: {document["area"]}
version: \"{document["version"]}\"
status: {document["status"]}
published_at: 2026-05-15
{superseded}---

# {document["title"]}

{warning}## Overview

{document["summary"]} This article applies to Acme Automations organizations and should be read
alongside the organization plan, integration environment, and the exact run timeline. Support
engineers should distinguish observed evidence from assumptions before proposing a change.

## Signals to collect

{document["signals"]} Record the organization ID, integration ID, relevant UTC timestamps, and
the smallest set of run identifiers needed to reproduce the observation. Never include secrets,
raw access tokens, or unredacted customer payloads in a support note.

## Why it happens

{document["cause"]} Similar symptoms can have unrelated causes, so a matching title or error word
is not enough by itself. Prefer current documentation over a superseded page and confirm that the
guidance version applies to the customer's plan and environment.

## Resolution workflow

{document["procedure"]} Make one controlled change at a time and preserve the before-and-after run
IDs. Actions that retry work, change routing, or alter customer configuration require an explicit
support-engineer decision.

## Verification

{document["verification"]} If verification fails, revert the controlled change when possible,
capture the new evidence, and escalate with the relevant timeline rather than repeating the same
action without a new hypothesis.
"""


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "AcmeTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=29,
            textColor=colors.HexColor("#17211B"),
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "AcmeSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#657068"),
            spaceAfter=20,
        ),
        "heading": ParagraphStyle(
            "AcmeHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#176B4D"),
            spaceBefore=14,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "AcmeBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#26332B"),
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "AcmeSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#657068"),
        ),
        "right": ParagraphStyle(
            "AcmeRight",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#657068"),
        ),
    }


def _document(path: Path, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(path),
        pagesize=LETTER,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.7 * inch,
        title=title,
        author="Acme Automations",
    )


def _page(canvas: Any, document: Any) -> None:
    canvas.saveState()
    width, height = LETTER
    canvas.setStrokeColor(colors.HexColor("#D8D5CA"))
    canvas.line(
        0.72 * inch, height - 0.52 * inch, width - 0.72 * inch, height - 0.52 * inch
    )
    canvas.setFillColor(colors.HexColor("#657068"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        0.72 * inch, height - 0.39 * inch, "ACME AUTOMATIONS / SUPPORT OPERATIONS"
    )
    canvas.drawRightString(width - 0.72 * inch, 0.42 * inch, f"Page {document.page}")
    canvas.restoreState()


def _build_incident_review(path: Path) -> None:
    styles = _styles()
    story: list[Any] = [
        Paragraph("Incident review: EU delivery latency", styles["title"]),
        Paragraph("INC-001 / June 14, 2026 / Final review", styles["subtitle"]),
        _summary_table(
            [
                ("Severity", "SEV2"),
                ("Region", "eu-west"),
                ("Customer impact", "Delayed webhook dispatch"),
                ("Data loss", "None"),
            ],
            styles,
        ),
        Paragraph("Executive summary", styles["heading"]),
        Paragraph(
            "A worker queue imbalance in eu-west increased webhook queue time for 47 minutes. "
            "Payload execution time and customer endpoint response time remained normal. The "
            "incident affected multiple organizations assigned to eu-west while US regions stayed "
            "within baseline. No customer configuration change was required.",
            styles["body"],
        ),
        Paragraph("Customer-visible evidence", styles["heading"]),
        Paragraph(
            "Affected runs show rising time between queued_at and dispatched_at, followed by normal "
            "execution duration. Support should correlate cases using organization region, the "
            "incident window, and queue-time metrics. A nearby incident with a different region or "
            "failure mode is not sufficient evidence.",
            styles["body"],
        ),
        Paragraph("Timeline (UTC)", styles["heading"]),
        _timeline_table(
            [
                ("11:52", "Alert fired for eu-west queue age."),
                ("12:00", "Incident declared; worker imbalance confirmed."),
                ("12:11", "New work redistributed across healthy workers."),
                ("12:31", "Queue age returned below two minutes."),
                ("12:47", "Backlog cleared; incident moved to monitoring."),
            ],
            styles,
        ),
        Paragraph("Support guidance", styles["heading"]),
        Paragraph(
            "Preserve affected run IDs, explain that deliveries were delayed rather than lost, and "
            "avoid asking customers to rotate secrets or change endpoints. Escalate cases where "
            "execution duration, destination errors, or impact time falls outside this incident.",
            styles["body"],
        ),
        PageBreak(),
        Paragraph("Technical analysis", styles["title"]),
        Paragraph("Queue imbalance and recovery evidence", styles["subtitle"]),
        Paragraph("Root cause", styles["heading"]),
        Paragraph(
            "A deployment changed worker lease renewal timing. Under uneven partition ownership, "
            "several workers retained fewer partitions while two workers accumulated a backlog. "
            "Automatic scaling added capacity but did not immediately rebalance existing leases.",
            styles["body"],
        ),
        Paragraph("Why retries were not the remedy", styles["heading"]),
        Paragraph(
            "Runs had not reached the destination, so creating manual retries would have added work "
            "to the same regional queue. Once dispatch occurred, destinations acknowledged normally. "
            "The correct mitigation redistributed queued work and preserved original delivery IDs.",
            styles["body"],
        ),
        Paragraph("Corrective actions", styles["heading"]),
        _timeline_table(
            [
                (
                    "Complete",
                    "Lease timing reverted and guarded by configuration validation.",
                ),
                ("Complete", "Queue-age alert split by region and partition."),
                ("Planned", "Load test adds uneven partition ownership scenario."),
                (
                    "Planned",
                    "Support incident view exposes queue and execution duration separately.",
                ),
            ],
            styles,
        ),
        Spacer(1, 12),
        Paragraph(
            "Evidence citation: this review supports region-specific latency investigations only "
            "when case time, home region, affected component, and queue-delay failure mode match.",
            styles["small"],
        ),
    ]
    _document(path, "Incident review - EU delivery latency").build(
        story, onFirstPage=_page, onLaterPages=_page
    )


def _build_handbook(path: Path) -> None:
    styles = _styles()
    story: list[Any] = [
        Paragraph("Support troubleshooting field handbook", styles["title"]),
        Paragraph("Evidence-first triage for Acme Automations", styles["subtitle"]),
        Paragraph("The first five minutes", styles["heading"]),
        Paragraph(
            "Record customer impact, start time, organization, integration, environment, and two "
            "representative run IDs. Separate what the customer observed from the suspected cause. "
            "Do not retry, resume, rotate, or reroute anything until the current state is preserved.",
            styles["body"],
        ),
        _summary_table(
            [
                (
                    "Authentication 4xx",
                    "Usually permanent; inspect credentials before retry",
                ),
                ("HTTP 429", "Transient; honor Retry-After and scheduled backoff"),
                ("HTTP 502", "Usually transient; compare identical successful retries"),
                (
                    "Queue delay",
                    "Check region and incident timeline before customer config",
                ),
            ],
            styles,
        ),
        Paragraph("Intermittent 502 workflow", styles["heading"]),
        Paragraph(
            "Compare the same payload across failed and successful attempts. If an unchanged payload "
            "succeeds automatically, the evidence points to a transient gateway, destination, or "
            "network condition rather than a deterministic payload defect. Calculate the rolling "
            "error rate, correlate incident time and region, and escalate when retries exhaust or the "
            "rate remains above one percent.",
            styles["body"],
        ),
        Paragraph("Evidence quality", styles["heading"]),
        Paragraph(
            "Prefer current documentation and direct operational records. Mark superseded pages as "
            "historical rather than silently using them. A useful conclusion cites the exact source "
            "and states what remains uncertain.",
            styles["body"],
        ),
        PageBreak(),
        Paragraph("Action safety", styles["title"]),
        Paragraph("Read freely; write only with intent", styles["subtitle"]),
        Paragraph("Read-only investigation", styles["heading"]),
        Paragraph(
            "Documentation search, organization lookup, integration state, run history, logs, and "
            "incident timelines do not change customer state. Use them to build a timeline and test a "
            "specific hypothesis.",
            styles["body"],
        ),
        Paragraph("Approval-gated actions", styles["heading"]),
        Paragraph(
            "Retries, resumes, pauses, route changes, credential changes, ticket updates, and customer "
            "messages require an explicit support-engineer decision. The proposed action must include "
            "the evidence, expected effect, risk, and an idempotency key when supported.",
            styles["body"],
        ),
        Paragraph("Escalation packet", styles["heading"]),
        _timeline_table(
            [
                (
                    "Scope",
                    "Organizations, regions, environments, and affected components.",
                ),
                (
                    "Timeline",
                    "First observation, representative runs, and current state in UTC.",
                ),
                (
                    "Evidence",
                    "Current docs, logs, incidents, and disconfirming observations.",
                ),
                (
                    "Actions",
                    "What was attempted, who approved it, and the measured result.",
                ),
            ],
            styles,
        ),
        Paragraph("Definition of done", styles["heading"]),
        Paragraph(
            "The root cause is supported by retrieved evidence, the recommended action is bounded, "
            "verification succeeded, and the customer-facing explanation distinguishes confirmed "
            "facts from remaining uncertainty.",
            styles["body"],
        ),
    ]
    _document(path, "Support troubleshooting field handbook").build(
        story, onFirstPage=_page, onLaterPages=_page
    )


def _summary_table(
    rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle]
) -> Table:
    data = [
        [Paragraph(key, styles["small"]), Paragraph(value, styles["body"])]
        for key, value in rows
    ]
    table = Table(data, colWidths=[1.35 * inch, 4.95 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5EEE8")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D5CA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8D5CA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _timeline_table(
    rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle]
) -> Table:
    data = [
        [Paragraph(key, styles["right"]), Paragraph(value, styles["body"])]
        for key, value in rows
    ]
    table = Table(data, colWidths=[0.8 * inch, 5.5 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, colors.HexColor("#E3E0D8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


if __name__ == "__main__":
    main()
