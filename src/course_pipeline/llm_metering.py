from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from course_pipeline.utils import append_jsonl


class LLMMeteringRecord(BaseModel):
    run_id: str
    stage: str
    provider: str
    model: str
    prompt_version: str
    timestamp: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    retry_count: int = 0
    cache_status: Literal["hit", "miss", "bypass", "unknown"] = "miss"
    estimated_cost_usd: float
    course_id: str | None = None
    claim_id: str | None = None
    question_group_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    success: bool = True
    error_text: str | None = None


def current_timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    *,
    input_cost_per_million_tokens: float,
    output_cost_per_million_tokens: float,
) -> float:
    input_cost = (input_tokens / 1_000_000) * input_cost_per_million_tokens
    output_cost = (output_tokens / 1_000_000) * output_cost_per_million_tokens
    return round(input_cost + output_cost, 8)


class LLMMeteringRecorder:
    def __init__(self, run_dir: Path) -> None:
        self.path = run_dir / "llm_metering.jsonl"

    def record(self, record: LLMMeteringRecord) -> None:
        append_jsonl(self.path, record.model_dump(mode="json"))
