from __future__ import annotations

from course_pipeline.question_gen_v3.models import QuestionCandidate
from course_pipeline.question_gen_v4.policy_models import PolicyScores
from course_pipeline.question_gen_v4.question_signals import detect_question_signals


def serveability_gate(candidate: QuestionCandidate, scores: PolicyScores, config: dict) -> tuple[bool, list[str]]:
    thresholds = config["serving_thresholds"]
    reasons: list[str] = []
    signals = detect_question_signals(candidate.question_text)
    if scores.serviceability >= thresholds["min_serviceability"]:
        reasons.append("servable_pass")
    else:
        reasons.append("servable_fail_low_serviceability")
    if scores.context_dependence > thresholds["max_context_dependence"]:
        reasons.append("servable_fail_context_dependence")
    if scores.answer_stability < thresholds["min_answer_stability"]:
        reasons.append("servable_fail_instability")
    if signals["generic_template"] and not candidate.linked_friction_ids:
        reasons.extend(signals["generic_template_codes"])
        reasons.append("servable_fail_generic_template")
    if candidate.question_type == "orientation" and signals["course_context_dependent"]:
        reasons.append("servable_fail_orientation_context")
    servable = (
        scores.serviceability >= thresholds["min_serviceability"]
        and scores.context_dependence <= thresholds["max_context_dependence"]
        and scores.answer_stability >= thresholds["min_answer_stability"]
        and not (signals["generic_template"] and not candidate.linked_friction_ids)
        and not (candidate.question_type == "orientation" and signals["course_context_dependent"])
    )
    return servable, reasons
