from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime

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
