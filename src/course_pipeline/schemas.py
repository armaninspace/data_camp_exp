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
