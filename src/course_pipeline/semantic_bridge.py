from __future__ import annotations

from course_pipeline.questions.candidates.models import FrictionPoint, TopicNode
from course_pipeline.semantic_schemas import FrictionRecord, TopicRecord
from course_pipeline.utils import slugify


def topic_records_to_topic_nodes(records: list[TopicRecord]) -> list[TopicNode]:
    return [
        TopicNode(
            topic_id=record.topic_id,
            label=record.label,
            aliases=list(record.aliases),
            topic_type=record.topic_type,
            description=record.description,
            source_section_ids=[],
            confidence=record.confidence,
        )
        for record in records
    ]


def friction_records_to_friction_points(records: list[FrictionRecord]) -> list[FrictionPoint]:
    points: list[FrictionPoint] = []
    for record in records:
        friction_id = slugify(f"{record.anchor_id}-{record.friction_type}-{record.description}") or (
            f"{record.anchor_id}-{record.friction_type}"
        )
        points.append(
            FrictionPoint(
                friction_id=friction_id,
                topic_id=record.anchor_id,
                friction_type=record.friction_type,
                prompting_signal=record.description,
                learner_symptom=record.description,
                why_it_matters=record.rationale,
                severity=_severity_from_confidence(record.confidence),
                confidence=record.confidence,
            )
        )
    return points


def _severity_from_confidence(confidence: float) -> float:
    return max(0.4, min(1.0, round(confidence, 2)))
