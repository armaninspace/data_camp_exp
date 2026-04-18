from __future__ import annotations

from course_pipeline.question_gen_v3.models import CanonicalDocument, PedagogicalProfile, TopicEdge, TopicNode


def extract_pedagogy(
    doc: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
) -> list[PedagogicalProfile]:
    edge_map: dict[str, list[TopicEdge]] = {}
    for edge in edges:
        edge_map.setdefault(edge.source_id, []).append(edge)
        edge_map.setdefault(edge.target_id, []).append(edge)
    profiles: list[PedagogicalProfile] = []
    for topic in topics:
        lower = topic.label.lower()
        modes = []
        if topic.topic_type in {"concept", "comparison_axis"}:
            modes.append("conceptual")
        if topic.topic_type in {"procedure", "tool"}:
            modes.append("procedural")
        if topic.topic_type in {"comparison_axis", "decision_point"}:
            modes.append("comparative")
        if topic.topic_type in {"diagnostic", "metric", "failure_mode"}:
            modes.append("diagnostic")
        if topic.topic_type in {"metric", "diagnostic"}:
            modes.append("interpretive")
        if topic.topic_type == "decision_point":
            modes.append("transfer")
        misconceptions = []
        sticking = []
        mastery = []
        if any(edge.relation == "contrasts_with" for edge in edge_map.get(topic.topic_id, [])):
            misconceptions.append(f"Confusing {topic.label} with a nearby alternative.")
            mastery.append(f"Explain when {topic.label} is preferable to the alternative.")
        if any(term in lower for term in ["arima", "smoothing", "benchmark", "accuracy", "multivariate", "univariate"]):
            sticking.append(f"Understanding what {topic.label} is for instead of just memorizing the name.")
        if any(term in lower for term in ["accuracy", "test", "white noise", "ljung-box"]):
            mastery.append(f"Interpret what the result of {topic.label} says about the data or model.")
        abstraction = "high" if topic.topic_type in {"comparison_axis", "decision_point"} else "medium" if topic.topic_type in {"concept", "metric"} else "low"
        procedure_load = "high" if topic.topic_type in {"procedure", "tool"} else "medium" if topic.topic_type in {"diagnostic", "decision_point"} else "low"
        notation_load = "medium" if any(term in lower for term in ["arima", "gdp", "xts", "zoo", "ljung-box"]) else "low"
        profiles.append(
            PedagogicalProfile(
                topic_id=topic.topic_id,
                cognitive_modes=sorted(set(modes)) or ["conceptual"],
                abstraction_level=abstraction,
                notation_load=notation_load,
                procedure_load=procedure_load,
                likely_misconceptions=misconceptions,
                likely_sticking_points=sticking,
                evidence_of_mastery=mastery,
            )
        )
    return profiles
