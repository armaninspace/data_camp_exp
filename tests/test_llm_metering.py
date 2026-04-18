from pathlib import Path

from course_pipeline.llm_metering import LLMMeteringRecord, LLMMeteringRecorder, estimate_cost_usd


def test_estimate_cost_usd_uses_per_million_rates() -> None:
    cost = estimate_cost_usd(
        1500,
        500,
        input_cost_per_million_tokens=2.0,
        output_cost_per_million_tokens=8.0,
    )
    assert cost == 0.007


def test_llm_metering_recorder_appends_jsonl(tmp_path: Path) -> None:
    recorder = LLMMeteringRecorder(tmp_path)
    recorder.record(
        LLMMeteringRecord(
            run_id="run-1",
            stage="policy_review_answers",
            provider="openai",
            model="gpt-4.1",
            prompt_version="policy_review_answers_v1",
            timestamp="2026-04-18T00:00:00+00:00",
            latency_ms=321,
            input_tokens=123,
            output_tokens=45,
            retry_count=0,
            cache_status="miss",
            estimated_cost_usd=0.00123,
            course_id="24491",
            entity_ids=["q1", "q2"],
        )
    )
    text = (tmp_path / "llm_metering.jsonl").read_text(encoding="utf-8")
    assert '"run_id": "run-1"' in text
    assert '"stage": "policy_review_answers"' in text
    assert '"entity_ids": ["q1", "q2"]' in text
