from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.questions.policy.models import CandidateRecord, PolicyScores
from course_pipeline.questions.policy.run_policy import answer_policy_questions, build_v4_1_review_bundle
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


def _rows() -> list[CandidateRecord]:
    return [
        CandidateRecord(
            candidate_id="q1",
            question="What is ARIMA?",
            answer="",
            topic_ids=["arima-models"],
            canonical_id="q1",
            is_correct=True,
            is_grounded=True,
            delivery_class="curated_visible",
            visible=True,
            non_visible_reasons=[],
            scores=PolicyScores(
                correctness=0.9,
                groundedness=0.9,
                contradiction_risk=0.1,
                coherence=0.9,
                query_likelihood=0.9,
                pedagogical_value=0.9,
                answer_richness=0.8,
                mastery_fit=0.9,
                distinctiveness=0.6,
                serviceability=0.8,
                context_dependence=0.2,
                answer_stability=0.9,
            ),
            source_refs=["support"],
            is_foundational_anchor=True,
            is_required_entry_candidate=True,
            is_canonical=True,
            is_alias=False,
            question_type="definition",
            mastery_band="novice",
            family_tags=["entry"],
        )
    ]


def test_answer_policy_questions_uses_metered_client(monkeypatch, tmp_path: Path) -> None:
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

    monkeypatch.setattr("course_pipeline.questions.policy.run_policy.MeteredLLMJsonClient", FakeClient)

    answers = answer_policy_questions(_settings(), tmp_path / "run-456", _course(), _rows())

    assert answers == {"q1": "ARIMA is a forecasting model."}
    assert calls[0]["run_id"] == "run-456"
    assert calls[0]["stage"] == "policy_review_answers"
    assert calls[0]["prompt_version"] == "policy_review_answers_v1"
    assert calls[1]["kwargs"]["course_id"] == "24491"
    assert calls[1]["kwargs"]["entity_ids"] == ["q1"]


def test_build_v4_1_review_bundle_exposes_llm_metering_path(monkeypatch, tmp_path: Path) -> None:
    def fake_answers(settings, run_dir, course, candidate_rows):
        (run_dir / "llm_metering.jsonl").write_text('{"stage":"policy_review_answers"}\n', encoding="utf-8")
        return {"q1": "ARIMA is a forecasting model."}

    monkeypatch.setattr("course_pipeline.questions.policy.run_policy.answer_policy_questions", fake_answers)

    outputs = build_v4_1_review_bundle(
        tmp_path,
        _settings(),
        [_course()],
        {
            "24491": {
                "visible_curated": _rows(),
                "hidden_correct": [],
                "coverage_warnings": [],
                "cache_entries": [],
                "validated_correct_all": _rows(),
                "hard_reject_audit_summary": {"hard_reject_count": 0},
            }
        },
    )

    assert outputs["llm_metering"] == tmp_path / "llm_metering.jsonl"
    assert outputs["llm_metering"].exists()
