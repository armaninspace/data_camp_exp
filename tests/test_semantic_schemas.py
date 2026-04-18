from __future__ import annotations

from course_pipeline.semantic_schemas import (
    AliasGroupRecord,
    AnchorCandidate,
    EvidenceSpan,
    FrictionRecord,
    SemanticDecisionRecord,
    SemanticValidationReport,
    TopicRecord,
)


def test_semantic_records_require_evidence_and_confidence() -> None:
    evidence = [EvidenceSpan(field="overview", excerpt="Learn ARIMA models and forecasting.")]

    topic = TopicRecord(
        course_id="7630",
        topic_id="arima",
        label="ARIMA",
        aliases=["autoregressive integrated moving average"],
        topic_type="concept",
        description="Time-series forecasting model family.",
        source_fields=["overview", "chapters"],
        evidence_spans=evidence,
        confidence=0.91,
    )
    anchor = AnchorCandidate(
        course_id="7630",
        anchor_id="arima",
        label="ARIMA",
        normalized_label="arima",
        anchor_type="foundational_vocabulary",
        foundational_candidate=True,
        learner_facing=True,
        requires_entry_question=True,
        rationale="Central named concept in the course outline.",
        source_fields=["overview"],
        evidence_spans=evidence,
        confidence=0.95,
    )
    alias_group = AliasGroupRecord(
        course_id="7630",
        canonical_label="ARIMA",
        aliases=["autoregressive integrated moving average"],
        rationale="Expanded acronym found in the overview.",
        source_fields=["overview"],
        evidence_spans=evidence,
        confidence=0.8,
    )
    friction = FrictionRecord(
        course_id="7630",
        anchor_id="arima",
        friction_type="interpretation_gap",
        description="Learners may know the acronym without knowing when to apply it.",
        rationale="The course emphasizes forecasting use cases.",
        source_fields=["overview"],
        evidence_spans=evidence,
        confidence=0.74,
    )

    assert topic.evidence_spans[0].field == "overview"
    assert anchor.requires_entry_question is True
    assert alias_group.aliases == ["autoregressive integrated moving average"]
    assert friction.confidence == 0.74


def test_semantic_validation_report_preserves_decision_provenance() -> None:
    decision = SemanticDecisionRecord(
        course_id="7631",
        entity_type="anchor",
        entity_id="overview-segment-1",
        action="drop",
        reason="placeholder_like_anchor",
        provenance_note="Rejected during deterministic sanitation.",
        source_fields=["chapters"],
        evidence_spans=[EvidenceSpan(field="chapters", excerpt="Overview")],
        confidence=0.99,
    )
    report = SemanticValidationReport(
        course_id="7631",
        topic_count=5,
        anchor_count=5,
        alias_group_count=1,
        friction_count=2,
        kept_count=6,
        dropped_count=1,
        merged_count=0,
        rewritten_count=0,
        suspicious_anchor_count=1,
        warnings=["one placeholder-like anchor dropped"],
        decisions=[decision],
    )

    assert report.decisions[0].action == "drop"
    assert report.decisions[0].evidence_spans[0].excerpt == "Overview"
    assert report.suspicious_anchor_count == 1
    assert report.errors == []
