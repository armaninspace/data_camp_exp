from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChapterOut(BaseModel):
    chapter_index: int
    title: str
    summary: str | None = None
    source: Literal["syllabus", "overview_inferred"]
    confidence: float


class NormalizedCourse(BaseModel):
    course_id: str
    source_url: str
    final_url: str | None = None
    provider: str
    title: str
    summary: str | None = None
    overview: str | None = None
    subjects: list[str] = Field(default_factory=list)
    level: str | None = None
    duration_hours: float | None = None
    pricing: str | None = None
    language: str | None = None
    chapters: list[ChapterOut] = Field(default_factory=list)
    raw_yaml_path: str
    fetched_at: datetime | None = None
    ratings: dict = Field(default_factory=dict)
    details: dict = Field(default_factory=dict)


class CitationOut(BaseModel):
    field: str
    evidence: str


class LearningOutcomeOut(BaseModel):
    id: str
    claim: str
    knowledge_type: Literal["factual", "conceptual", "procedural", "metacognitive"]
    process_level: Literal["remember", "understand", "apply", "analyze", "evaluate", "create"]
    dok_level: Literal[1, 2, 3, 4]
    solo_level: Literal["unistructural", "multistructural", "relational", "extended_abstract"]
    confidence: float
    reasoning: str
    citations: list[CitationOut] = Field(default_factory=list)


class CoverageNotesOut(BaseModel):
    syllabus_present: bool
    evidence_strength: Literal["strong", "moderate", "weak"]
    gaps_or_ambiguities: list[str] = Field(default_factory=list)


class LearningOutcomeExtractionOut(BaseModel):
    course_id: str
    course_title: str
    learning_outcomes: list[LearningOutcomeOut] = Field(default_factory=list)
    coverage_notes: CoverageNotesOut


class SourceEvidenceOut(BaseModel):
    field: str
    excerpt: str


class GenerationBasisOut(BaseModel):
    source_kind: Literal["topic", "friction_candidate", "contrast", "confusion", "prerequisite"]
    source_id: str
    rationale: str


class TopicOut(BaseModel):
    topic_id: str
    course_id: str
    chapter_id: str
    chapter_title: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    topic_type: Literal["concept", "procedure", "tool", "metric_test", "contrast", "confusion", "prerequisite", "advanced"]
    prerequisites: list[str] = Field(default_factory=list)
    contrasts: list[str] = Field(default_factory=list)
    confusions: list[str] = Field(default_factory=list)
    evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    importance: float = 0.0


class LearnerFrictionCandidateOut(BaseModel):
    candidate_id: str
    course_id: str
    chapter_id: str
    chapter_title: str
    text: str
    candidate_type: Literal["term", "acronym", "method", "test", "process", "contrast", "overloaded_term"]
    evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    confidence: float = 0.0


class CandidateQuestionOut(BaseModel):
    question_id: str
    course_id: str
    question_text: str
    chapter_id: str
    chapter_title: str
    topic_id: str
    topic_label: str
    mastery_band: Literal["novice", "developing", "proficient"]
    question_type: Literal[
        "definition",
        "purpose",
        "intuition",
        "how_to",
        "when_to_use",
        "common_error",
        "comparison",
        "misconception",
        "application",
        "limitation",
        "interpretation",
    ]
    source_evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    generation_basis: GenerationBasisOut
    score: float


class ClaimQuestionGroupOut(BaseModel):
    question_group_id: str
    course_id: str
    claim_id: str
    intent_slug: str
    canonical_question: str
    pedagogical_move: str
    canonical_answer_id: str
    confidence: float
    citations: list[CitationOut] = Field(default_factory=list)
    source_run_id: str
    prompt_version: str
    generation_stage: str = "atomized"
    validator_status: str = "pending"
    coverage_status: str = "accounted_for"


class QuestionGroupVariationOut(BaseModel):
    variation_id: str
    question_group_id: str
    text: str
    normalized_text: str
    equivalence_notes: str
    source: Literal["generated", "canonical", "promoted"]
    candidate_source: str = "variation_generation"
    validation_decision: str = "pending"
    validation_reason: str | None = None
    accepted_for_runtime: bool = False


class CanonicalAnswerOut(BaseModel):
    canonical_answer_id: str
    question_group_id: str
    answer_markdown: str
    answer_style: str
    answer_version: int
    reviewer_state: Literal["unreviewed", "approved", "rejected"]
    citations: list[CitationOut] = Field(default_factory=list)
    source_run_id: str
    prompt_version: str
    answer_fit_status: str = "pending"
    grounding_status: str = "pending"
    grounding_reason: str | None = None
    answer_scope_notes: str | None = None


class QuestionCacheValidationLogOut(BaseModel):
    entity_type: str
    entity_id: str
    validator_type: str
    decision: str
    reason: str | None = None
    model_version: str | None = None


class ClaimCoverageAuditOut(BaseModel):
    course_id: str
    claim_id: str
    produced_question_groups: bool
    question_group_count: int = 0
    no_groups_reason: str | None = None
    source_run_id: str


class QuestionCacheGenerationOut(BaseModel):
    course_id: str
    course_title: str
    claim_id: str
    claim_text: str
    question_groups: list[ClaimQuestionGroupOut] = Field(default_factory=list)
    variations: list[QuestionGroupVariationOut] = Field(default_factory=list)
    canonical_answers: list[CanonicalAnswerOut] = Field(default_factory=list)


class QuestionCacheMatchResult(BaseModel):
    course_id: str | None = None
    claim_id: str | None = None
    question_group_id: str | None = None
    variation_id: str | None = None
    canonical_answer_id: str | None = None
    incoming_question: str
    normalized_question: str
    match_method: Literal["exact_variation", "exact_canonical", "lexical", "fallback"]
    match_score: float
    resolved_as_hit: bool
    answer_markdown: str | None = None
    fallback_reason: str | None = None
    candidate_for_cache_warming: bool = False
