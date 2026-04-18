from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.bundle_schemas import BundleManifest, BundleValidationReport, CourseBundleSummary
from course_pipeline.questions.ledger.models import AnchorSummary, LedgerRow
from course_pipeline.schemas import NormalizedCourse


def render_question_ledger_report(course_summaries: list[CourseBundleSummary]) -> str:
    lines = ["# Question Ledger V6 Report", ""]
    for summary in course_summaries:
        lines.extend(
            [
                f"## Course `{summary.course_id}`",
                "",
                f"- all questions: {summary.all_questions}",
                f"- visible curated: {summary.visible_curated}",
                f"- cache-servable: {summary.cache_servable}",
                f"- aliases: {summary.aliases}",
                f"- anchors with non-pass coverage: {summary.anchors_non_pass}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_top_level_inspection_report(
    *,
    bundle_manifest: BundleManifest,
    validation_report: BundleValidationReport,
    pipeline_variant: str,
) -> str:
    lines = [
        "# Inspection Bundle Report",
        "",
        f"- run id: `{bundle_manifest.run_id}`",
        f"- pipeline variant: `{pipeline_variant}`",
        f"- declared course scope: {json.dumps(bundle_manifest.course_ids)}",
        f"- actual rendered course scope: {json.dumps(validation_report.actual_rendered_course_scope)}",
        f"- validation status: `{validation_report.status}`",
        f"- strict mode: `{str(bundle_manifest.strict).lower()}`",
        "",
        "## Validation Summary",
        "",
        f"- missing required files: {len(validation_report.missing_files)}",
        f"- blocking missing files: {len(validation_report.blocking_missing_files)}",
        f"- scope drift records: {len(validation_report.scope_drift)}",
        f"- count mismatches: {len(validation_report.count_mismatches)}",
        f"- suspicious anchors: {len(validation_report.suspicious_anchors)}",
        f"- coverage failures: {len(validation_report.coverage_failures)}",
        f"- coverage warnings: {len(validation_report.coverage_warnings)}",
        "",
        "## Scope Drift",
        "",
    ]
    if validation_report.scope_drift:
        for record in validation_report.scope_drift:
            lines.append(
                f"- artifact `{record.artifact}` expected {json.dumps(record.expected_course_scope)}"
                f" but rendered {json.dumps(record.actual_course_scope)}: {record.reason}"
            )
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Suspicious Anchors",
        "",
    ])
    if validation_report.suspicious_anchors:
        for item in validation_report.suspicious_anchors:
            lines.append(
                f"- course `{item.course_id}` anchor `{item.anchor_label}` (`{item.anchor_id}`): {item.reason}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Coverage Summary", ""])
    if validation_report.coverage_failures:
        for item in validation_report.coverage_failures:
            lines.append(f"- FAIL: {item}")
    elif validation_report.coverage_warnings:
        for item in validation_report.coverage_warnings:
            lines.append(f"- WARN: {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Per-Course Stats", ""])
    for summary in validation_report.course_summaries:
        lines.extend(_render_course_summary(summary))
    if validation_report.errors:
        lines.extend(["", "## Errors", ""])
        for error in validation_report.errors:
            lines.append(f"- {error}")
    return "\n".join(lines).rstrip() + "\n"


def _render_course_summary(summary: CourseBundleSummary) -> list[str]:
    return [
        f"### Course `{summary.course_id}`",
        f"- title: {summary.title}",
        f"- all questions: {summary.all_questions}",
        f"- visible curated: {summary.visible_curated}",
        f"- cache_servable: {summary.cache_servable}",
        f"- aliases: {summary.aliases}",
        f"- hidden correct: {summary.hidden_correct}",
        f"- anchors with non-pass coverage: {summary.anchors_non_pass}",
        f"- suspicious anchors: {summary.suspicious_anchor_count}",
        f"- markdown: `{summary.markdown_filename}`",
        "",
    ]


def render_course_page(
    *,
    course: NormalizedCourse,
    visible_rows: list[LedgerRow],
    hidden_correct_rows: list[dict],
    anchor_summaries: list[AnchorSummary],
    answers_by_candidate_id: dict[str, str],
    cache_count: int,
    hard_reject_count: int,
) -> str:
    lines = [f"# {course.title} (`{course.course_id}`)", "", "## Visible Curated Q/A Pairs", ""]
    if visible_rows:
        for row in visible_rows:
            answer = answers_by_candidate_id.get(row.question_id, row.answer_text or "")
            lines.append(f"Q: {row.question_text}  ")
            lines.append(f"A: {answer}".rstrip())
            lines.append("")
    else:
        lines.append("- none")
        lines.append("")

    lines.extend(["## Hidden But Correct", ""])
    if hidden_correct_rows:
        for item in hidden_correct_rows:
            lines.append(f"- {item.get('question', '').strip()}")
            lines.append(
                "  delivery_class: "
                f"{item.get('delivery_class', 'unknown')}; reasons: "
                f"{json.dumps(item.get('non_visible_reasons', []), ensure_ascii=False)}"
            )
            lines.append(
                "  anchor="
                f"{str(item.get('is_foundational_anchor', False)).lower()} "
                "required_entry="
                f"{str(item.get('is_required_entry_candidate', False)).lower()}"
            )
    else:
        lines.append("- none")
    lines.append("")

    lines.extend(["## Coverage Warnings", ""])
    warnings = [summary for summary in anchor_summaries if summary.coverage_status in {"WARN", "FAIL"}]
    if warnings:
        for summary in warnings:
            lines.append(
                f"- `{summary.coverage_status}` for `{summary.anchor_label}`"
                f" (`{summary.anchor_type}`): visible={summary.visible_count},"
                f" required_entry_visible={str(summary.required_entry_visible).lower()}"
            )
    else:
        lines.append("- none")
    lines.append("")

    lines.extend(["## Policy Summary", ""])
    lines.append(f"- validated-correct count: {len(visible_rows) + len(hidden_correct_rows) + cache_count}")
    lines.append(f"- visible curated count: {len(visible_rows)}")
    lines.append(f"- hidden correct count: {len(hidden_correct_rows)}")
    lines.append(f"- hard reject count: {hard_reject_count}")
    lines.append(f"- cache entries: {cache_count}")
    lines.append("")

    lines.extend(["## Scraped Course Description", "", "### Summary", "", course.summary or "", "", "### Overview", ""])
    lines.append(course.overview or "")
    lines.extend(["", "### Syllabus", ""])
    if course.chapters:
        for section in course.chapters:
            lines.append(f"{section.chapter_index}. {section.title}  ")
            lines.append((section.summary or "").strip())
            lines.append("")
    else:
        lines.append("- none")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_bundle_metadata(
    *,
    output_dir: Path,
    bundle_manifest: BundleManifest,
    validation_report: BundleValidationReport,
    inspection_report: str,
    question_ledger_report: str,
    scoped_run_manifest: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(scoped_run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "validation_report.json").write_text(
        validation_report.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "inspection_report.md").write_text(inspection_report, encoding="utf-8")
    (output_dir / "question_ledger_v6_report.md").write_text(question_ledger_report, encoding="utf-8")
