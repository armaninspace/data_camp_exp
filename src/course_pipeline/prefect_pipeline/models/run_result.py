from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary


class RunResult(BaseModel):
    run_id: str
    status: Literal["completed", "failed"]
    manifest_path: Path
    stage_summaries: list[StageSummary]
    artifact_paths: list[str]
    warning_count: int
    promoted_ref: bool = False
    blocking_failure: str | None = None
