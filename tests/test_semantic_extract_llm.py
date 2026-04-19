from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.semantic_extract_llm import (
    build_semantic_extract_payload,
    extract_semantics_with_llm,
)
from course_pipeline.schemas import ChapterOut, NormalizedCourse


def _course() -> NormalizedCourse:
    return NormalizedCourse(
        course_id="7630",
        source_url="https://example.com/course",
        final_url="https://example.com/course",
        provider="DataCamp",
        title="Forecasting in R",
        summary="Learn ARIMA models and benchmark methods for forecasting.",
        overview=(
            "This course teaches ARIMA models, exponential smoothing, forecast accuracy, "
            "and benchmarking approaches for time series forecasting."
        ),
        subjects=["Forecasting"],
        raw_yaml_path="/tmp/course.yaml",
        chapters=[
            ChapterOut(
                chapter_index=1,
                title="ARIMA models",
                summary="Fit ARIMA models and compare them with benchmark methods.",
                source="syllabus",
                confidence=1.0,
            )
        ],
    )


def test_build_semantic_extract_payload_uses_normalized_course_fields() -> None:
    payload = build_semantic_extract_payload(
        extract_semantics_with_llm(raw_course=_course(), settings=None, run_dir=None)["normalized_document"]
    )
    assert payload["course"]["course_id"] == "7630"
    assert payload["course"]["sections"][0]["title"] == "ARIMA models"


def test_extract_semantics_with_llm_falls_back_to_heuristics_without_api_key() -> None:
    result = extract_semantics_with_llm(raw_course=_course(), settings=None, run_dir=None)

    assert result["extraction_mode"] == "llm_semantic_extract_bypassed_no_openai_key"
    assert result["topic_records"]
    assert result["anchor_candidates"]
    assert result["friction_records"]
    assert any(record.label == "ARIMA models" for record in result["topic_records"])
    assert any(record.requires_entry_question for record in result["anchor_candidates"])


def test_extract_semantics_with_llm_uses_metered_client_when_available(monkeypatch, tmp_path: Path) -> None:
    class FakeSettings:
        openai_api_key = "test-key"
        openai_model = "gpt-4.1"
        openai_timeout = 30
        openai_input_cost_per_million_tokens = 0.0
        openai_output_cost_per_million_tokens = 0.0

    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            assert run_id == "run123"
            assert stage == "semantic_extract"
            assert prompt_version == "semantic_extract_v1"
            self.run_dir = run_dir

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            assert "structured learner-facing course semantics" in system_prompt
            payload = json.loads(user_prompt)
            assert payload["course"]["course_id"] == "7630"
            return json.dumps(
                {
                    "topics": [
                        {
                            "topic_id": "arima",
                            "label": "ARIMA",
                            "aliases": ["autoregressive integrated moving average"],
                            "topic_type": "concept",
                            "description": "Forecasting model family.",
                            "source_fields": ["overview"],
                            "evidence_spans": [{"field": "overview", "excerpt": "ARIMA models"}],
                            "confidence": 0.93,
                        }
                    ],
                    "anchors": [
                        {
                            "anchor_id": "arima",
                            "label": "ARIMA",
                            "normalized_label": "arima",
                            "anchor_type": "foundational_vocabulary",
                            "foundational_candidate": True,
                            "learner_facing": True,
                            "requires_entry_question": True,
                            "rationale": "Core named concept.",
                            "source_fields": ["overview"],
                            "evidence_spans": [{"field": "overview", "excerpt": "ARIMA models"}],
                            "confidence": 0.95,
                        }
                    ],
                    "alias_groups": [],
                    "frictions": [],
                }
            )

    monkeypatch.setattr("course_pipeline.semantic_extract_llm.MeteredLLMJsonClient", FakeClient)

    run_dir = tmp_path / "run123"
    run_dir.mkdir()
    result = extract_semantics_with_llm(raw_course=_course(), settings=FakeSettings(), run_dir=run_dir)

    assert result["extraction_mode"] == "llm"
    assert [record.label for record in result["topic_records"]] == ["ARIMA"]
    assert result["anchor_candidates"][0].requires_entry_question is True


def test_extract_semantics_with_llm_parses_nested_course_semantics_response(monkeypatch, tmp_path: Path) -> None:
    class FakeSettings:
        openai_api_key = "test-key"
        openai_model = "gpt-4.1"
        openai_timeout = 30
        openai_input_cost_per_million_tokens = 0.0
        openai_output_cost_per_million_tokens = 0.0

    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            self.run_dir = run_dir

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            return json.dumps(
                {
                    "course_semantics": {
                        "topics": [
                            {
                                "topic_id": "arima",
                                "label": "ARIMA",
                                "aliases": [],
                                "topic_type": "concept",
                                "description": "Forecasting model family.",
                                "source_fields": ["overview"],
                                "evidence_spans": [{"field": "overview", "excerpt": "ARIMA models"}],
                                "confidence": 0.93,
                            }
                        ],
                        "anchors": [
                            {
                                "anchor_id": "arima",
                                "label": "ARIMA",
                                "normalized_label": "arima",
                                "anchor_type": "foundational_vocabulary",
                                "foundational_candidate": True,
                                "learner_facing": True,
                                "requires_entry_question": True,
                                "rationale": "Core named concept.",
                                "source_fields": ["overview"],
                                "evidence_spans": [{"field": "overview", "excerpt": "ARIMA models"}],
                                "confidence": 0.95,
                            }
                        ],
                        "alias_groups": [],
                        "frictions": [],
                    }
                }
            )

    monkeypatch.setattr("course_pipeline.semantic_extract_llm.MeteredLLMJsonClient", FakeClient)

    run_dir = tmp_path / "run123"
    run_dir.mkdir()
    result = extract_semantics_with_llm(raw_course=_course(), settings=FakeSettings(), run_dir=run_dir)

    assert result["extraction_mode"] == "llm"
    assert len(result["topic_records"]) == 1
    assert result["topic_records"][0].label == "ARIMA"
    assert len(result["anchor_candidates"]) == 1


def test_extract_semantics_with_llm_coerces_loose_nested_topic_shape(monkeypatch, tmp_path: Path) -> None:
    class FakeSettings:
        openai_api_key = "test-key"
        openai_model = "gpt-4.1"
        openai_timeout = 30
        openai_input_cost_per_million_tokens = 0.0
        openai_output_cost_per_million_tokens = 0.0

    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            self.run_dir = run_dir

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            return json.dumps(
                {
                    "course_semantics": {
                        "topics": [
                            {
                                "topic": "Vectors in R",
                                "source_fields": ["sections"],
                                "evidence_spans": ["You will be able to create vectors in R."],
                            }
                        ]
                    }
                }
            )

    monkeypatch.setattr("course_pipeline.semantic_extract_llm.MeteredLLMJsonClient", FakeClient)

    run_dir = tmp_path / "run124"
    run_dir.mkdir()
    result = extract_semantics_with_llm(raw_course=_course(), settings=FakeSettings(), run_dir=run_dir)

    assert result["extraction_mode"] == "llm"
    assert len(result["topic_records"]) == 1
    assert result["topic_records"][0].label == "Vectors in R"
    assert len(result["anchor_candidates"]) == 1
    assert result["anchor_candidates"][0].label == "Vectors in R"


def test_extract_semantics_with_llm_falls_back_when_llm_returns_unusable_shape(monkeypatch, tmp_path: Path) -> None:
    class FakeSettings:
        openai_api_key = "test-key"
        openai_model = "gpt-4.1"
        openai_timeout = 30
        openai_input_cost_per_million_tokens = 0.0
        openai_output_cost_per_million_tokens = 0.0

    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            self.run_dir = run_dir

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            return json.dumps({"course_semantics": {"skills": [{"value": "R programming basics"}]}})

    monkeypatch.setattr("course_pipeline.semantic_extract_llm.MeteredLLMJsonClient", FakeClient)

    run_dir = tmp_path / "run125"
    run_dir.mkdir()
    result = extract_semantics_with_llm(raw_course=_course(), settings=FakeSettings(), run_dir=run_dir)

    assert result["extraction_mode"] == "llm_semantic_extract_empty_fallback"
    assert result["topic_records"]
    assert result["anchor_candidates"]
