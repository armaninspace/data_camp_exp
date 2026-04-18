from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class GeneratedAnswerRecord(BaseModel):
    course_id: str
    candidate_id: str
    question_text: str
    answer_markdown: str
    source_refs: list[str] = Field(default_factory=list)
    generation_rationale: str
    confidence: float
    generated_by_llm: bool = True


class AnswerValidationRecord(BaseModel):
    course_id: str
    candidate_id: str
    validation_status: Literal["accepted", "rejected"]
    answer_fit_status: Literal["accepted", "rejected"]
    grounding_status: Literal["accepted", "rejected"]
    reasons: list[str] = Field(default_factory=list)
    confidence: float


class ReviewAnswerRecord(BaseModel):
    course_id: str
    candidate_id: str
    question_text: str
    answer_markdown: str
    validation_status: Literal["accepted", "rejected"]
