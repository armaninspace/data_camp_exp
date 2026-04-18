from __future__ import annotations

from course_pipeline.question_gen_v3.models import FrictionPoint, ScoredCandidate
from course_pipeline.question_gen_v4.policy_models import FamilyTagSet


def tag_families(candidate: ScoredCandidate, frictions_by_topic: dict[str, list[FrictionPoint]]) -> FamilyTagSet:
    tags: list[str] = []
    rationale: dict[str, str] = {}
    c = candidate.candidate
    qtype = c.question_type
    if qtype in {"definition", "orientation", "purpose"}:
        tags.append("entry")
        rationale["entry"] = "Question provides an entry point into a concept or topic."
    if qtype == "comparison":
        tags.append("bridge")
        rationale["bridge"] = "Question bridges nearby concepts or methods through comparison."
    if qtype == "procedure":
        tags.append("procedural")
        rationale["procedural"] = "Question asks how to do something or when to apply a step."
    if qtype in {"misconception", "comparison"} or c.linked_friction_ids:
        tags.append("friction")
        rationale["friction"] = "Question targets confusion, method choice, or a likely learner sticking point."
    if qtype in {"diagnostic", "interpretation"}:
        tags.append("diagnostic")
        rationale["diagnostic"] = "Question asks for adequacy, interpretation, or failure detection."
    if qtype == "transfer":
        tags.append("transfer")
        rationale["transfer"] = "Question asks how the idea changes in a new context."
    if not tags and frictions_by_topic.get(c.topic_id):
        tags.append("friction")
        rationale["friction"] = "Topic has friction signals even though the question type is not explicit."
    return FamilyTagSet(tags=sorted(set(tags)), rationale_by_tag=rationale)
