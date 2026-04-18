from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from course_pipeline.question_gen_v4.policy_models import PolicyScores


DeliveryClass = Literal["curated_visible", "cache_servable", "alias_only", "analysis_only", "hard_reject"]


class CandidateRecord(BaseModel):
    candidate_id: str
    question: str
    answer: str = ""
    topic_ids: list[str] = Field(default_factory=list)
    canonical_id: str | None = None
    is_correct: bool
    is_grounded: bool
    delivery_class: DeliveryClass
    visible: bool
    non_visible_reasons: list[str] = Field(default_factory=list)
    scores: PolicyScores
    source_refs: list[str] = Field(default_factory=list)
    is_foundational_anchor: bool = False
    is_required_entry_candidate: bool = False
    is_canonical: bool = False
    is_alias: bool = False
    question_type: str = ""
    mastery_band: str = ""
    family_tags: list[str] = Field(default_factory=list)


class CoverageWarning(BaseModel):
    warning_id: str
    concept_id: str
    concept_label: str
    warning_type: Literal[
        "missing_visible_canonical_entry",
        "only_hidden_correct_entry_exists",
        "only_alias_entry_exists",
        "definition_generation_failed",
    ]
    has_hidden_correct_variants: bool = False
    candidate_ids: list[str] = Field(default_factory=list)
    message: str
