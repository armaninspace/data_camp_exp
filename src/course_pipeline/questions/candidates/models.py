from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Section(BaseModel):
    section_index: int
    title: str
    summary: str
    source: Literal["explicit", "inferred"]


class CanonicalDocument(BaseModel):
    doc_id: str
    title: str
    summary: str = ""
    overview: str = ""
    level: str | None = None
    tooling: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)


class TopicNode(BaseModel):
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
    source_section_ids: list[int] = Field(default_factory=list)
    confidence: float


class TopicEdge(BaseModel):
    source_id: str
    target_id: str
    relation: Literal[
        "prerequisite_of",
        "part_of",
        "contrasts_with",
        "confused_with",
        "evaluated_by",
        "uses",
        "decision_depends_on",
        "failure_revealed_by",
    ]
    rationale: str
    confidence: float


class PedagogicalProfile(BaseModel):
    topic_id: str
    cognitive_modes: list[str] = Field(default_factory=list)
    abstraction_level: Literal["low", "medium", "high"]
    notation_load: Literal["low", "medium", "high"]
    procedure_load: Literal["low", "medium", "high"]
    likely_misconceptions: list[str] = Field(default_factory=list)
    likely_sticking_points: list[str] = Field(default_factory=list)
    evidence_of_mastery: list[str] = Field(default_factory=list)


class FrictionPoint(BaseModel):
    friction_id: str
    topic_id: str
    friction_type: Literal[
        "confusion",
        "choice",
        "failure_mode",
        "prerequisite_gap",
        "transfer_gap",
        "interpretation_gap",
    ]
    prompting_signal: str
    learner_symptom: str
    why_it_matters: str
    severity: float
    confidence: float


class QuestionCandidate(BaseModel):
    candidate_id: str
    topic_id: str
    slot: Literal[
        "novice_orientation",
        "novice_definition",
        "developing_procedural",
        "developing_comparison",
        "developing_misconception",
        "proficient_diagnostic",
        "proficient_transfer",
    ]
    mastery_band: Literal["novice", "developing", "proficient"]
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
    question_text: str
    rationale: str
    source_support: list[str] = Field(default_factory=list)
    linked_friction_ids: list[str] = Field(default_factory=list)
    section_ids: list[int] = Field(default_factory=list)
    source_kind: Literal["original", "repaired", "derived"] = "original"
    source_question_id: str | None = None
    llm_stage: Literal["repair", "expand"] | None = None
    provenance_note: str | None = None
    derived_by_llm: bool = False
    llm_grounding_confidence: float | None = None
    llm_repair_confidence: float | None = None
    llm_derivation_confidence: float | None = None


class RejectedCandidate(BaseModel):
    candidate: QuestionCandidate
    reasons: list[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    friction_value: float
    specificity: float
    answer_richness: float
    mastery_fit: float
    novelty: float
    groundedness: float
    semantic_confidence: float = 0.0
    llm_repair_confidence: float = 0.0
    llm_derivation_confidence: float = 0.0
    total: float


class ScoredCandidate(BaseModel):
    candidate: QuestionCandidate
    score: CandidateScore
    rejection_flags: list[str] = Field(default_factory=list)


class DuplicateCluster(BaseModel):
    kept_candidate_id: str
    duplicate_candidate_ids: list[str] = Field(default_factory=list)
    rationale: str


class SelectionSummary(BaseModel):
    target_n: int
    selected_count: int
    candidate_count: int
    rejected_count: int
    duplicate_cluster_count: int
    quotas_requested: dict = Field(default_factory=dict)
    quotas_met: dict = Field(default_factory=dict)
    type_distribution: dict = Field(default_factory=dict)
    mastery_distribution: dict = Field(default_factory=dict)
    friction_linked_selection_rate: float = 0.0


class ReviewAnswer(BaseModel):
    candidate_id: str
    answer_markdown: str
