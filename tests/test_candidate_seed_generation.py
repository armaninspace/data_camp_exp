from __future__ import annotations

from course_pipeline.question_seed_generate import generate_seed_candidates
from course_pipeline.questions.candidates.generate_candidates import generate_candidates
from course_pipeline.questions.candidates.models import CanonicalDocument, TopicNode
from course_pipeline.semantic_schemas import AnchorCandidate, EvidenceSpan


def test_foundational_metric_special_case_keeps_plain_definition_entry_candidates() -> None:
    doc = CanonicalDocument(
        doc_id="24370",
        title="Statistician in R",
        summary="Track summary",
        overview="Track overview",
        sections=[],
    )
    topics = [
        TopicNode(
            topic_id="unemployment",
            label="unemployment",
            aliases=[],
            topic_type="metric",
            description="Finding a job after unemployment.",
            source_section_ids=[10],
            confidence=0.78,
        )
    ]

    candidates = generate_candidates(
        doc,
        topics,
        edges=[],
        pedagogy=[],
        frictions=[],
        config={"generation": {"target_final_per_course": 8}},
    )

    definition_questions = [candidate.question_text for candidate in candidates if candidate.question_type == "definition"]
    assert "What is unemployment?" in definition_questions
    assert any(candidate.question_type == "comparison" for candidate in candidates)


def test_generate_seed_candidates_synthesizes_missing_required_entry_definition(monkeypatch) -> None:
    doc = CanonicalDocument(
        doc_id="9000",
        title="Course",
        summary="Summary",
        overview="Overview",
        sections=[],
    )
    topics = [
        TopicNode(
            topic_id="arima",
            label="ARIMA",
            aliases=[],
            topic_type="concept",
            description="Forecasting model family.",
            source_section_ids=[1],
            confidence=0.95,
        )
    ]
    anchors = [
        AnchorCandidate(
            course_id="9000",
            anchor_id="arima",
            label="ARIMA",
            normalized_label="arima",
            anchor_type="foundational_vocabulary",
            foundational_candidate=True,
            learner_facing=True,
            requires_entry_question=True,
            rationale="Foundational concept.",
            source_fields=["overview"],
            evidence_spans=[EvidenceSpan(field="overview", excerpt="ARIMA models")],
            confidence=0.95,
        )
    ]

    monkeypatch.setattr("course_pipeline.question_seed_generate.generate_candidates", lambda *args, **kwargs: [])

    result = generate_seed_candidates(
        doc,
        topics,
        edges=[],
        pedagogy=[],
        frictions=[],
        config={"generation": {"target_final_per_course": 8}},
        anchors=anchors,
    )

    assert any(candidate.question_text == "What is ARIMA?" for candidate in result["candidates"])
    assert result["invariant_report"].protected_seeds_synthesized == ["arima"]
