from __future__ import annotations

import json
import os
from pathlib import Path

from course_pipeline.normalize import iter_courses
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


def _ordered_course_ids() -> list[str]:
    courses, _ = iter_courses(INPUT_ROOT)
    return [course.course_id for course in courses]


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
    assert result.promoted_ref is False
    assert (run_root / "all_questions.jsonl").exists()
    assert (run_root / "inspection_bundle" / "24491_forecasting-in-r.md").exists()
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_mode"] == "dev"
    assert manifest["promoted_ref"] is False
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


def test_prefect_flow_prod_run_promotes_into_ref_current(tmp_path: Path) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path / "runs",
        ref_root=tmp_path / "ref",
        course_ids=["24491"],
        max_courses=1,
        strict_mode=True,
        run_mode="prod",
    )
    result = question_generation_pipeline_flow(config)
    assert result.status == "completed"
    assert result.promoted_ref is True
    ref_root = tmp_path / "ref" / "current"
    assert (ref_root / "aggregate" / "all_questions.jsonl").exists()
    assert (ref_root / "aggregate" / "inspection_bundle" / "24491_forecasting-in-r.md").exists()
    assert (ref_root / "by_course" / "24491" / "course.json").exists()
    assert (ref_root / "ref_state.json").exists()
    promotion_manifest = tmp_path / "ref" / "promotions" / f"{result.run_id}.json"
    assert promotion_manifest.exists()


def test_prefect_flow_prod_promotions_accumulate_by_course_id(tmp_path: Path) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    base_kwargs = {
        "input_root": INPUT_ROOT,
        "output_root": tmp_path / "runs",
        "ref_root": tmp_path / "ref",
        "strict_mode": False,
        "run_mode": "prod",
    }
    first = question_generation_pipeline_flow(RunConfig(course_ids=["24491"], max_courses=1, **base_kwargs))
    second = question_generation_pipeline_flow(RunConfig(course_ids=["24593"], max_courses=1, **base_kwargs))
    assert first.status == "completed"
    assert second.status == "completed"
    ref_root = tmp_path / "ref" / "current"
    course_rows = _read_jsonl(ref_root / "aggregate" / "courses.jsonl")
    assert {row["course_id"] for row in course_rows} == {"24491", "24593"}
    assert (ref_root / "by_course" / "24491" / "course.json").exists()
    assert (ref_root / "by_course" / "24593" / "course.json").exists()

    ref_state = json.loads((ref_root / "ref_state.json").read_text(encoding="utf-8"))
    assert ref_state["course_count"] == 2
    assert ref_state["last_promoted_run_id"] == second.run_id


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


def test_prefect_flow_offset_records_selected_course_ids_in_manifest(tmp_path: Path) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    ordered_course_ids = _ordered_course_ids()
    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        strict_mode=False,
        offset=1,
        max_courses=2,
    )
    result = question_generation_pipeline_flow(config)
    run_root = tmp_path / result.run_id
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    assert result.status == "completed"
    assert manifest["selected_course_ids"] == ordered_course_ids[1:3]
    assert manifest["skipped_existing_course_ids"] == []
    assert manifest["selection_counts"]["available_courses"] == len(ordered_course_ids)
    assert manifest["selection_counts"]["offset"] == 1
    assert manifest["selection_counts"]["selected_courses"] == 2


def test_prefect_flow_skip_existing_ref_courses_filters_before_slice(tmp_path: Path) -> None:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    ordered_course_ids = _ordered_course_ids()
    ref_root = tmp_path / "ref"
    existing_course_id = ordered_course_ids[0]
    (ref_root / "current" / "by_course" / existing_course_id).mkdir(parents=True)

    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path / "runs",
        ref_root=ref_root,
        strict_mode=False,
        skip_existing_ref_courses=True,
        max_courses=2,
    )
    result = question_generation_pipeline_flow(config)
    run_root = tmp_path / "runs" / result.run_id
    manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    assert result.status == "completed"
    assert manifest["skipped_existing_course_ids"] == [existing_course_id]
    assert manifest["selected_course_ids"] == ordered_course_ids[1:3]
    assert manifest["selection_counts"]["skipped_existing_ref_courses"] == 1
    assert manifest["selection_counts"]["selected_courses"] == 2
