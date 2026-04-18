from __future__ import annotations

from course_pipeline.question_gen_v3.models import TopicNode


FOUNDATIONAL_TYPES = {"concept", "tool", "metric", "diagnostic", "comparison_axis", "decision_point"}


def detect_foundational_anchors(topics: list[TopicNode]) -> dict[str, TopicNode]:
    anchors: dict[str, TopicNode] = {}
    for topic in topics:
        if topic.topic_type not in FOUNDATIONAL_TYPES:
            continue
        if topic.confidence < 0.72:
            continue
        anchors[topic.topic_id] = topic
    return anchors


def is_required_entry_candidate(topic_id: str, question_type: str, anchors: dict[str, TopicNode]) -> bool:
    return topic_id in anchors and question_type == "definition"
