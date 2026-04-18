from __future__ import annotations

from course_pipeline.semantic_bridge import (
    friction_records_to_friction_points,
    topic_records_to_topic_nodes,
)
from course_pipeline.semantic_schemas import EvidenceSpan, FrictionRecord, TopicRecord


def test_topic_records_to_topic_nodes_preserves_core_fields() -> None:
    records = [
        TopicRecord(
            course_id="7630",
            topic_id="arima",
            label="ARIMA",
            aliases=["autoregressive integrated moving average"],
            topic_type="concept",
            description="Forecasting model family.",
            source_fields=["overview"],
            evidence_spans=[EvidenceSpan(field="overview", excerpt="ARIMA models")],
            confidence=0.91,
        )
    ]

    topics = topic_records_to_topic_nodes(records)

    assert len(topics) == 1
    assert topics[0].topic_id == "arima"
    assert topics[0].label == "ARIMA"
    assert topics[0].aliases == ["autoregressive integrated moving average"]
    assert topics[0].confidence == 0.91


def test_friction_records_to_friction_points_preserves_anchor_and_confidence() -> None:
    records = [
        FrictionRecord(
            course_id="7630",
            anchor_id="arima",
            friction_type="interpretation_gap",
            description="Learners may know the term but not when to apply it.",
            rationale="The course frames ARIMA as a method-choice concept.",
            source_fields=["overview"],
            evidence_spans=[EvidenceSpan(field="overview", excerpt="ARIMA models")],
            confidence=0.73,
        )
    ]

    points = friction_records_to_friction_points(records)

    assert len(points) == 1
    assert points[0].topic_id == "arima"
    assert points[0].confidence == 0.73
    assert points[0].severity == 0.73
    assert points[0].learner_symptom == "Learners may know the term but not when to apply it."
