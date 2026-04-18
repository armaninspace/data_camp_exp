from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class RunContext(BaseModel):
    run_id: str
    started_at: datetime
    input_root: Path
    output_root: Path
    ref_root: Path
    run_root: Path
    standardized_dir: Path
    semantics_dir: Path
    candidates_dir: Path
    policy_dir: Path
    ledger_dir: Path
    bundle_dir: Path
    logs_dir: Path
    manifest_path: Path
    run_mode: Literal["dev", "test", "prod"]
    promote_ref: bool
    strict_mode: bool
    persist_to_db: bool
    model_profile: str
    tags: list[str]
    plan_llm_metering: bool
    planned_llm_metering_stages: list[str]
