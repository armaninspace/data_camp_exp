from __future__ import annotations

import json
import re
from pathlib import Path

from course_pipeline.bundle_schemas import (
    BundleValidationReport,
    CountMismatchRecord,
    CourseBundleSummary,
    ScopeDriftRecord,
    SuspiciousAnchorRecord,
)
from course_pipeline.questions.ledger.models import AnchorSummary, LedgerRow


GENERIC_ANCHOR_LABELS = {
    "introduction",
    "overview",
    "overview segment 1",
    "overview segment 2",
    "advanced methods",
    "methods",
    "data",
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def suspicious_anchor_records(course_id: str, anchor_summaries: list[AnchorSummary]) -> list[SuspiciousAnchorRecord]:
    records: list[SuspiciousAnchorRecord] = []
    for summary in anchor_summaries:
        label = summary.anchor_label.strip().lower()
        if "www-" in summary.anchor_id or label.startswith("www.") or ".com" in label or "http" in label:
            records.append(
                SuspiciousAnchorRecord(
                    course_id=course_id,
                    anchor_id=summary.anchor_id,
                    anchor_label=summary.anchor_label,
                    reason="domain_or_url_like_anchor",
                    severity="fail",
                )
            )
        elif re.match(r"overview[- ]segment[- ]\d+", label):
            records.append(
                SuspiciousAnchorRecord(
                    course_id=course_id,
                    anchor_id=summary.anchor_id,
                    anchor_label=summary.anchor_label,
                    reason="mechanically_inferred_overview_segment",
                )
            )
        elif label in GENERIC_ANCHOR_LABELS:
            records.append(
                SuspiciousAnchorRecord(
                    course_id=course_id,
                    anchor_id=summary.anchor_id,
                    anchor_label=summary.anchor_label,
                    reason="generic_or_non_pedagogical_anchor",
                )
            )
    return records


def validate_course_counts(
    *,
    course_id: str,
    ledger_rows: list[LedgerRow],
    visible_rows: list[LedgerRow],
    cache_rows: list[LedgerRow],
    alias_rows: list[LedgerRow],
    hidden_correct_count: int,
) -> list[CountMismatchRecord]:
    mismatches: list[CountMismatchRecord] = []
    visible_from_ledger = sum(1 for row in ledger_rows if row.delivery_class == "curated_visible")
    cache_from_ledger = sum(1 for row in ledger_rows if row.delivery_class == "cache_servable")
    alias_from_ledger = sum(1 for row in ledger_rows if row.delivery_class == "alias_only")
    hidden_from_ledger = sum(1 for row in ledger_rows if row.delivery_class == "analysis_only")

    expected_vs_actual = [
        ("visible_curated", visible_from_ledger, len(visible_rows)),
        ("cache_servable", cache_from_ledger, len(cache_rows)),
        ("aliases", alias_from_ledger, len(alias_rows)),
        ("hidden_correct", hidden_from_ledger, hidden_correct_count),
    ]
    for metric, expected, actual in expected_vs_actual:
        if expected != actual:
            mismatches.append(
                CountMismatchRecord(
                    course_id=course_id,
                    metric=metric,
                    expected=expected,
                    actual=actual,
                    reason="stage_artifact_count_mismatch",
                )
            )
    return mismatches


def build_validation_report(
    *,
    run_id: str,
    strict: bool,
    declared_course_scope: list[str],
    required_files: dict[str, bool],
    blocking_required_files: list[str],
    course_summaries: list[CourseBundleSummary],
    scope_drift: list[ScopeDriftRecord],
    suspicious_anchors: list[SuspiciousAnchorRecord],
    count_mismatches: list[CountMismatchRecord],
    coverage_failures: list[str],
    coverage_warnings: list[str],
    extra_errors: list[str] | None = None,
) -> BundleValidationReport:
    missing_files = [name for name, exists in required_files.items() if not exists]
    blocking_missing_files = [name for name in blocking_required_files if not required_files.get(name, False)]
    errors = [*blocking_missing_files, *(extra_errors or [])]
    if scope_drift:
        errors.append("scope_drift_detected")
    if strict and coverage_failures:
        errors.extend(coverage_failures)
    if strict and len(suspicious_anchors) >= 3:
        errors.append("strict_mode_suspicious_anchor_threshold_exceeded")
    if count_mismatches:
        errors.append("count_mismatches_detected")
    status = "failed" if errors else "passed"
    return BundleValidationReport(
        run_id=run_id,
        strict=strict,
        declared_course_scope=declared_course_scope,
        actual_rendered_course_scope=[summary.course_id for summary in course_summaries],
        required_files=required_files,
        missing_files=missing_files,
        blocking_missing_files=blocking_missing_files,
        scope_drift=scope_drift,
        suspicious_anchors=suspicious_anchors,
        count_mismatches=count_mismatches,
        coverage_failures=coverage_failures,
        coverage_warnings=coverage_warnings,
        course_summaries=course_summaries,
        status=status,
        errors=errors,
    )
