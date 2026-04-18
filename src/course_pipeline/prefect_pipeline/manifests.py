from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from course_pipeline.prefect_pipeline.models.run_context import RunContext
from course_pipeline.prefect_pipeline.models.run_result import RunResult
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary


def current_git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            encoding="utf-8",
        ).strip()
    except Exception:  # noqa: BLE001
        return None


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_llm_metering_summary(context: RunContext) -> dict:
    metering_path = context.run_root / "llm_metering.jsonl"
    if not context.plan_llm_metering:
        return {
            "enabled": False,
            "status": "not_planned",
            "expected_artifact": "llm_metering.jsonl",
            "artifact_present": metering_path.exists(),
            "record_count": 0,
            "estimated_cost_usd": 0.0,
            "stages": [],
        }

    if not metering_path.exists():
        return {
            "enabled": True,
            "status": "planned_not_run",
            "expected_artifact": "llm_metering.jsonl",
            "artifact_present": False,
            "record_count": 0,
            "estimated_cost_usd": 0.0,
            "stages": [
                {"stage": stage, "record_count": 0, "estimated_cost_usd": 0.0}
                for stage in context.planned_llm_metering_stages
            ],
        }

    rows = _read_jsonl(metering_path)
    by_stage: dict[str, dict[str, int | float | str]] = defaultdict(
        lambda: {"record_count": 0, "estimated_cost_usd": 0.0}
    )
    for row in rows:
        stage = str(row.get("stage") or "unknown")
        by_stage[stage]["record_count"] += 1
        by_stage[stage]["estimated_cost_usd"] += float(row.get("estimated_cost_usd") or 0.0)

    stages = []
    seen = set()
    for stage in context.planned_llm_metering_stages:
        stage_data = by_stage.get(stage, {"record_count": 0, "estimated_cost_usd": 0.0})
        stages.append(
            {
                "stage": stage,
                "record_count": int(stage_data["record_count"]),
                "estimated_cost_usd": round(float(stage_data["estimated_cost_usd"]), 8),
            }
        )
        seen.add(stage)
    for stage in sorted(set(by_stage) - seen):
        stage_data = by_stage[stage]
        stages.append(
            {
                "stage": stage,
                "record_count": int(stage_data["record_count"]),
                "estimated_cost_usd": round(float(stage_data["estimated_cost_usd"]), 8),
            }
        )

    return {
        "enabled": True,
        "status": "completed",
        "expected_artifact": "llm_metering.jsonl",
        "artifact_present": True,
        "record_count": len(rows),
        "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
        "stages": stages,
    }


def write_manifest(
    context: RunContext,
    stage_summaries: list[StageSummary],
    artifact_index: list[dict[str, str | int | None]],
    status: str,
    blocking_failure: str | None = None,
    promoted_ref: bool = False,
    selection_metadata: dict | None = None,
) -> None:
    warning_count = sum(len(stage.warnings) for stage in stage_summaries)
    llm_metering = build_llm_metering_summary(context)
    payload = {
        "run_id": context.run_id,
        "status": status,
        "started_at": context.started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "run_mode": context.run_mode,
        "strict_mode": context.strict_mode,
        "input_root": str(context.input_root),
        "output_root": str(context.output_root),
        "ref_root": str(context.ref_root),
        "promote_ref": context.promote_ref,
        "promoted_ref": promoted_ref,
        "stage_summaries": [stage.model_dump(mode="json") for stage in stage_summaries],
        "artifact_index": artifact_index,
        "warning_count": warning_count,
        "blocking_failure": blocking_failure,
        "git_commit": current_git_commit(),
        "model_profile": context.model_profile,
        "llm_metering": llm_metering,
        "selected_course_ids": (selection_metadata or {}).get("selected_course_ids", []),
        "skipped_existing_course_ids": (selection_metadata or {}).get("skipped_existing_course_ids", []),
        "selection_counts": (selection_metadata or {}).get("selection_counts", {}),
    }
    context.manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_run_result(
    context: RunContext,
    stage_summaries: list[StageSummary],
    artifact_index: list[dict[str, str | int | None]],
    status: str,
    blocking_failure: str | None = None,
    promoted_ref: bool = False,
    selection_metadata: dict | None = None,
) -> RunResult:
    write_manifest(
        context,
        stage_summaries,
        artifact_index,
        status=status,
        blocking_failure=blocking_failure,
        promoted_ref=promoted_ref,
        selection_metadata=selection_metadata,
    )
    warning_count = sum(len(stage.warnings) for stage in stage_summaries)
    artifact_paths = [item["relative_path"] for item in artifact_index]
    return RunResult(
        run_id=context.run_id,
        status=status,
        manifest_path=context.manifest_path,
        stage_summaries=stage_summaries,
        artifact_paths=[str(path) for path in artifact_paths],
        warning_count=warning_count,
        promoted_ref=promoted_ref,
        blocking_failure=blocking_failure,
    )
