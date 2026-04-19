from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    TopicEdge,
    TopicNode,
)

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


class SemanticExtractionReport(BaseModel):
    course_id: str
    response_shape: str
    normalization_path: Literal[
        "llm",
        "normalized_loose_shape",
        "heuristic_fallback",
        "parse_failure_fallback",
        "empty_output_fallback",
        "bypassed_no_openai_key",
    ]
    fallback_reason: str | None = None
    raw_topic_count: int = 0
    raw_anchor_count: int = 0
    normalized_topic_count: int = 0
    normalized_anchor_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class SemanticGuardReport(BaseModel):
    course_id: str
    document_has_semantic_signal: bool
    topic_count: int
    anchor_count: int
    status: Literal["ok", "warning", "fallback", "failed"]
    warnings: list[str] = Field(default_factory=list)


class SemanticStageResult(BaseModel):
    normalized_document: CanonicalDocument
    semantic_payload: dict
    semantic_extraction_mode: str
    semantic_extraction_report: SemanticExtractionReport
    semantic_guard_report: SemanticGuardReport
    semantic_topic_records: list[TopicRecord] = Field(default_factory=list)
    semantic_anchor_candidates: list[AnchorCandidate] = Field(default_factory=list)
    semantic_alias_groups: list[AliasGroupRecord] = Field(default_factory=list)
    semantic_friction_records: list[FrictionRecord] = Field(default_factory=list)
    sanitized_topic_records: list[TopicRecord] = Field(default_factory=list)
    sanitized_anchor_candidates: list[AnchorCandidate] = Field(default_factory=list)
    sanitized_alias_groups: list[AliasGroupRecord] = Field(default_factory=list)
    sanitized_friction_records: list[FrictionRecord] = Field(default_factory=list)
    semantic_validation_report: SemanticValidationReport
    topics: list[TopicNode] = Field(default_factory=list)
    edges: list[TopicEdge] = Field(default_factory=list)
    pedagogy: list[PedagogicalProfile] = Field(default_factory=list)
    frictions: list[FrictionPoint] = Field(default_factory=list)
