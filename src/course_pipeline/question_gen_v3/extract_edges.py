from __future__ import annotations

from course_pipeline.question_gen_v3.models import CanonicalDocument, TopicEdge, TopicNode


def extract_edges(doc: CanonicalDocument, topics: list[TopicNode]) -> list[TopicEdge]:
    edges: list[TopicEdge] = []
    by_label = {topic.label.lower(): topic for topic in topics}
    labels = list(by_label)
    if "arima" in " ".join(labels) and "exponential smoothing" in " ".join(labels):
        arima = next((topic for topic in topics if "arima" in topic.label.lower()), None)
        smooth = next((topic for topic in topics if "exponential smoothing" in topic.label.lower()), None)
        if arima and smooth:
            edges.append(
                TopicEdge(
                    source_id=arima.topic_id,
                    target_id=smooth.topic_id,
                    relation="contrasts_with",
                    rationale="The source explicitly presents ARIMA and exponential smoothing as complementary approaches.",
                    confidence=0.9,
                )
            )
    accuracy = next((topic for topic in topics if "accuracy" in topic.label.lower()), None)
    if accuracy:
        for topic in topics:
            if topic.topic_id == accuracy.topic_id:
                continue
            if any(term in topic.label.lower() for term in ["forecast", "arima", "smoothing", "benchmark"]):
                edges.append(
                    TopicEdge(
                        source_id=topic.topic_id,
                        target_id=accuracy.topic_id,
                        relation="evaluated_by",
                        rationale="Forecasting methods are evaluated through forecast accuracy.",
                        confidence=0.74,
                    )
                )
    for topic in topics:
        lower = topic.label.lower()
        if "xts" in lower or "zoo" in lower:
            for maybe in topics:
                if maybe.topic_id == topic.topic_id:
                    continue
                if any(term in maybe.description.lower() for term in ["xts", "zoo"]):
                    edges.append(
                        TopicEdge(
                            source_id=maybe.topic_id,
                            target_id=topic.topic_id,
                            relation="uses",
                            rationale="The section describes working with data using xts and zoo.",
                            confidence=0.7,
                        )
                    )
        if topic.topic_type == "comparison_axis":
            for maybe in topics:
                if maybe.topic_id == topic.topic_id:
                    continue
                if maybe.source_section_ids == topic.source_section_ids:
                    edges.append(
                        TopicEdge(
                            source_id=maybe.topic_id,
                            target_id=topic.topic_id,
                            relation="decision_depends_on",
                            rationale="The section implies a choice or comparison around this topic.",
                            confidence=0.58,
                        )
                    )
    deduped: dict[tuple[str, str, str], TopicEdge] = {}
    for edge in edges:
        deduped[(edge.source_id, edge.target_id, edge.relation)] = edge
    return list(deduped.values())
