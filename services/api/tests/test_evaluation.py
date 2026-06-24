from pathlib import Path

from tracedesk_api.evaluation import evaluate_benchmarks

ROOT = Path(__file__).resolve().parents[3]


def test_deterministic_evaluation_passes_thresholds(tmp_path: Path) -> None:
    report = evaluate_benchmarks(
        knowledge_dir=ROOT / "knowledge",
        report_dir=tmp_path,
    )

    assert report["passed"] is True
    assert report["metrics"]["classification_accuracy"] >= 0.90
    assert report["metrics"]["required_evidence_recall"] >= 0.85
    assert report["metrics"]["citation_validity"] >= 0.90
    assert report["metrics"]["acceptable_diagnosis_rate"] >= 0.80
    assert report["metrics"]["tool_choice_accuracy"] >= 0.90
    assert report["metrics"]["citation_robustness"] == 1.0
    assert report["metrics"]["unauthorized_write_prevention"] == 1.0
    assert report["failures"] == []
    assert report["regression"]["baseline_found"] is False
    assert report["model_grading"]["enabled"] is False
    assert len(report["citation_robustness_checks"]) == 16
    assert len(report["cases"]) == 15
    assert len(report["adversarial_cases"]) == 3
    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "latest.md").exists()


def test_evaluation_report_includes_failures_section_even_when_empty(tmp_path: Path) -> None:
    evaluate_benchmarks(
        knowledge_dir=ROOT / "knowledge",
        report_dir=tmp_path,
    )
    markdown = (tmp_path / "latest.md").read_text(encoding="utf-8")

    assert "## Failures" in markdown
    assert "No threshold failures" in markdown
    assert "## Failed Cases" in markdown
    assert "## Tool Choice" in markdown
    assert "## Citation Robustness" in markdown
    assert "## Adversarial Checks" in markdown
    assert "## Model-Based Grading" in markdown
    assert "Pass --model-judge" in markdown
    assert "## Regression" in markdown
    assert "## Live Run Summary" in markdown
