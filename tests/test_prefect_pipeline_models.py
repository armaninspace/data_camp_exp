from __future__ import annotations

from pathlib import Path

from course_pipeline.prefect_pipeline.context import create_run_context
import json

from course_pipeline.llm_metering import LLMMeteringRecord, LLMMeteringRecorder
from course_pipeline.prefect_pipeline.manifests import build_run_result
from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary


def test_run_config_defaults(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    assert config.strict_mode is True
    assert config.run_mode == "dev"
    assert config.promote_ref is True
    assert config.standardized_output_subdir == "standardized"
    assert config.offset == 0
    assert config.skip_existing_ref_courses is False
    assert config.enable_answer_generation is True
    assert config.plan_llm_metering is True
    assert config.planned_llm_metering_stages == [
        "semantic_extract",
        "candidate_repair",
        "candidate_expand",
        "answer_generate",
        "answer_validate",
        "candidate_review_answers",
        "policy_review_answers",
    ]


def test_create_run_context_creates_stage_directories(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    context = create_run_context(config)
    assert context.run_root.exists()
    assert context.ref_root == tmp_path / "ref"
    assert context.standardized_dir.exists()
    assert context.answer_dir.exists()
    assert context.bundle_dir.exists()


def test_build_run_result_writes_manifest(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    context = create_run_context(config)
    stage = StageSummary(stage_name="prepare", started_at=context.started_at, status="completed")
    result = build_run_result(context, [stage], [], status="completed")
    assert result.status == "completed"
    assert result.promoted_ref is False
    assert context.manifest_path.exists()
    manifest = json.loads(context.manifest_path.read_text(encoding="utf-8"))
    assert manifest["llm_metering"]["enabled"] is True
    assert manifest["llm_metering"]["status"] == "planned_not_run"
    assert manifest["llm_metering"]["artifact_present"] is False


def test_build_run_result_marks_llm_metering_not_planned_when_disabled(tmp_path: Path) -> None:
    config = RunConfig(
        input_root=tmp_path / "in",
        output_root=tmp_path / "out",
        plan_llm_metering=False,
    )
    context = create_run_context(config)
    stage = StageSummary(stage_name="prepare", started_at=context.started_at, status="completed")
    build_run_result(context, [stage], [], status="completed")
    manifest = json.loads(context.manifest_path.read_text(encoding="utf-8"))
    assert manifest["llm_metering"]["enabled"] is False
    assert manifest["llm_metering"]["status"] == "not_planned"
    assert manifest["llm_metering"]["stages"] == []


def test_build_run_result_summarizes_llm_metering_when_present(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    context = create_run_context(config)
    recorder = LLMMeteringRecorder(context.run_root)
    recorder.record(
        LLMMeteringRecord(
            run_id=context.run_id,
            stage="policy_review_answers",
            provider="openai",
            model="gpt-4.1",
            prompt_version="policy_review_answers_v1",
            timestamp="2026-04-18T00:00:00+00:00",
            latency_ms=100,
            input_tokens=1000,
            output_tokens=500,
            estimated_cost_usd=0.01,
        )
    )
    recorder.record(
        LLMMeteringRecord(
            run_id=context.run_id,
            stage="policy_review_answers",
            provider="openai",
            model="gpt-4.1",
            prompt_version="policy_review_answers_v1",
            timestamp="2026-04-18T00:00:01+00:00",
            latency_ms=120,
            input_tokens=500,
            output_tokens=200,
            estimated_cost_usd=0.005,
        )
    )
    stage = StageSummary(stage_name="prepare", started_at=context.started_at, status="completed")
    build_run_result(context, [stage], [], status="completed")
    manifest = json.loads(context.manifest_path.read_text(encoding="utf-8"))
    assert manifest["llm_metering"]["enabled"] is True
    assert manifest["llm_metering"]["status"] == "completed"
    assert manifest["llm_metering"]["artifact_present"] is True
    assert manifest["llm_metering"]["record_count"] == 2
    assert manifest["llm_metering"]["estimated_cost_usd"] == 0.015
    assert manifest["llm_metering"]["stages"] == [
        {"stage": "semantic_extract", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "candidate_repair", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "candidate_expand", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "answer_generate", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "answer_validate", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "candidate_review_answers", "record_count": 0, "estimated_cost_usd": 0.0},
        {"stage": "policy_review_answers", "record_count": 2, "estimated_cost_usd": 0.015},
    ]
