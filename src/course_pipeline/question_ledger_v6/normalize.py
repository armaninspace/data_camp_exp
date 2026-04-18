from __future__ import annotations

from course_pipeline.question_gen_v4_1.policy_models import CandidateRecord


QUESTION_TYPE_MAP = {
    "definition": "definition",
    "purpose": "purpose",
    "orientation": "purpose",
    "comparison": "comparison",
    "procedure": "procedure",
    "when_to_use": "procedure",
    "misconception": "misconception",
    "diagnostic": "diagnostic",
    "interpretation": "diagnostic",
    "transfer": "application",
}


FAMILY_PRIORITY = ["entry", "bridge", "procedural", "friction", "diagnostic", "transfer"]


def normalize_question_type(question_type: str) -> str:
    return QUESTION_TYPE_MAP.get(question_type, "application")


def select_question_family(family_tags: list[str], question_type: str) -> str:
    if family_tags:
        for family in FAMILY_PRIORITY:
            if family in family_tags:
                return family
    mapped = normalize_question_type(question_type)
    if mapped == "definition" or mapped == "purpose":
        return "entry"
    if mapped == "comparison":
        return "bridge"
    if mapped == "procedure":
        return "procedural"
    if mapped == "misconception":
        return "friction"
    if mapped == "diagnostic":
        return "diagnostic"
    return "transfer"


def normalize_question_text(question_text: str) -> str:
    text = " ".join(question_text.split())
    lowered = text.lower()
    if lowered.startswith("what is repeated cycles?"):
        return "What are repeated cycles?"
    if lowered.startswith("what is ljung-box test?"):
        return "What is the Ljung-Box test?"
    if lowered.startswith("what is xts used for in this course?"):
        return "What is xts used for?"
    if lowered.startswith("what is zoo used for in this course?"):
        return "What is zoo used for?"
    return text


def ledger_tags(record: CandidateRecord, family: str, question_type: str) -> list[str]:
    tags = {family, question_type}
    if record.is_foundational_anchor:
        tags.add("foundational")
    if record.is_required_entry_candidate:
        tags.add("protected")
    if record.is_alias:
        tags.add("alias")
    if not record.visible:
        tags.add("hidden")
    return sorted(tags)
