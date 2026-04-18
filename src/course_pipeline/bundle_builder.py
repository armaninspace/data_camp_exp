from __future__ import annotations

import json
import shutil
from pathlib import Path

from course_pipeline.bundle_render import (
    render_course_page,
    render_question_ledger_report,
    render_top_level_inspection_report,
    write_bundle_metadata,
)
from course_pipeline.bundle_schemas import BundleManifest, CourseBundleSummary, ScopeDriftRecord
from course_pipeline.bundle_validate import (
    build_validation_report,
    read_jsonl,
    suspicious_anchor_records,
    validate_course_counts,
)
from course_pipeline.questions.ledger.models import AnchorSummary, LedgerRow
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.utils import ensure_dir, slugify, write_jsonl


class BundleBuildError(RuntimeError):
    pass


def build_inspection_bundle(
    *,
    run_id: str,
    output_dir: Path,
    output_root: Path,
    course_ids: list[str] | None = None,
    strict: bool = False,
    dry_run: bool = False,
) -> Path:
    run_root = output_root / run_id
    if not run_root.exists():
        raise BundleBuildError(f"run directory does not exist: {run_root}")

    core_required_paths = {
        "run_manifest.json": run_root / "run_manifest.json",
        "question_ledger_v6_report.md": run_root / "question_ledger_v6_report.md",
        "all_questions.jsonl": run_root / "all_questions.jsonl",
        "visible_curated.jsonl": run_root / "visible_curated.jsonl",
        "cache_servable.jsonl": run_root / "cache_servable.jsonl",
        "aliases.jsonl": run_root / "aliases.jsonl",
        "anchors_summary.json": run_root / "anchors_summary.json",
        "courses.jsonl": run_root / "courses.jsonl",
    }
    optional_paths = {
        "review_bundle": run_root / "review_bundle",
        "review_answers.jsonl": run_root / "review_answers.jsonl",
        "llm_metering.jsonl": run_root / "llm_metering.jsonl",
    }
    required_files = {
        **{name: path.exists() for name, path in core_required_paths.items()},
        **{name: path.exists() for name, path in optional_paths.items()},
    }
    blocking_required_files = list(core_required_paths)
    if (
        not required_files["run_manifest.json"]
        or not required_files["question_ledger_v6_report.md"]
        or not required_files["all_questions.jsonl"]
    ):
        report = build_validation_report(
            run_id=run_id,
            strict=strict,
            declared_course_scope=course_ids or [],
            required_files=required_files,
            blocking_required_files=blocking_required_files,
            course_summaries=[],
            scope_drift=[],
            suspicious_anchors=[],
            count_mismatches=[],
            coverage_failures=[],
            coverage_warnings=[],
            extra_errors=["required_core_artifacts_missing"],
        )
        raise BundleBuildError(report.model_dump_json(indent=2))

    run_manifest = json.loads((run_root / "run_manifest.json").read_text(encoding="utf-8"))
    if run_manifest.get("run_id") != run_id:
        raise BundleBuildError(f"run manifest run_id mismatch: expected {run_id}, found {run_manifest.get('run_id')}")

    courses = [
        NormalizedCourse.model_validate_json(line)
        for line in (run_root / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    course_by_id = {course.course_id: course for course in courses}
    declared_scope = course_ids or list(run_manifest.get("selected_course_ids") or course_by_id)
    for course_id in declared_scope:
        if course_id not in course_by_id:
            raise BundleBuildError(f"requested course_id missing from run outputs: {course_id}")

    all_rows_raw = read_jsonl(run_root / "all_questions.jsonl")
    visible_rows_raw = read_jsonl(run_root / "visible_curated.jsonl")
    cache_rows_raw = read_jsonl(run_root / "cache_servable.jsonl")
    alias_rows_raw = read_jsonl(run_root / "aliases.jsonl")

    output_dir = output_dir.resolve()
    if output_dir.exists() and not dry_run:
        shutil.rmtree(output_dir)
    if not dry_run:
        ensure_dir(output_dir / "courses")
        ensure_dir(output_dir / "final_deliverables")

    count_mismatches = []
    scope_drift: list[ScopeDriftRecord] = []
    suspicious = []
    coverage_failures: list[str] = []
    coverage_warnings: list[str] = []
    course_summaries: list[CourseBundleSummary] = []

    scoped_all: list[dict] = []
    scoped_visible: list[dict] = []
    scoped_cache: list[dict] = []
    scoped_aliases: list[dict] = []
    scoped_anchors: list[dict] = []

    policy_artifacts_dir = run_root / "policy" / "course_artifacts"
    ledger_artifacts_dir = run_root / "ledger" / "course_artifacts"
    answers_by_course_and_candidate: dict[str, dict[str, str]] = {}
    if required_files["review_answers.jsonl"]:
        for row in read_jsonl(optional_paths["review_answers.jsonl"]):
            course_id = str(row.get("course_id"))
            candidate_id = str(row.get("candidate_id"))
            answers_by_course_and_candidate.setdefault(course_id, {})[candidate_id] = str(row.get("answer_markdown", ""))

    for course_id in declared_scope:
        course = course_by_id[course_id]
        course_all = [
            LedgerRow.model_validate(row)
            for row in all_rows_raw
            if str(row.get("course_id")) == course_id
        ]
        course_visible = [
            LedgerRow.model_validate(row)
            for row in visible_rows_raw
            if str(row.get("course_id")) == course_id
        ]
        course_cache = [
            LedgerRow.model_validate(row)
            for row in cache_rows_raw
            if str(row.get("course_id")) == course_id
        ]
        course_aliases = [
            LedgerRow.model_validate(row)
            for row in alias_rows_raw
            if str(row.get("course_id")) == course_id
        ]
        anchor_path = ledger_artifacts_dir / course_id / "anchors_summary.json"
        if not anchor_path.exists():
            raise BundleBuildError(f"missing per-course anchors summary for {course_id}: {anchor_path}")
        course_anchors = [
            AnchorSummary.model_validate(item)
            for item in json.loads(anchor_path.read_text(encoding="utf-8"))
        ]
        hidden_correct_rows = read_jsonl(policy_artifacts_dir / course_id / "hidden_correct.jsonl")
        hidden_correct_count = len(hidden_correct_rows)

        count_mismatches.extend(
            validate_course_counts(
                course_id=course_id,
                ledger_rows=course_all,
                visible_rows=course_visible,
                cache_rows=course_cache,
                alias_rows=course_aliases,
                hidden_correct_count=hidden_correct_count,
            )
        )
        course_suspicious = suspicious_anchor_records(course_id, course_anchors)
        suspicious.extend(course_suspicious)
        course_coverage_failures = [
            f"{course_id}:{summary.anchor_label}"
            for summary in course_anchors
            if summary.coverage_status == "FAIL"
        ]
        course_coverage_warnings = [
            f"{course_id}:{summary.anchor_label}"
            for summary in course_anchors
            if summary.coverage_status == "WARN"
        ]
        coverage_failures.extend(course_coverage_failures)
        coverage_warnings.extend(course_coverage_warnings)

        markdown_filename = f"{course_id}_{slugify(course.title)}.md"
        if not dry_run:
            course_page = render_course_page(
                course=course,
                visible_rows=course_visible,
                hidden_correct_rows=hidden_correct_rows,
                anchor_summaries=course_anchors,
                answers_by_candidate_id=answers_by_course_and_candidate.get(course_id, {}),
                cache_count=len(course_cache),
                hard_reject_count=sum(1 for row in course_all if row.delivery_class == "hard_reject"),
            )
            (output_dir / "courses" / markdown_filename).write_text(course_page, encoding="utf-8")

        course_summaries.append(
            CourseBundleSummary(
                course_id=course_id,
                title=course.title,
                slug=slugify(course.title),
                all_questions=len(course_all),
                visible_curated=len(course_visible),
                cache_servable=len(course_cache),
                aliases=len(course_aliases),
                hidden_correct=hidden_correct_count,
                anchors_non_pass=sum(1 for summary in course_anchors if summary.coverage_status != "PASS"),
                coverage_states=sorted({summary.coverage_status for summary in course_anchors}),
                suspicious_anchor_count=len(course_suspicious),
                markdown_filename=f"courses/{markdown_filename}",
            )
        )

        scoped_all.extend(row.model_dump(mode="json") | {"course_id": course_id} for row in course_all)
        scoped_visible.extend(row.model_dump(mode="json") | {"course_id": course_id} for row in course_visible)
        scoped_cache.extend(row.model_dump(mode="json") | {"course_id": course_id} for row in course_cache)
        scoped_aliases.extend(row.model_dump(mode="json") | {"course_id": course_id} for row in course_aliases)
        scoped_anchors.extend(row.model_dump(mode="json") | {"course_id": course_id} for row in course_anchors)

    rendered_scope = [summary.course_id for summary in course_summaries]
    if sorted(rendered_scope) != sorted(declared_scope):
        scope_drift.append(
            ScopeDriftRecord(
                artifact="bundle_render",
                expected_course_scope=declared_scope,
                actual_course_scope=rendered_scope,
                reason="rendered_course_scope_does_not_match_declared_scope",
            )
        )
    if sorted({row["course_id"] for row in scoped_all}) != sorted(set(declared_scope)):
        scope_drift.append(
            ScopeDriftRecord(
                artifact="final_deliverables/all_questions.jsonl",
                expected_course_scope=declared_scope,
                actual_course_scope=sorted({row["course_id"] for row in scoped_all}),
                reason="scoped_all_questions_do_not_match_declared_scope",
            )
        )

    validation = build_validation_report(
        run_id=run_id,
        strict=strict,
        declared_course_scope=declared_scope,
        required_files=required_files,
        blocking_required_files=blocking_required_files,
        course_summaries=course_summaries,
        scope_drift=scope_drift,
        suspicious_anchors=suspicious,
        count_mismatches=count_mismatches,
        coverage_failures=coverage_failures,
        coverage_warnings=coverage_warnings,
    )
    if validation.status == "failed":
        raise BundleBuildError(validation.model_dump_json(indent=2))

    if dry_run:
        return output_dir

    write_jsonl(output_dir / "final_deliverables" / "all_questions.jsonl", scoped_all)
    write_jsonl(output_dir / "final_deliverables" / "visible_curated.jsonl", scoped_visible)
    write_jsonl(output_dir / "final_deliverables" / "cache_servable.jsonl", scoped_cache)
    write_jsonl(output_dir / "final_deliverables" / "aliases.jsonl", scoped_aliases)
    (output_dir / "final_deliverables" / "anchors_summary.json").write_text(
        json.dumps(scoped_anchors, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if required_files["review_answers.jsonl"]:
        scoped_review_answers = [
            row for row in read_jsonl(optional_paths["review_answers.jsonl"]) if str(row.get("course_id")) in declared_scope
        ]
        write_jsonl(output_dir / "review_answers.jsonl", scoped_review_answers)
    if required_files["llm_metering.jsonl"]:
        shutil.copy2(optional_paths["llm_metering.jsonl"], output_dir / "llm_metering.jsonl")

    bundle_manifest = BundleManifest(
        bundle_name=output_dir.name,
        run_id=run_id,
        strict=strict,
        course_ids=declared_scope,
        output_dir=output_dir,
        files=[],
    )
    inspection_report = render_top_level_inspection_report(
        bundle_manifest=bundle_manifest,
        validation_report=validation,
        pipeline_variant="prefect_llm_assisted_question_pipeline",
    )
    question_ledger_report = render_question_ledger_report(course_summaries)
    scoped_run_manifest = {
        **run_manifest,
        "bundle_name": output_dir.name,
        "selected_course_ids": declared_scope,
    }
    write_bundle_metadata(
        output_dir=output_dir,
        bundle_manifest=bundle_manifest,
        validation_report=validation,
        inspection_report=inspection_report,
        question_ledger_report=question_ledger_report,
        scoped_run_manifest=scoped_run_manifest,
    )
    bundle_files = [
        "run_manifest.json",
        "validation_report.json",
        "inspection_report.md",
        "question_ledger_v6_report.md",
        "final_deliverables/all_questions.jsonl",
        "final_deliverables/visible_curated.jsonl",
        "final_deliverables/cache_servable.jsonl",
        "final_deliverables/aliases.jsonl",
        "final_deliverables/anchors_summary.json",
        *[summary.markdown_filename for summary in course_summaries],
    ]
    if required_files["review_answers.jsonl"]:
        bundle_files.append("review_answers.jsonl")
    if required_files["llm_metering.jsonl"]:
        bundle_files.append("llm_metering.jsonl")
    (output_dir / "README.md").write_text(
        (
            "# Inspection Bundle Builder\n\n"
            "Built from a single run with strict scoped validation.\n\n"
            f"- run id: `{run_id}`\n"
            f"- course scope: {json.dumps(declared_scope)}\n"
            f"- strict: `{str(strict).lower()}`\n"
            f"- dry run: `{str(dry_run).lower()}`\n"
        ),
        encoding="utf-8",
    )
    manifest_payload = {
        "bundle_name": output_dir.name,
        "run_id": run_id,
        "strict": strict,
        "course_ids": declared_scope,
        "files": bundle_files,
    }
    (output_dir / "bundle_manifest.json").write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_dir
