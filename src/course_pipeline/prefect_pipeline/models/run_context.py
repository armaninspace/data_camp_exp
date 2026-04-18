from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class RunContext(BaseModel):
    run_id: str
    started_at: datetime
    input_root: Path
    output_root: Path
    run_root: Path
    standardized_dir: Path
    semantics_dir: Path
    candidates_dir: Path
    policy_dir: Path
    ledger_dir: Path
    bundle_dir: Path
    logs_dir: Path
    manifest_path: Path
    strict_mode: bool
    persist_to_db: bool
    model_profile: str
    tags: list[str]
