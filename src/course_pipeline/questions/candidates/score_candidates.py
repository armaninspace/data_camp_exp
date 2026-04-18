from __future__ import annotations

from course_pipeline.questions.candidates.models import CandidateScore, FrictionPoint, QuestionCandidate, ScoredCandidate, TopicEdge, TopicNode
from course_pipeline.semantic_schemas import AnchorCandidate


def score_candidates(
    candidates: list[QuestionCandidate],
    topics: list[TopicNode],
    edges: list[TopicEdge],
    frictions: list[FrictionPoint],
    config: dict,
    *,
    anchor_candidates: list[AnchorCandidate] | None = None,
) -> list[ScoredCandidate]:
    topic_map = {topic.topic_id: topic for topic in topics}
    anchor_map = {anchor.anchor_id: anchor for anchor in (anchor_candidates or [])}
    friction_map: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        friction_map.setdefault(friction.topic_id, []).append(friction)
    edge_count: dict[str, int] = {}
    for edge in edges:
        edge_count[edge.source_id] = edge_count.get(edge.source_id, 0) + 1
        edge_count[edge.target_id] = edge_count.get(edge.target_id, 0) + 1
    weights = config["weights"]
    scored: list[ScoredCandidate] = []
    for candidate in candidates:
        topic = topic_map[candidate.topic_id]
        topic_frictions = friction_map.get(candidate.topic_id, [])
        friction_value = min(1.0, 0.35 + sum(f.severity for f in topic_frictions) / max(1, len(topic_frictions)))
        specificity = min(1.0, 0.45 + 0.1 * len(topic.label.split()) + 0.08 * edge_count.get(topic.topic_id, 0))
        answer_richness = 0.45
        if candidate.question_type in {"comparison", "diagnostic", "transfer", "misconception"}:
            answer_richness += 0.25
        if topic.topic_type in {"comparison_axis", "decision_point", "diagnostic", "metric"}:
            answer_richness += 0.15
        answer_richness = min(1.0, answer_richness)
        mastery_fit = 0.9 if (
            (candidate.mastery_band == "novice" and candidate.question_type in {"orientation", "definition", "purpose"})
            or (candidate.mastery_band == "developing" and candidate.question_type in {"procedure", "comparison", "misconception"})
            or (candidate.mastery_band == "proficient" and candidate.question_type in {"diagnostic", "transfer", "comparison", "interpretation"})
        ) else 0.45
        novelty = 0.85 if candidate.question_type not in {"definition", "orientation"} else 0.62
        groundedness = min(1.0, 0.55 + 0.1 * len(candidate.source_support) + 0.2 * topic.confidence)
        if candidate.llm_grounding_confidence is not None:
            groundedness = min(1.0, groundedness + 0.05 * candidate.llm_grounding_confidence)
        semantic_confidence = anchor_map.get(candidate.topic_id).confidence if candidate.topic_id in anchor_map else topic.confidence
        llm_repair_confidence = candidate.llm_repair_confidence or 0.0
        llm_derivation_confidence = candidate.llm_derivation_confidence or 0.0
        total = (
            weights["friction_value"] * friction_value
            + weights["specificity"] * specificity
            + weights["answer_richness"] * answer_richness
            + weights["mastery_fit"] * mastery_fit
            + weights["novelty"] * novelty
            + weights["groundedness"] * groundedness
        )
        total = min(
            1.0,
            total
            + 0.03 * semantic_confidence
            + 0.02 * llm_repair_confidence
            + 0.02 * llm_derivation_confidence,
        )
        scored.append(
            ScoredCandidate(
                candidate=candidate,
                score=CandidateScore(
                    friction_value=round(friction_value, 4),
                    specificity=round(specificity, 4),
                    answer_richness=round(answer_richness, 4),
                    mastery_fit=round(mastery_fit, 4),
                    novelty=round(novelty, 4),
                    groundedness=round(groundedness, 4),
                    semantic_confidence=round(semantic_confidence, 4),
                    llm_repair_confidence=round(llm_repair_confidence, 4),
                    llm_derivation_confidence=round(llm_derivation_confidence, 4),
                    total=round(total, 4),
                ),
            )
        )
    return scored
