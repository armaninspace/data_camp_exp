from __future__ import annotations

import json
import os
from pathlib import Path

from course_pipeline.prefect_pipeline.artifacts import build_artifact_index_entries
from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow
from course_pipeline.prefect_pipeline.models.run_config import RunConfig


REPO_ROOT = Path("/code")
INPUT_ROOT = REPO_ROOT / "data" / "classcentral-datacamp-yaml"


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_artifact_index_entries_are_relative(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    file_path = run_root / "a.jsonl"
    file_path.write_text("", encoding="utf-8")
    entries = build_artifact_index_entries("stage", [file_path], run_root)
    assert entries == [
        {
            "artifact_type": "jsonl",
            "relative_path": "a.jsonl",
            "stage": "stage",
            "row_count": None,
            "content_type": "file",
        }
    ]


def test_prefect_flow_smoke_success(tmp_path: Path) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        course_ids=["24491"],
        max_courses=1,
        strict_mode=True,
    )
    result = question_generation_pipeline_flow(config)
    run_root = tmp_path / result.run_id
    assert result.status == "completed"
    assert (run_root / "all_questions.jsonl").exists()
    assert (run_root / "inspection_bundle" / "24491_forecasting-in-r.md").exists()
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    stage_names = [stage["stage_name"] for stage in manifest["stage_summaries"]]
    assert "standardize_courses" in stage_names
    assert "build_ledger" in stage_names
    all_questions = _read_jsonl(run_root / "all_questions.jsonl")
    policy_rows = _read_jsonl(run_root / "policy" / "validated_correct_all.jsonl")
    hard_reject_rows = _read_jsonl(run_root / "policy" / "hard_reject_records.jsonl")
    assert len(all_questions) == len(policy_rows) + len(hard_reject_rows)
    hidden_required_entry = [
        row
        for row in all_questions
        if row.get("required_entry")
        and not row.get("visible")
        and row.get("non_visible_reasons") == ["analysis_only_low_distinctiveness"]
    ]
    assert hidden_required_entry == []


def test_prefect_flow_strict_mode_failure_records_manifest(tmp_path: Path, monkeypatch) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    from course_pipeline.prefect_pipeline import flows

    original_run_policy = flows.run_policy

    def fake_run_policy(context, standardized_result, candidate_result):
        payload = original_run_policy(context, standardized_result, candidate_result)
        payload["warning_messages"] = ["forced strict coverage failure"]
        return payload

    monkeypatch.setattr(flows, "run_policy", fake_run_policy)
    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        course_ids=["24491"],
        max_courses=1,
        strict_mode=True,
    )
    result = question_generation_pipeline_flow(config)
    run_root = tmp_path / result.run_id
    assert result.status == "failed"
    assert result.blocking_failure == "forced strict coverage failure"
    assert (run_root / "policy" / "validated_correct_all.jsonl").exists()
    assert (run_root / "run_manifest.json").exists()
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
    assert manifest["blocking_failure"] == "forced strict coverage failure"
