from __future__ import annotations

import json
from pathlib import Path

import pytest

from course_pipeline.bundle_builder import BundleBuildError, build_inspection_bundle


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _make_run(tmp_path: Path) -> tuple[Path, str]:
    run_id = "20260418T212725Z"
    run_root = tmp_path / run_id
    (run_root / "review_bundle").mkdir(parents=True)
    (run_root / "policy" / "course_artifacts" / "7630").mkdir(parents=True)
    (run_root / "ledger" / "course_artifacts" / "7630").mkdir(parents=True)
    (run_root / "run_manifest.json").write_text(
        json.dumps({"run_id": run_id, "selected_course_ids": ["7630"]}) + "\n",
        encoding="utf-8",
    )
    (run_root / "question_ledger_v6_report.md").write_text("# report\n", encoding="utf-8")
    (run_root / "review_bundle" / "7630_intro.md").write_text("# course\n", encoding="utf-8")
    _write_jsonl(
        run_root / "courses.jsonl",
        [
            {
                "course_id": "7630",
                "source_url": "https://example.com",
                "provider": "DataCamp",
                "title": "Intro",
                "raw_yaml_path": "/tmp/course.yaml",
                "chapters": [],
            }
        ],
    )
    ledger_row = {
        "question_id": "q1",
        "question_text": "What is ARIMA?",
        "answer_text": "",
        "anchor_id": "arima-models",
        "anchor_label": "ARIMA models",
        "tracked_topics": ["arima"],
        "anchor_type": "foundational_vocabulary",
        "question_family": "entry",
        "question_type": "definition",
        "mastery_band": "novice",
        "canonical": True,
        "alias": False,
        "canonical_target": None,
        "required_entry": True,
        "validated_correct": True,
        "grounded": True,
        "serviceable": True,
        "delivery_class": "curated_visible",
        "visible": True,
        "non_visible_reasons": [],
        "reject_reasons": [],
        "tags": ["entry"],
        "scores": {
            "groundedness": 0.9,
            "correctness": 0.9,
            "query_likelihood": 0.9,
            "pedagogical_value": 0.9,
            "serviceability": 0.9,
            "distinctiveness": 0.9,
        },
        "source_refs": ["course 7630"],
        "course_id": "7630",
    }
    _write_jsonl(run_root / "all_questions.jsonl", [ledger_row])
    _write_jsonl(run_root / "visible_curated.jsonl", [ledger_row])
    _write_jsonl(run_root / "cache_servable.jsonl", [])
    _write_jsonl(run_root / "aliases.jsonl", [])
    (run_root / "anchors_summary.json").write_text(
        json.dumps(
            [
                {
                    "anchor_id": "arima-models",
                    "anchor_label": "ARIMA models",
                    "anchor_type": "foundational_vocabulary",
                    "coverage_status": "PASS",
                    "generated_count": 1,
                    "validated_correct_count": 1,
                    "visible_count": 1,
                    "cache_servable_count": 0,
                    "analysis_only_count": 0,
                    "hard_reject_count": 0,
                    "required_entry_exists": True,
                    "required_entry_visible": True,
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_root / "ledger" / "course_artifacts" / "7630" / "anchors_summary.json").write_text(
        json.dumps(
            [
                {
                    "anchor_id": "arima-models",
                    "anchor_label": "ARIMA models",
                    "anchor_type": "foundational_vocabulary",
                    "coverage_status": "PASS",
                    "generated_count": 1,
                    "validated_correct_count": 1,
                    "visible_count": 1,
                    "cache_servable_count": 0,
                    "analysis_only_count": 0,
                    "hard_reject_count": 0,
                    "required_entry_exists": True,
                    "required_entry_visible": True,
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_jsonl(run_root / "policy" / "course_artifacts" / "7630" / "hidden_correct.jsonl", [])
    return tmp_path, run_id


def test_build_inspection_bundle_creates_scoped_bundle(tmp_path: Path) -> None:
    output_root, run_id = _make_run(tmp_path)
    bundle_dir = build_inspection_bundle(
        run_id=run_id,
        output_dir=tmp_path / "bundle",
        output_root=output_root,
        course_ids=["7630"],
        strict=True,
    )
    assert (bundle_dir / "validation_report.json").exists()
    assert (bundle_dir / "inspection_report.md").exists()
    assert (bundle_dir / "courses" / "7630_intro.md").exists()
    assert (bundle_dir / "final_deliverables" / "all_questions.jsonl").exists()
    page = (bundle_dir / "courses" / "7630_intro.md").read_text(encoding="utf-8")
    assert "## Visible Curated Q/A Pairs" in page
    assert "## Hidden But Correct" in page
    assert "## Policy Summary" in page
    assert "## Scraped Course Description" in page


def test_build_inspection_bundle_fails_on_missing_required_file(tmp_path: Path) -> None:
    output_root, run_id = _make_run(tmp_path)
    (output_root / run_id / "all_questions.jsonl").unlink()
    with pytest.raises(BundleBuildError):
        build_inspection_bundle(
            run_id=run_id,
            output_dir=tmp_path / "bundle",
            output_root=output_root,
            course_ids=["7630"],
            strict=True,
        )


def test_build_inspection_bundle_fails_on_count_mismatch(tmp_path: Path) -> None:
    output_root, run_id = _make_run(tmp_path)
    _write_jsonl(output_root / run_id / "visible_curated.jsonl", [])
    with pytest.raises(BundleBuildError):
        build_inspection_bundle(
            run_id=run_id,
            output_dir=tmp_path / "bundle",
            output_root=output_root,
            course_ids=["7630"],
            strict=True,
        )


def test_build_inspection_bundle_supports_dry_run(tmp_path: Path) -> None:
    output_root, run_id = _make_run(tmp_path)
    bundle_dir = build_inspection_bundle(
        run_id=run_id,
        output_dir=tmp_path / "bundle",
        output_root=output_root,
        course_ids=["7630"],
        strict=True,
        dry_run=True,
    )
    assert bundle_dir == (tmp_path / "bundle").resolve()
    assert not bundle_dir.exists()
