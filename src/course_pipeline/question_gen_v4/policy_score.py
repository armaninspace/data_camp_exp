from __future__ import annotations

from course_pipeline.question_gen_v3.models import FrictionPoint, ScoredCandidate
from course_pipeline.question_gen_v4.policy_models import PolicyScores
from course_pipeline.question_gen_v4.question_signals import detect_question_signals


def compute_policy_scores(
    candidate: ScoredCandidate,
    frictions_by_topic: dict[str, list[FrictionPoint]],
) -> PolicyScores:
    c = candidate.candidate
    s = candidate.score
    topic_frictions = frictions_by_topic.get(c.topic_id, [])
    signals = detect_question_signals(c.question_text)
    generic_penalty = 0.0
    if signals["generic_template"]:
        generic_penalty += 0.18
    if signals["course_context_dependent"]:
        generic_penalty += 0.08
    if c.question_type in {"orientation", "transfer"} and signals["course_context_dependent"]:
        generic_penalty += 0.07
    if topic_frictions and c.linked_friction_ids:
        generic_penalty = max(0.0, generic_penalty - 0.08)
    correctness = min(1.0, 0.7 + 0.2 * s.groundedness)
    groundedness = s.groundedness
    contradiction_risk = 0.1 if groundedness >= 0.8 else 0.22 if groundedness >= 0.7 else 0.35
    coherence = 0.88 if c.question_text.endswith("?") and len(c.question_text.split()) >= 5 else 0.65
    query_likelihood = 0.9 if len(c.question_text.split()) <= 14 else 0.72
    if c.question_type in {"definition", "procedure", "comparison"}:
        query_likelihood = min(1.0, query_likelihood + 0.05)
    if signals["generic_template"]:
        query_likelihood = max(0.0, query_likelihood - 0.08)
    pedagogical_value = min(1.0, 0.38 + 0.32 * s.friction_value + 0.18 * s.answer_richness + 0.12 * s.mastery_fit)
    if c.question_type in {"comparison", "diagnostic", "misconception"} and topic_frictions:
        pedagogical_value = min(1.0, pedagogical_value + 0.05)
    pedagogical_value = max(0.0, pedagogical_value - generic_penalty)
    answer_richness = s.answer_richness
    mastery_fit = s.mastery_fit
    distinctiveness = s.novelty
    context_dependence = 0.65 if signals["course_context_dependent"] else 0.35
    if c.question_type == "transfer":
        context_dependence = max(context_dependence, 0.5)
    if signals["generic_template"]:
        context_dependence = min(1.0, context_dependence + 0.12)
    serviceability = min(
        1.0,
        0.18
        + 0.33 * groundedness
        + 0.17 * coherence
        + 0.16 * answer_richness
        + 0.08 * query_likelihood
        - 0.16 * context_dependence
        - generic_penalty,
    )
    if c.question_type == "definition" and not signals["generic_template"]:
        serviceability += 0.06
    if c.question_type == "procedure" and not signals["course_context_dependent"]:
        serviceability += 0.03
    if c.question_type in {"diagnostic", "transfer"} and not topic_frictions:
        serviceability -= 0.05
    serviceability = max(0.0, min(1.0, serviceability))
    answer_stability = min(
        1.0,
        0.25
        + 0.34 * groundedness
        + 0.16 * coherence
        + 0.18 * answer_richness
        - 0.18 * context_dependence
        - 0.6 * generic_penalty,
    )
    if c.question_type == "definition" and not signals["generic_template"]:
        answer_stability += 0.06
    if c.question_type == "procedure" and not signals["course_context_dependent"]:
        answer_stability += 0.03
    answer_stability = max(0.0, min(1.0, answer_stability))
    return PolicyScores(
        correctness=round(correctness, 4),
        groundedness=round(groundedness, 4),
        contradiction_risk=round(contradiction_risk, 4),
        coherence=round(coherence, 4),
        query_likelihood=round(query_likelihood, 4),
        pedagogical_value=round(pedagogical_value, 4),
        answer_richness=round(answer_richness, 4),
        mastery_fit=round(mastery_fit, 4),
        distinctiveness=round(distinctiveness, 4),
        serviceability=round(serviceability, 4),
        context_dependence=round(context_dependence, 4),
        answer_stability=round(answer_stability, 4),
    )
