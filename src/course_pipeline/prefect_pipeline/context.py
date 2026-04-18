from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.prefect_pipeline.models.run_context import RunContext
from course_pipeline.utils import ensure_dir


def build_run_id(run_label: str | None = None) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{run_label}" if run_label else timestamp


def create_run_context(config: RunConfig) -> RunContext:
    run_id = build_run_id(config.run_label)
    run_root = config.output_root / run_id
    if run_root.exists() and not config.overwrite_existing:
        raise FileExistsError(f"run directory already exists: {run_root}")
    ensure_dir(run_root)
    context = RunContext(
        run_id=run_id,
        started_at=datetime.now(UTC),
        input_root=Path(config.input_root),
        output_root=Path(config.output_root),
        run_root=run_root,
        standardized_dir=ensure_dir(run_root / config.standardized_output_subdir),
        semantics_dir=ensure_dir(run_root / config.semantic_output_subdir),
        candidates_dir=ensure_dir(run_root / config.candidate_output_subdir),
        policy_dir=ensure_dir(run_root / config.policy_output_subdir),
        ledger_dir=ensure_dir(run_root / config.ledger_output_subdir),
        bundle_dir=ensure_dir(run_root / config.bundle_output_subdir),
        logs_dir=ensure_dir(run_root / "logs"),
        manifest_path=run_root / "run_manifest.json",
        strict_mode=config.strict_mode,
        persist_to_db=config.persist_to_db,
        model_profile=config.model_profile,
        tags=list(config.tags),
    )
    return context
