from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader


@dataclass(frozen=True)
class SourceDocument:
    id: str
    title: str
    product_area: str
    version: str
    status: str
    source_type: str
    source_path: str
    published_at: datetime
    superseded_by: str | None
    checksum: str
    text: str


@dataclass(frozen=True)
class SourceChunk:
    id: str
    document_id: str
    chunk_index: int
    heading: str
    content: str
    token_count: int


def load_sources(knowledge_dir: Path, pdf_dir: Path) -> list[SourceDocument]:
    sources = [_load_markdown(path) for path in sorted((knowledge_dir / "docs").glob("*.md"))]
    manifest = yaml.safe_load((knowledge_dir / "pdf_manifest.yaml").read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        sources.append(_load_pdf(pdf_dir / item["filename"], item))
    return sources


def chunk_document(
    document: SourceDocument, minimum_words: int = 300, maximum_words: int = 520
) -> list[SourceChunk]:
    sections = _sections(document.text)
    chunks: list[tuple[str, str]] = []
    headings: list[str] = []
    paragraphs: list[str] = []
    word_count = 0
    for heading, body in sections:
        for part_number, body_part in enumerate(_split_large_section(body, maximum_words), start=1):
            part_heading = heading if part_number == 1 else f"{heading} (continued)"
            section_words = len(body_part.split())
            if (
                paragraphs
                and word_count >= minimum_words
                and word_count + section_words > maximum_words
            ):
                chunks.append((" / ".join(headings), "\n\n".join(paragraphs)))
                headings, paragraphs, word_count = [], [], 0
            headings.append(part_heading)
            paragraphs.append(f"## {part_heading}\n\n{body_part}")
            word_count += section_words
    if paragraphs:
        chunks.append((" / ".join(headings), "\n\n".join(paragraphs)))
    return [
        SourceChunk(
            id=f"{document.id}#{index:03d}",
            document_id=document.id,
            chunk_index=index,
            heading=heading[:240],
            content=content,
            token_count=_estimated_tokens(content),
        )
        for index, (heading, content) in enumerate(chunks)
    ]


def load_benchmarks(path: Path) -> tuple[str, list[dict[str, Any]]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return str(payload["version"]), list(payload["cases"])


def _load_markdown(path: Path) -> SourceDocument:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path}")
    _, frontmatter, body = raw.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    return SourceDocument(
        id=str(metadata["slug"]),
        title=str(metadata["title"]),
        product_area=str(metadata["product_area"]),
        version=str(metadata["version"]),
        status=str(metadata["status"]),
        source_type="markdown",
        source_path=path.as_posix(),
        published_at=_as_datetime(metadata["published_at"]),
        superseded_by=metadata.get("superseded_by"),
        checksum=hashlib.sha256(raw.encode()).hexdigest(),
        text=body.strip(),
    )


def _load_pdf(path: Path, metadata: dict[str, Any]) -> SourceDocument:
    reader = PdfReader(path)
    text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    return SourceDocument(
        id=str(metadata["slug"]),
        title=str(metadata["title"]),
        product_area=str(metadata["area"]),
        version=str(metadata["version"]),
        status=str(metadata["status"]),
        source_type="pdf",
        source_path=path.as_posix(),
        published_at=datetime(2026, 6, 15, tzinfo=UTC),
        superseded_by=None,
        checksum=hashlib.sha256(path.read_bytes()).hexdigest(),
        text=text,
    )


def _sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = "Document"
    body: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^#{1,3}\s+(.+)$", line)
        if match:
            if body and " ".join(body).strip():
                sections.append((heading, "\n".join(body).strip()))
            heading = match.group(1).strip()
            body = []
        else:
            body.append(line)
    if body and " ".join(body).strip():
        sections.append((heading, "\n".join(body).strip()))
    return sections or [("Document", text.strip())]


def _estimated_tokens(text: str) -> int:
    return max(1, round(len(re.findall(r"\w+|[^\w\s]", text)) * 1.2))


def _split_large_section(body: str, maximum_words: int) -> list[str]:
    words = body.split()
    if len(words) <= maximum_words:
        return [body]
    return [
        " ".join(words[index : index + maximum_words])
        for index in range(0, len(words), maximum_words)
    ]


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    return datetime.fromisoformat(str(value)).replace(tzinfo=UTC)
