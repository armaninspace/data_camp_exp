from __future__ import annotations

from course_pipeline.foundational_entry_questions import anchor_entry_label, is_plain_definition_question
from course_pipeline.question_gen_v3.models import TopicNode


FOUNDATIONAL_TYPES = {"concept", "tool", "metric", "diagnostic", "comparison_axis", "decision_point"}
GENERIC_FOUNDATIONAL_LABELS = {"advanced methods", "methods", "introduction", "overview", "data"}


def detect_foundational_anchors(topics: list[TopicNode]) -> dict[str, TopicNode]:
    canonical_topics: dict[str, TopicNode] = {}
    for topic in topics:
        if topic.topic_type not in FOUNDATIONAL_TYPES:
            continue
        if topic.confidence < 0.72:
            continue
        if topic.label.lower().strip() in GENERIC_FOUNDATIONAL_LABELS:
            continue
        key = anchor_entry_label(topic.label).lower()
        existing = canonical_topics.get(key)
        if existing is None or topic.confidence > existing.confidence:
            canonical_topics[key] = topic
    return {topic.topic_id: topic for topic in canonical_topics.values()}


def is_required_entry_candidate(
    topic_id: str,
    question_type: str,
    question_text: str,
    anchors: dict[str, TopicNode],
) -> bool:
    topic = anchors.get(topic_id)
    if not topic or question_type != "definition":
        return False
    return is_plain_definition_question(topic.label, question_text)
