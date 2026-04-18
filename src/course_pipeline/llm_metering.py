from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from course_pipeline.config import Settings
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


class MeteredLLMJsonClient:
    def __init__(self, settings: Settings, *, run_id: str, run_dir: Path, stage: str, prompt_version: str) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for review-answer generation")
        self.settings = settings
        self.run_id = run_id
        self.stage = stage
        self.prompt_version = prompt_version
        self.recorder = LLMMeteringRecorder(run_dir)

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        course_id: str | None = None,
        claim_id: str | None = None,
        question_group_id: str | None = None,
        entity_ids: list[str] | None = None,
        retry_count: int = 0,
        cache_status: Literal["hit", "miss", "bypass", "unknown"] = "miss",
    ) -> str:
        body = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started_at = current_timestamp_utc()
        started_perf = time.perf_counter()
        payload: dict | None = None
        error_text: str | None = None
        try:
            with urllib.request.urlopen(request, timeout=self.settings.openai_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            error_text = f"OpenAI request failed: {exc.code} {error_body}"
            raise RuntimeError(error_text) from exc
        finally:
            usage = (payload or {}).get("usage") or {}
            input_tokens = int(usage.get("prompt_tokens") or 0)
            output_tokens = int(usage.get("completion_tokens") or 0)
            self.recorder.record(
                LLMMeteringRecord(
                    run_id=self.run_id,
                    stage=self.stage,
                    provider="openai",
                    model=self.settings.openai_model,
                    prompt_version=self.prompt_version,
                    timestamp=started_at,
                    latency_ms=int(round((time.perf_counter() - started_perf) * 1000)),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    retry_count=retry_count,
                    cache_status=cache_status,
                    estimated_cost_usd=estimate_cost_usd(
                        input_tokens,
                        output_tokens,
                        input_cost_per_million_tokens=self.settings.openai_input_cost_per_million_tokens,
                        output_cost_per_million_tokens=self.settings.openai_output_cost_per_million_tokens,
                    ),
                    course_id=course_id,
                    claim_id=claim_id,
                    question_group_id=question_group_id,
                    entity_ids=entity_ids or [],
                    success=error_text is None,
                    error_text=error_text,
                )
            )
        assert payload is not None
        return payload["choices"][0]["message"]["content"]
