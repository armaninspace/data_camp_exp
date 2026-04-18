from __future__ import annotations

from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.question_llm_schemas import CandidateRepairRecord, DerivedCandidateRecord
from course_pipeline.questions.candidates.pipeline import run_question_gen_v3_for_course
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


def test_run_question_gen_v3_for_course_includes_llm_enhancement_artifacts(monkeypatch, tmp_path: Path) -> None:
    def fake_repair_candidates_with_llm(**kwargs):
        candidate = kwargs["candidates"][0]
        return (
            [
                CandidateRepairRecord(
                    course_id="24491",
                    source_question_id=candidate.candidate_id,
                    action="rewrite",
                    original_question=candidate.question_text,
                    repaired_question="What is ARIMA?",
                    repair_reason="normalize beginner definition",
                    grounding_rationale="supported by course text",
                    confidence=0.9,
                )
            ]
            + [
                CandidateRepairRecord(
                    course_id="24491",
                    source_question_id=item.candidate_id,
                    action="keep",
                    original_question=item.question_text,
                    repaired_question=item.question_text,
                    repair_reason="keep",
                    grounding_rationale="grounded",
                    confidence=0.8,
                )
                for item in kwargs["candidates"][1:]
            ],
            {"repair": True},
        )

    def fake_expand_candidates_with_llm(**kwargs):
        return (
            [
                DerivedCandidateRecord(
                    course_id="24491",
                    question_text="When would I compare ARIMA with a benchmark method?",
                    question_family="bridge",
                    question_type="comparison",
                    mastery_band="proficient",
                    anchor_label="ARIMA models",
                    derivation_reason="fills comparison gap",
                    grounding_rationale="supported by chapter summary",
                    confidence=0.7,
                )
            ],
            {"expand": True},
        )

    monkeypatch.setattr(
        "course_pipeline.questions.candidates.pipeline.repair_candidates_with_llm",
        fake_repair_candidates_with_llm,
    )
    monkeypatch.setattr(
        "course_pipeline.questions.candidates.pipeline.expand_candidates_with_llm",
        fake_expand_candidates_with_llm,
    )

    result = run_question_gen_v3_for_course(_course(), settings=_settings(), run_dir=tmp_path / "run-1")

    assert result["candidate_repairs"]
    assert result["candidate_expansions"]
    assert result["candidate_merge_report"]
    assert result["repair_payload"] == {"repair": True}
    assert result["expand_payload"] == {"expand": True}
    assert any(candidate.source_kind == "derived" for candidate in result["merged_candidates"])
