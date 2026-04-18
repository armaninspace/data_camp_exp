from __future__ import annotations

from course_pipeline.question_llm_merge import merge_llm_candidates
from course_pipeline.question_llm_schemas import CandidateRepairRecord, DerivedCandidateRecord
from course_pipeline.questions.candidates.models import QuestionCandidate, TopicNode


def _topic(topic_id: str, label: str) -> TopicNode:
    return TopicNode(
        topic_id=topic_id,
        label=label,
        aliases=[],
        topic_type="concept",
        description=label,
        source_section_ids=[1],
        confidence=0.9,
    )


def _candidate(candidate_id: str, topic_id: str, text: str) -> QuestionCandidate:
    return QuestionCandidate(
        candidate_id=candidate_id,
        topic_id=topic_id,
        slot="novice_definition",
        mastery_band="novice",
        question_type="definition",
        question_text=text,
        rationale="test",
        source_support=["support"],
        linked_friction_ids=[],
        section_ids=[1],
    )


def test_merge_llm_candidates_preserves_rewrites_and_derivations() -> None:
    raw = [
        _candidate("q1", "arima-models", "What is ARIMA?"),
        _candidate("q2", "benchmark-methods", "Why benchmark methods?"),
    ]
    repairs = [
        CandidateRepairRecord(
            course_id="24491",
            source_question_id="q1",
            action="keep",
            original_question="What is ARIMA?",
            repaired_question="What is ARIMA?",
            repair_reason="already_good",
            grounding_rationale="grounded",
            confidence=0.9,
        ),
        CandidateRepairRecord(
            course_id="24491",
            source_question_id="q2",
            action="rewrite",
            original_question="Why benchmark methods?",
            repaired_question="Why do benchmark methods matter?",
            repair_reason="awkward phrasing",
            grounding_rationale="grounded",
            confidence=0.8,
        ),
    ]
    derived = [
        DerivedCandidateRecord(
            course_id="24491",
            question_text="When should I compare ARIMA to benchmark methods?",
            question_family="bridge",
            question_type="comparison",
            mastery_band="proficient",
            anchor_label="ARIMA models",
            derivation_reason="fills comparison gap",
            grounding_rationale="supported by course overview",
            confidence=0.7,
        )
    ]

    merged, report = merge_llm_candidates(
        course_id="24491",
        raw_candidates=raw,
        repair_records=repairs,
        derived_candidates=derived,
        topics=[_topic("arima-models", "ARIMA models"), _topic("benchmark-methods", "Benchmark methods")],
    )

    assert [candidate.question_text for candidate in merged] == [
        "What is ARIMA?",
        "Why do benchmark methods matter?",
        "When should I compare ARIMA to benchmark methods?",
    ]
    assert merged[1].source_kind == "repaired"
    assert merged[1].source_question_id == "q2"
    assert merged[2].source_kind == "derived"
    assert merged[2].llm_stage == "expand"
    assert [row.source_kind for row in report] == ["original", "repaired", "derived"]
