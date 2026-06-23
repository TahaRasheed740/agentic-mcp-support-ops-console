from pathlib import Path

from pypdf import PdfReader

from tracedesk_api.knowledge_sources import chunk_document, load_benchmarks, load_sources

ROOT = Path(__file__).resolve().parents[3]


def test_corpus_has_expected_sources_and_chunk_sizes() -> None:
    sources = load_sources(ROOT / "knowledge", ROOT / "output" / "pdf")
    chunks = [chunk for source in sources for chunk in chunk_document(source)]

    assert len(sources) == 40
    assert len(chunks) == 40
    assert {source.status for source in sources} == {"current", "superseded"}
    assert all(300 <= chunk.token_count <= 600 for chunk in chunks)


def test_benchmarks_reference_existing_tickets_and_sources() -> None:
    sources = load_sources(ROOT / "knowledge", ROOT / "output" / "pdf")
    version, cases = load_benchmarks(ROOT / "knowledge" / "benchmarks" / "v1.yaml")
    source_ids = {source.id for source in sources}

    assert version == "1.0"
    assert len(cases) == 15
    assert [case["ticket_id"] for case in cases] == [
        f"TKT-{number}" for number in range(1001, 1016)
    ]
    assert all(set(case["required_sources"]).issubset(source_ids) for case in cases)
    assert all(case["acceptable_root_causes"] for case in cases)
    assert all(case["expected_actions"] for case in cases)


def test_generated_pdfs_have_two_readable_pages_each() -> None:
    expectations = {
        "acme-incident-review-eu-latency.pdf": "worker queue imbalance",
        "acme-support-troubleshooting-handbook.pdf": "Intermittent 502 workflow",
    }
    for filename, phrase in expectations.items():
        reader = PdfReader(ROOT / "output" / "pdf" / filename)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert len(reader.pages) == 2
        assert phrase in extracted
