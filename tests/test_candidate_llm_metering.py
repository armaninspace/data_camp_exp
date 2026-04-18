from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.questions.candidates.models import (
    CandidateScore,
    QuestionCandidate,
    ScoredCandidate,
)
from course_pipeline.questions.candidates.pipeline import answer_selected_questions, build_review_bundle
from course_pipeline.schemas import ChapterOut, NormalizedCourse


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


def _course() -> NormalizedCourse:
    return NormalizedCourse(
        course_id="24491",
        source_url="https://example.com",
        final_url="https://example.com",
        provider="DataCamp",
        title="Forecasting in R",
        summary="Summary",
        overview="Overview",
        raw_yaml_path="/tmp/course.yaml",
        chapters=[
            ChapterOut(
                chapter_index=1,
                title="Intro",
                summary="Intro summary",
                source="syllabus",
                confidence=1.0,
            )
        ],
    )


def _selected() -> list[ScoredCandidate]:
    return [
        ScoredCandidate(
            candidate=QuestionCandidate(
                candidate_id="q1",
                topic_id="arima-models",
                slot="novice_definition",
                mastery_band="novice",
                question_type="definition",
                question_text="What is ARIMA?",
                rationale="Core concept",
                source_support=["support"],
                linked_friction_ids=[],
                section_ids=[1],
            ),
            score=CandidateScore(
                friction_value=0.5,
                specificity=0.7,
                answer_richness=0.8,
                mastery_fit=0.9,
                novelty=0.5,
                groundedness=0.9,
                total=4.3,
            ),
            rejection_flags=[],
        )
    ]


def test_answer_selected_questions_uses_metered_client(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict] = []

    class FakeClient:
        def __init__(self, settings, *, run_id, run_dir, stage, prompt_version):
            calls.append(
                {
                    "run_id": run_id,
                    "run_dir": run_dir,
                    "stage": stage,
                    "prompt_version": prompt_version,
                }
            )

        def invoke_json(self, system_prompt, user_prompt, **kwargs):
            calls.append({"kwargs": kwargs, "payload": json.loads(user_prompt)})
            return json.dumps(
                {
                    "answers": [
                        {
                            "candidate_id": "q1",
                            "answer_markdown": "ARIMA is a forecasting model.",
                        }
                    ]
                }
            )

    monkeypatch.setattr("course_pipeline.questions.candidates.pipeline.MeteredLLMJsonClient", FakeClient)

    answers = answer_selected_questions(_settings(), tmp_path / "run-123", _course(), _selected())

    assert answers == {"q1": "ARIMA is a forecasting model."}
    assert calls[0]["run_id"] == "run-123"
    assert calls[0]["stage"] == "candidate_review_answers"
    assert calls[0]["prompt_version"] == "candidate_review_answers_v1"
    assert calls[1]["kwargs"]["course_id"] == "24491"
    assert calls[1]["kwargs"]["entity_ids"] == ["q1"]


def test_build_review_bundle_exposes_llm_metering_path(monkeypatch, tmp_path: Path) -> None:
    def fake_answers(settings, run_dir, course, selected):
        (run_dir / "llm_metering.jsonl").write_text('{"stage":"candidate_review_answers"}\n', encoding="utf-8")
        return {"q1": "ARIMA is a forecasting model."}

    monkeypatch.setattr("course_pipeline.questions.candidates.pipeline.answer_selected_questions", fake_answers)

    outputs = build_review_bundle(
        tmp_path,
        _settings(),
        [_course()],
        {"24491": {"final_selected": _selected()}},
    )

    assert outputs["llm_metering"] == tmp_path / "llm_metering.jsonl"
    assert outputs["llm_metering"].exists()
