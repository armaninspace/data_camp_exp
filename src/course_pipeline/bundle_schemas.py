from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class SuspiciousAnchorRecord(BaseModel):
    course_id: str
    anchor_id: str
    anchor_label: str
    reason: str
    severity: Literal["info", "warn", "fail"] = "warn"


class CountMismatchRecord(BaseModel):
    course_id: str
    metric: str
    expected: int
    actual: int
    reason: str


class ScopeDriftRecord(BaseModel):
    artifact: str
    expected_course_scope: list[str] = Field(default_factory=list)
    actual_course_scope: list[str] = Field(default_factory=list)
    reason: str


class CourseBundleSummary(BaseModel):
    course_id: str
    title: str
    slug: str
    all_questions: int
    visible_curated: int
    cache_servable: int
    aliases: int
    hidden_correct: int
    anchors_non_pass: int
    coverage_states: list[str] = Field(default_factory=list)
    suspicious_anchor_count: int = 0
    markdown_filename: str


class BundleValidationReport(BaseModel):
    run_id: str
    strict: bool
    declared_course_scope: list[str]
    actual_rendered_course_scope: list[str]
    required_files: dict[str, bool]
    missing_files: list[str] = Field(default_factory=list)
    blocking_missing_files: list[str] = Field(default_factory=list)
    scope_drift: list[ScopeDriftRecord] = Field(default_factory=list)
    suspicious_anchors: list[SuspiciousAnchorRecord] = Field(default_factory=list)
    count_mismatches: list[CountMismatchRecord] = Field(default_factory=list)
    coverage_failures: list[str] = Field(default_factory=list)
    coverage_warnings: list[str] = Field(default_factory=list)
    course_summaries: list[CourseBundleSummary] = Field(default_factory=list)
    status: Literal["passed", "failed"]
    errors: list[str] = Field(default_factory=list)


class BundleManifest(BaseModel):
    bundle_name: str
    run_id: str
    strict: bool
    course_ids: list[str]
    output_dir: Path
    files: list[str] = Field(default_factory=list)
