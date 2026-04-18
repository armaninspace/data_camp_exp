from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PolicyScores(BaseModel):
    correctness: float
    groundedness: float
    contradiction_risk: float
    coherence: float
    query_likelihood: float
    pedagogical_value: float
    answer_richness: float
    mastery_fit: float
    distinctiveness: float
    serviceability: float
    context_dependence: float
    answer_stability: float


class FamilyTagSet(BaseModel):
    tags: list[Literal["entry", "bridge", "procedural", "friction", "diagnostic", "transfer"]] = Field(default_factory=list)
    rationale_by_tag: dict[str, str] = Field(default_factory=dict)


class CanonicalGroup(BaseModel):
    group_id: str
    canonical_candidate_id: str
    member_candidate_ids: list[str]
    alias_candidate_ids: list[str] = Field(default_factory=list)
    rationale: str


class PolicyDecision(BaseModel):
    candidate_id: str
    canonical_id: str | None = None
    family_tags: list[str] = Field(default_factory=list)
    policy_bucket: Literal["curated_core", "cache_servable", "alias_only", "analysis_only", "hard_reject"]
    servable: bool = False
    scores: PolicyScores
    reason_codes: list[str] = Field(default_factory=list)


class RetentionRecord(BaseModel):
    candidate_id: str
    policy_bucket: str
    store_full_record: bool
    store_answer_text: bool
    store_audit_only: bool


class CacheEntry(BaseModel):
    cache_id: str
    canonical_candidate_id: str
    canonical_question: str
    canonical_answer: str
    alias_questions: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    active: bool = True


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
