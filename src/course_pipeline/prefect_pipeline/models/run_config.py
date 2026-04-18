from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    run_label: str | None = None
    input_root: Path
    output_root: Path
    standardized_output_subdir: str = "standardized"
    semantic_output_subdir: str = "semantics"
    candidate_output_subdir: str = "candidates"
    policy_output_subdir: str = "policy"
    ledger_output_subdir: str = "ledger"
    bundle_output_subdir: str = "inspection_bundle"
    strict_mode: bool = True
    max_courses: int | None = None
    course_ids: list[str] | None = None
    overwrite_existing: bool = False
    persist_to_db: bool = False
    publish_prefect_artifacts: bool = True
    fail_fast: bool = False
    log_level: str = "INFO"
    model_profile: str = "default"
    tags: list[str] = Field(default_factory=list)
    concurrency_limit: int = 1
