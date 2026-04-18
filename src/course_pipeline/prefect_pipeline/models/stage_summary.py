from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StageSummary(BaseModel):
    stage_name: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    input_count: int | None = None
    output_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    artifact_paths: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
