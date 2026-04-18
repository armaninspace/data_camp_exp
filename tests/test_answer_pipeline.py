from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.answer_generate_llm import generate_answers_with_llm
from course_pipeline.answer_pipeline import run_answer_generation_for_course
from course_pipeline.answer_validate_llm import validate_answers_with_llm
from course_pipeline.config import Settings
from course_pipeline.questions.policy.models import CandidateRecord, PolicyScores
from course_pipeline.schemas import ChapterOut, NormalizedCourse


def _course() -> NormalizedCourse:
    return NormalizedCourse(
        course_id="24491",
        source_url="https://example.com/course",
        final_url="https://example.com/course",
        provider="DataCamp",
        title="Forecasting in R",
        summary="Learn benchmark methods and ARIMA models.",
        overview="ARIMA models and benchmark methods are introduced for time series forecasting.",
        raw_yaml_path="/tmp/course.yaml",
        chapters=[
            ChapterOut(
                chapter_index=1,
                title="Intro",
                summary="Benchmark methods and ARIMA models.",
                source="syllabus",
                confidence=1.0,
            )
        ],
    )


def _candidate_rows() -> list[CandidateRecord]:
    return [
        CandidateRecord(
            candidate_id="arima-definition",
            question="What is ARIMA?",
            answer="",
            topic_ids=["arima"],
            canonical_id="arima-definition",
            is_correct=True,
            is_grounded=True,
            delivery_class="curated_visible",
            visible=True,
            non_visible_reasons=[],
            scores=PolicyScores(
                correctness=0.93,
                groundedness=0.92,
                contradiction_risk=0.02,
                coherence=0.94,
                query_likelihood=0.91,
                pedagogical_value=0.88,
                answer_richness=0.85,
                mastery_fit=0.9,
                distinctiveness=0.81,
                serviceability=0.9,
                context_dependence=0.2,
                answer_stability=0.89,
            ),
            source_refs=["ARIMA models are introduced for time series forecasting."],
            is_foundational_anchor=True,
            is_required_entry_candidate=True,
            is_canonical=True,
            is_alias=False,
            question_type="definition",
            mastery_band="novice",
        )
    ]


def _settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        openai_model="gpt-4.1",
        openai_timeout=30,
        openai_input_cost_per_million_tokens=2.0,
        openai_output_cost_per_million_tokens=8.0,
        database_url="postgresql+psycopg://agent@127.0.0.1:55432/course_pipeline",
        output_root=Path("/tmp/unused"),
    )


def test_generate_answers_with_llm_uses_metered_client(monkeypatch, tmp_path: Path) -> None:
    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            assert run_id == "run-1"
            assert stage == "answer_generate"
            assert prompt_version == "answer_generate_v1"

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            payload = json.loads(user_prompt)
            assert payload["course"]["course_id"] == "24491"
            return json.dumps(
                {
                    "answers": [
                        {
                            "candidate_id": "arima-definition",
                            "answer_markdown": "ARIMA is a forecasting model family used for time series.",
                            "generation_rationale": "supported by the course overview",
                            "confidence": 0.91,
                        }
                    ]
                }
            )

    monkeypatch.setattr("course_pipeline.answer_generate_llm.MeteredLLMJsonClient", FakeClient)
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    records, payload = generate_answers_with_llm(
        settings=_settings(),
        run_dir=run_dir,
        course=_course(),
        candidate_rows=_candidate_rows(),
    )

    assert payload["questions"][0]["candidate_id"] == "arima-definition"
    assert records[0].candidate_id == "arima-definition"
    assert records[0].confidence == 0.91


def test_validate_answers_with_llm_falls_back_deterministically_without_key(tmp_path: Path) -> None:
    generated, _ = generate_answers_with_llm(
        settings=None,
        run_dir=None,
        course=_course(),
        candidate_rows=_candidate_rows(),
    )
    assert generated == []

    result = run_answer_generation_for_course(
        course=_course(),
        candidate_rows=_candidate_rows(),
        settings=None,
        run_dir=tmp_path / "run-1",
    )

    assert result["generated_answers"] == []
    assert result["answer_validation_logs"] == []
    assert result["review_answers"] == []


def test_validate_answers_with_llm_rejects_empty_answers_without_llm(tmp_path: Path) -> None:
    from course_pipeline.answer_schemas import GeneratedAnswerRecord

    validations, payload = validate_answers_with_llm(
        settings=None,
        run_dir=None,
        course=_course(),
        candidate_rows=_candidate_rows(),
        generated_answers=[
            GeneratedAnswerRecord(
                course_id="24491",
                candidate_id="arima-definition",
                question_text="What is ARIMA?",
                answer_markdown="",
                source_refs=["overview"],
                generation_rationale="test",
                confidence=0.1,
            )
        ],
    )

    assert payload["answers"][0]["candidate_id"] == "arima-definition"
    assert validations[0].validation_status == "rejected"
    assert "empty_answer" in validations[0].reasons
