from __future__ import annotations

from course_pipeline.questions.candidates.models import FrictionPoint, PedagogicalProfile, TopicEdge, TopicNode
from course_pipeline.utils import slugify


def mine_friction(
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
) -> list[FrictionPoint]:
    profiles = {profile.topic_id: profile for profile in pedagogy}
    frictions: list[FrictionPoint] = []
    seen: set[str] = set()
    for edge in edges:
        if edge.relation in {"contrasts_with", "decision_depends_on"}:
            fid = slugify(f"{edge.source_id}-{edge.relation}-{edge.target_id}")
            if fid in seen:
                continue
            seen.add(fid)
            frictions.append(
                FrictionPoint(
                    friction_id=fid,
                    topic_id=edge.source_id,
                    friction_type="choice" if edge.relation == "decision_depends_on" else "confusion",
                    prompting_signal=edge.rationale,
                    learner_symptom="The learner is unsure how two nearby methods or ideas differ.",
                    why_it_matters="This affects method choice and interpretation.",
                    severity=0.85 if edge.relation == "contrasts_with" else 0.75,
                    confidence=edge.confidence,
                )
            )
        if edge.relation in {"evaluated_by", "failure_revealed_by"}:
            fid = slugify(f"{edge.source_id}-{edge.relation}-{edge.target_id}")
            if fid in seen:
                continue
            seen.add(fid)
            frictions.append(
                FrictionPoint(
                    friction_id=fid,
                    topic_id=edge.source_id,
                    friction_type="interpretation_gap",
                    prompting_signal=edge.rationale,
                    learner_symptom="The learner does not know what signal or result would indicate success or failure.",
                    why_it_matters="Without interpretation, procedures stay mechanical and fragile.",
                    severity=0.8,
                    confidence=edge.confidence,
                )
            )
    for topic in topics:
        profile = profiles.get(topic.topic_id)
        if profile is None:
            continue
        if topic.topic_type in {"procedure", "tool"}:
            fid = slugify(f"{topic.topic_id}-sequence-risk")
            if fid not in seen:
                seen.add(fid)
                frictions.append(
                    FrictionPoint(
                        friction_id=fid,
                        topic_id=topic.topic_id,
                        friction_type="prerequisite_gap",
                        prompting_signal=f"{topic.label} is a step that can be applied too early or too mechanically.",
                        learner_symptom="The learner applies the step without knowing when it is needed or what it changes.",
                        why_it_matters="This affects data preparation and downstream interpretation.",
                        severity=0.72,
                        confidence=0.72,
                    )
                )
        for sticking in profile.likely_sticking_points:
            fid = slugify(f"{topic.topic_id}-{sticking}")
            if fid in seen:
                continue
            seen.add(fid)
            frictions.append(
                FrictionPoint(
                    friction_id=fid,
                    topic_id=topic.topic_id,
                    friction_type="prerequisite_gap" if topic.topic_type in {"diagnostic", "metric"} else "confusion",
                    prompting_signal=sticking,
                    learner_symptom="The learner can name the topic but not use it confidently.",
                    why_it_matters="This blocks explanation, comparison, or interpretation.",
                    severity=0.65,
                    confidence=0.7,
                )
            )
        if topic.topic_type == "decision_point":
            fid = slugify(f"{topic.topic_id}-transfer")
            if fid not in seen:
                seen.add(fid)
                frictions.append(
                    FrictionPoint(
                        friction_id=fid,
                        topic_id=topic.topic_id,
                        friction_type="transfer_gap",
                        prompting_signal=f"{topic.label} requires choosing or applying ideas in context.",
                        learner_symptom="The learner does not know how to carry the idea into a new case.",
                        why_it_matters="Transfer separates recognition from usable understanding.",
                        severity=0.8,
                        confidence=0.74,
                    )
                )
    return frictions
