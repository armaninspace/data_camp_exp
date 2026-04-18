from __future__ import annotations

from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.question_llm_schemas import CandidateRepairRecord
from course_pipeline.question_refine_llm import repair_candidates_with_llm
from course_pipeline.questions.candidates.models import CanonicalDocument, QuestionCandidate, TopicNode
from course_pipeline.questions.candidates.pipeline import run_question_gen_v3_for_course
from course_pipeline.schemas import ChapterOut, NormalizedCourse
from course_pipeline.semantic_schemas import AnchorCandidate, EvidenceSpan, TopicRecord


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
        course_id="7630",
        source_url="https://example.com/course",
        final_url="https://example.com/course",
        provider="DataCamp",
        title="Forecasting in R",
        summary="Learn ARIMA models and benchmark methods for forecasting.",
        overview="This course teaches ARIMA models and forecast accuracy.",
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


def test_repair_candidates_with_llm_preserves_required_plain_definitions(monkeypatch, tmp_path: Path) -> None:
    course = CanonicalDocument(
        doc_id="7630",
        title="Forecasting in R",
        summary="Learn ARIMA models",
        overview="ARIMA models",
        sections=[],
    )
    topics = [
        TopicNode(
            topic_id="arima",
            label="ARIMA",
            aliases=[],
            topic_type="concept",
            description="Forecasting model family",
            source_section_ids=[1],
            confidence=0.9,
        )
    ]
    candidates = [
        QuestionCandidate(
            candidate_id="arima-def",
            topic_id="arima",
            slot="novice_definition",
            mastery_band="novice",
            question_type="definition",
            question_text="What is ARIMA?",
            rationale="plain definition",
            source_support=["overview"],
            linked_friction_ids=[],
            section_ids=[1],
        )
    ]

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def invoke_json(self, *args, **kwargs):
            return '{"repairs":[{"source_question_id":"arima-def","action":"drop","repair_reason":"bad","confidence":0.2}]}'

    monkeypatch.setattr("course_pipeline.question_refine_llm.MeteredLLMJsonClient", FakeClient)
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()

    repairs, _payload = repair_candidates_with_llm(
        settings=_settings(),
        run_dir=run_dir,
        course=course,
        topics=topics,
        edges=[],
        pedagogy=[],
        frictions=[],
        candidates=candidates,
        foundational_anchor_labels=["ARIMA"],
    )

    assert repairs[0].action == "keep"
    assert repairs[0].repaired_question == "What is ARIMA?"
    assert repairs[0].repair_reason == "protected_required_entry_kept"


def test_overview_segment_placeholder_does_not_survive_to_final_candidates(monkeypatch, tmp_path: Path) -> None:
    def fake_extract_semantics_with_llm(*, raw_course, settings, run_dir):
        evidence = [EvidenceSpan(field="chapters", excerpt="Overview")]
        return {
            "normalized_document": CanonicalDocument(
                doc_id=raw_course.course_id,
                title=raw_course.title,
                summary=raw_course.summary,
                overview=raw_course.overview,
                level=None,
                subjects=raw_course.subjects,
                sections=[],
            ),
            "payload": {"course": {"course_id": raw_course.course_id}},
            "topic_records": [
                TopicRecord(
                    course_id=raw_course.course_id,
                    topic_id="overview-segment-1",
                    label="overview-segment-1",
                    aliases=[],
                    topic_type="concept",
                    description="placeholder",
                    source_fields=["chapters"],
                    evidence_spans=evidence,
                    confidence=0.6,
                ),
                TopicRecord(
                    course_id=raw_course.course_id,
                    topic_id="arima",
                    label="ARIMA",
                    aliases=[],
                    topic_type="concept",
                    description="Forecasting model family",
                    source_fields=["overview"],
                    evidence_spans=[EvidenceSpan(field="overview", excerpt="ARIMA models")],
                    confidence=0.95,
                ),
            ],
            "anchor_candidates": [
                AnchorCandidate(
                    course_id=raw_course.course_id,
                    anchor_id="overview-segment-1",
                    label="overview-segment-1",
                    normalized_label="overview-segment-1",
                    anchor_type="contextual_topic",
                    foundational_candidate=False,
                    learner_facing=False,
                    requires_entry_question=False,
                    rationale="placeholder",
                    source_fields=["chapters"],
                    evidence_spans=evidence,
                    confidence=0.6,
                ),
                AnchorCandidate(
                    course_id=raw_course.course_id,
                    anchor_id="arima",
                    label="ARIMA",
                    normalized_label="arima",
                    anchor_type="foundational_vocabulary",
                    foundational_candidate=True,
                    learner_facing=True,
                    requires_entry_question=True,
                    rationale="real anchor",
                    source_fields=["overview"],
                    evidence_spans=[EvidenceSpan(field="overview", excerpt="ARIMA models")],
                    confidence=0.95,
                ),
            ],
            "alias_groups": [],
            "friction_records": [],
            "extraction_mode": "llm",
        }

    monkeypatch.setattr("course_pipeline.semantic_pipeline.extract_semantics_with_llm", fake_extract_semantics_with_llm)
    result = run_question_gen_v3_for_course(_course(), settings=None, run_dir=tmp_path / "run-1")

    assert all(candidate.topic_id != "overview-segment-1" for candidate in result["merged_candidates"])
    assert all(candidate.topic_id == "arima" for candidate in result["raw_candidates"])
