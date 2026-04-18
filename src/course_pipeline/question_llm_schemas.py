from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class CandidateRepairRecord(BaseModel):
    course_id: str
    source_question_id: str
    action: Literal["keep", "rewrite", "drop"]
    original_question: str
    repaired_question: str | None = None
    repair_reason: str
    grounding_rationale: str
    confidence: float
    derived_by_llm: bool = False


class DerivedCandidateRecord(BaseModel):
    course_id: str
    question_text: str
    question_family: Literal["entry", "procedural", "friction", "transfer", "bridge"]
    question_type: Literal[
        "orientation",
        "definition",
        "procedure",
        "comparison",
        "misconception",
        "diagnostic",
        "interpretation",
        "transfer",
        "purpose",
        "when_to_use",
    ]
    mastery_band: Literal["novice", "developing", "proficient"]
    anchor_label: str
    derivation_reason: str
    grounding_rationale: str
    confidence: float
    derived_by_llm: bool = True


class CandidateMergeRecord(BaseModel):
    course_id: str
    candidate_id: str
    source_kind: Literal["original", "repaired", "derived"]
    source_question_id: str | None = None
    llm_stage: Literal["repair", "expand"] | None = None
    provenance_note: str
    original_question: str | None = None
    final_question: str
