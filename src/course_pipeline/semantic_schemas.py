from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    field: str
    excerpt: str


class TopicRecord(BaseModel):
    course_id: str
    topic_id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    topic_type: Literal[
        "concept",
        "procedure",
        "tool",
        "metric",
        "diagnostic",
        "comparison_axis",
        "failure_mode",
        "decision_point",
        "prerequisite",
    ]
    description: str
    source_fields: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float


class AnchorCandidate(BaseModel):
    course_id: str
    anchor_id: str
    label: str
    normalized_label: str
    anchor_type: Literal[
        "foundational_vocabulary",
        "procedure",
        "tool",
        "metric",
        "diagnostic",
        "comparison_axis",
        "failure_mode",
        "decision_point",
        "contextual_topic",
    ]
    foundational_candidate: bool
    learner_facing: bool
    requires_entry_question: bool
    rationale: str
    source_fields: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float


class AliasGroupRecord(BaseModel):
    course_id: str
    canonical_label: str
    aliases: list[str] = Field(default_factory=list)
    rationale: str
    source_fields: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float


class FrictionRecord(BaseModel):
    course_id: str
    anchor_id: str
    friction_type: Literal[
        "confusion",
        "choice",
        "failure_mode",
        "prerequisite_gap",
        "transfer_gap",
        "interpretation_gap",
    ]
    description: str
    rationale: str
    source_fields: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float


class SemanticDecisionRecord(BaseModel):
    course_id: str
    entity_type: Literal["topic", "anchor", "alias_group", "friction"]
    entity_id: str
    action: Literal["keep", "drop", "merge", "rewrite"]
    reason: str
    provenance_note: str | None = None
    source_fields: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    confidence: float | None = None
    merged_into_id: str | None = None


class SemanticValidationReport(BaseModel):
    course_id: str
    topic_count: int
    anchor_count: int
    alias_group_count: int
    friction_count: int
    kept_count: int
    dropped_count: int
    merged_count: int
    rewritten_count: int
    suspicious_anchor_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    decisions: list[SemanticDecisionRecord] = Field(default_factory=list)
