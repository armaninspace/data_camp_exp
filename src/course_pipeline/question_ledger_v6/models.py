from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


QuestionFamily = Literal["entry", "bridge", "procedural", "friction", "diagnostic", "transfer"]
QuestionType = Literal["definition", "purpose", "comparison", "procedure", "misconception", "diagnostic", "application"]
DeliveryClass = Literal["curated_visible", "cache_servable", "alias_only", "analysis_only", "hard_reject"]


class LedgerScores(BaseModel):
    groundedness: float
    correctness: float
    query_likelihood: float
    pedagogical_value: float
    serviceability: float
    distinctiveness: float


class LedgerRow(BaseModel):
    question_id: str
    question_text: str
    answer_text: str = ""
    anchor_id: str
    anchor_label: str
    anchor_type: str = ""
    question_family: QuestionFamily
    question_type: QuestionType
    mastery_band: Literal["novice", "developing", "proficient"]
    canonical: bool
    alias: bool
    canonical_target: str | None = None
    required_entry: bool
    validated_correct: bool
    grounded: bool
    serviceable: bool
    delivery_class: DeliveryClass
    visible: bool
    non_visible_reasons: list[str] = Field(default_factory=list)
    reject_reasons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    scores: LedgerScores
    source_refs: list[str] = Field(default_factory=list)


class AnchorSummary(BaseModel):
    anchor_id: str
    anchor_label: str
    anchor_type: str
    coverage_status: Literal["PASS", "WARN", "FAIL"]
    generated_count: int
    validated_correct_count: int
    visible_count: int
    cache_servable_count: int
    analysis_only_count: int
    hard_reject_count: int
    required_entry_exists: bool
    required_entry_visible: bool
