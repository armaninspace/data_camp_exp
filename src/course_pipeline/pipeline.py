from __future__ import annotations

import json
from pathlib import Path

import yaml

from course_pipeline.config import Settings
from course_pipeline.normalize import iter_courses
from course_pipeline.questions.candidates import (
    ScoredCandidate,
    build_candidate_review_bundle,
    run_candidate_generation_for_course,
    write_candidate_course_artifacts,
    write_candidate_run_report,
)
from course_pipeline.questions.ledger import (
    AnchorSummary,
    LedgerRow,
    build_ledger_review_bundle,
    build_question_ledger_for_course,
    load_candidate_course_artifacts_for_ledger,
    write_ledger_run_report,
)
from course_pipeline.questions.policy import (
    CacheEntry,
    CandidateRecord,
    CoverageWarning,
    PolicyDecision,
    build_cache_entries,
    build_legacy_policy_review_bundle,
    build_policy_review_bundle,
    load_candidate_course_artifacts,
    run_legacy_policy_stage,
    run_policy_stage,
    write_legacy_policy_report,
    write_policy_report,
)
from course_pipeline.schemas import (
    NormalizedCourse,
)
from course_pipeline.storage import Storage
from course_pipeline.utils import ensure_dir, write_jsonl


def ingest_all(input_dir: Path, storage: Storage, run_id: str) -> tuple[list[NormalizedCourse], list[dict]]:
    courses, errors = iter_courses(input_dir)
    storage.record_source_files(run_id, courses, errors)
    storage.upsert_courses(run_id, courses)
    return courses, errors


def export_standardized(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
) -> dict[str, Path]:
    courses, errors = ingest_all(input_dir, storage, run_id)
    run_dir = ensure_dir(settings.output_root / run_id)
    standardized_dir = ensure_dir(run_dir / "standardized_courses")

    course_rows = []
    chapter_rows = []
    error_rows = list(errors)

    for course in courses:
        course_payload = course.model_dump(mode="json")
        course_rows.append(course_payload)
        standardized_path = standardized_dir / f"{course.course_id}.yaml"
        standardized_path.write_text(
            yaml.safe_dump(course_payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        for chapter in course.chapters:
            chapter_rows.append(
                {
                    "course_id": course.course_id,
                    "course_title": course.title,
                    **chapter.model_dump(mode="json"),
                }
            )

    outputs = {
        "courses": run_dir / "courses.jsonl",
        "chapters": run_dir / "chapters.jsonl",
        "errors": run_dir / "errors.jsonl",
        "standardized_courses": standardized_dir,
    }
    write_jsonl(outputs["courses"], course_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(outputs["errors"], error_rows)
    return outputs


def run_question_generation_v3(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    courses, errors = ingest_all(input_dir, storage, run_id)
    selected = courses
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        selected = [course for course in selected if course.course_id in allowed]
    if limit:
        selected = selected[:limit]

    run_dir = ensure_dir(settings.output_root / run_id)
    course_rows = [course.model_dump(mode="json") for course in selected]
    chapter_rows = [
        {
            "course_id": course.course_id,
            "course_title": course.title,
            **chapter.model_dump(mode="json"),
        }
        for course in selected
        for chapter in course.chapters
    ]
    topic_rows: list[dict] = []
    edge_rows: list[dict] = []
    pedagogy_rows: list[dict] = []
    friction_rows: list[dict] = []
    raw_candidate_rows: list[dict] = []
    rejected_rows: list[dict] = []
    scored_rows: list[dict] = []
    duplicate_rows: list[dict] = []
    final_rows: list[dict] = []
    summary_rows: list[dict] = []
    error_rows = list(errors)
    per_course: dict[str, dict] = {}

    for course in selected:
        try:
            result = run_candidate_generation_for_course(course)
            per_course[course.course_id] = result
            write_candidate_course_artifacts(run_dir, course.course_id, result)
            topic_rows.extend(item.model_dump(mode="json") for item in result["topics"])
            edge_rows.extend(item.model_dump(mode="json") for item in result["edges"])
            pedagogy_rows.extend(item.model_dump(mode="json") for item in result["pedagogy"])
            friction_rows.extend(item.model_dump(mode="json") for item in result["frictions"])
            raw_candidate_rows.extend(item.model_dump(mode="json") for item in result["raw_candidates"])
            rejected_rows.extend(item.model_dump(mode="json") for item in result["rejected_candidates"])
            scored_rows.extend(item.model_dump(mode="json") for item in result["scored_candidates"])
            duplicate_rows.extend(item.model_dump(mode="json") for item in result["duplicate_clusters"])
            final_rows.extend(item.model_dump(mode="json") for item in result["final_selected"])
            summary_rows.append(result["selection_summary"].model_dump(mode="json") | {"course_id": course.course_id})
        except Exception as exc:  # noqa: BLE001
            error_rows.append(
                {
                    "course_id": course.course_id,
                    "raw_yaml_path": course.raw_yaml_path,
                    "error": str(exc),
                }
            )

    outputs = {
        "courses": run_dir / "courses.jsonl",
        "chapters": run_dir / "chapters.jsonl",
        "topics": run_dir / "topics.jsonl",
        "edges": run_dir / "edges.jsonl",
        "pedagogy": run_dir / "pedagogy.jsonl",
        "friction_points": run_dir / "friction_points.jsonl",
        "raw_candidates": run_dir / "raw_candidates.jsonl",
        "rejected_candidates": run_dir / "rejected_candidates.jsonl",
        "scored_candidates": run_dir / "scored_candidates.jsonl",
        "duplicate_clusters": run_dir / "duplicate_clusters.jsonl",
        "final_selected": run_dir / "final_selected.jsonl",
        "selection_summaries": run_dir / "selection_summaries.jsonl",
        "report": run_dir / "question_gen_v3_report.md",
        "errors": run_dir / "question_gen_v3_errors.jsonl",
    }
    write_jsonl(outputs["courses"], course_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(outputs["topics"], topic_rows)
    write_jsonl(outputs["edges"], edge_rows)
    write_jsonl(outputs["pedagogy"], pedagogy_rows)
    write_jsonl(outputs["friction_points"], friction_rows)
    write_jsonl(outputs["raw_candidates"], raw_candidate_rows)
    write_jsonl(outputs["rejected_candidates"], rejected_rows)
    write_jsonl(outputs["scored_candidates"], scored_rows)
    write_jsonl(outputs["duplicate_clusters"], duplicate_rows)
    write_jsonl(outputs["final_selected"], final_rows)
    write_jsonl(outputs["selection_summaries"], summary_rows)
    write_jsonl(outputs["errors"], error_rows)
    write_candidate_run_report(run_dir, per_course)
    return outputs


def build_question_generation_v3_review_bundle(
    run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    per_course: dict[str, dict] = {}
    for course in course_rows:
        artifact_dir = run_dir / "course_artifacts" / course.course_id
        per_course[course.course_id] = {
            "final_selected": [
                ScoredCandidate.model_validate_json(line)
                for line in (artifact_dir / "final_selected.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        }
    return build_candidate_review_bundle(run_dir, settings, course_rows, per_course)


def run_question_generation_v4_policy(
    source_run_dir: Path,
    settings: Settings,
    run_id: str,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    run_dir = ensure_dir(settings.output_root / run_id)
    per_course: dict[str, dict] = {}
    decision_rows: list[dict] = []
    canonical_rows: list[dict] = []
    retention_rows: list[dict] = []
    cache_entry_rows: list[dict] = []
    metrics_rows: list[dict] = []
    error_rows: list[dict] = []
    for course in course_rows:
        try:
            v3_payload = load_candidate_course_artifacts(source_run_dir, course.course_id)
            result = run_legacy_policy_stage(v3_payload)
            scored_by_id = {row.candidate.candidate_id: row for row in v3_payload["scored_candidates"]}
            answers_by_candidate_id = {}
            cache_entries = build_cache_entries(
                candidates_by_id=scored_by_id,
                decisions=result["policy_decisions"],
                answers_by_candidate_id=answers_by_candidate_id,
                alias_ids_by_canonical=result["alias_ids_by_canonical"],
            )
            result["cache_entries"] = cache_entries
            result["scored_by_id"] = scored_by_id
            per_course[course.course_id] = result
            course_dir = ensure_dir(run_dir / "course_artifacts" / course.course_id)
            write_jsonl(course_dir / "policy_decisions.jsonl", [item.model_dump(mode="json") for item in result["policy_decisions"]])
            write_jsonl(course_dir / "canonical_groups.jsonl", [item.model_dump(mode="json") for item in result["canonical_groups"]])
            write_jsonl(course_dir / "retention_records.jsonl", [item.model_dump(mode="json") for item in result["retention_records"]])
            write_jsonl(course_dir / "cache_entries.jsonl", [item.model_dump(mode="json") for item in cache_entries])
            (course_dir / "policy_metrics.json").write_text(json.dumps(result["metrics"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            decision_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["policy_decisions"])
            canonical_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["canonical_groups"])
            retention_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["retention_records"])
            cache_entry_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in cache_entries)
            metrics_rows.append({"course_id": course.course_id, **result["metrics"]})
        except Exception as exc:  # noqa: BLE001
            error_rows.append({"course_id": course.course_id, "error": str(exc)})
    outputs = {
        "policy_decisions": run_dir / "policy_decisions.jsonl",
        "canonical_groups": run_dir / "canonical_groups.jsonl",
        "retention_records": run_dir / "retention_records.jsonl",
        "cache_entries": run_dir / "cache_entries.jsonl",
        "policy_metrics": run_dir / "policy_metrics.jsonl",
        "report": run_dir / "question_gen_v4_report.md",
        "errors": run_dir / "question_gen_v4_errors.jsonl",
    }
    write_jsonl(outputs["policy_decisions"], decision_rows)
    write_jsonl(outputs["canonical_groups"], canonical_rows)
    write_jsonl(outputs["retention_records"], retention_rows)
    write_jsonl(outputs["cache_entries"], cache_entry_rows)
    write_jsonl(outputs["policy_metrics"], metrics_rows)
    write_jsonl(outputs["errors"], error_rows)
    write_legacy_policy_report(run_dir, per_course)
    outputs["report"] = run_dir / "question_gen_v4_report.md"
    return outputs


def build_question_generation_v4_review_bundle(
    run_dir: Path,
    source_run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    per_course: dict[str, dict] = {}
    for course in course_rows:
        v3_payload = load_candidate_course_artifacts(source_run_dir, course.course_id)
        scored_by_id = {row.candidate.candidate_id: row for row in v3_payload["scored_candidates"]}
        decisions = [
            PolicyDecision.model_validate_json(line)
            for line in (run_dir / "course_artifacts" / course.course_id / "policy_decisions.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        cache_entries = [
            CacheEntry.model_validate_json(line)
            for line in (run_dir / "course_artifacts" / course.course_id / "cache_entries.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        metrics = json.loads((run_dir / "course_artifacts" / course.course_id / "policy_metrics.json").read_text(encoding="utf-8"))
        per_course[course.course_id] = {
            "policy_decisions": decisions,
            "cache_entries": cache_entries,
            "metrics": metrics,
            "scored_by_id": scored_by_id,
        }
    return build_legacy_policy_review_bundle(run_dir, settings, course_rows, per_course)


def run_question_generation_v4_1_policy(
    source_run_dir: Path,
    settings: Settings,
    run_id: str,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    run_dir = ensure_dir(settings.output_root / run_id)
    per_course: dict[str, dict] = {}
    validated_rows: list[dict] = []
    visible_rows: list[dict] = []
    hidden_rows: list[dict] = []
    warning_rows: list[dict] = []
    canonical_rows: list[dict] = []
    cache_entry_rows: list[dict] = []
    reject_rows: list[dict] = []
    metrics_rows: list[dict] = []
    error_rows: list[dict] = []
    for course in course_rows:
        try:
            v3_payload = load_candidate_course_artifacts(source_run_dir, course.course_id)
            result = run_policy_stage(v3_payload)
            scored_by_id = {row.candidate.candidate_id: row for row in v3_payload["scored_candidates"]}
            cache_entries = build_cache_entries(
                candidates_by_id=scored_by_id,
                decisions=result["policy_decisions"],
                answers_by_candidate_id={},
                alias_ids_by_canonical=result["alias_ids_by_canonical"],
            )
            result["cache_entries"] = cache_entries
            per_course[course.course_id] = result
            course_dir = ensure_dir(run_dir / "course_artifacts" / course.course_id)
            write_jsonl(course_dir / "validated_correct_all.jsonl", [item.model_dump(mode="json") for item in result["validated_correct_all"]])
            write_jsonl(course_dir / "visible_curated.jsonl", [item.model_dump(mode="json") for item in result["visible_curated"]])
            write_jsonl(course_dir / "hidden_correct.jsonl", [item.model_dump(mode="json") for item in result["hidden_correct"]])
            write_jsonl(course_dir / "coverage_warnings.jsonl", [item.model_dump(mode="json") for item in result["coverage_warnings"]])
            write_jsonl(course_dir / "canonical_groups.jsonl", [item.model_dump(mode="json") for item in result["canonical_groups"]])
            write_jsonl(course_dir / "cache_entries.jsonl", [item.model_dump(mode="json") for item in cache_entries])
            write_jsonl(course_dir / "hard_reject_records.jsonl", [item.model_dump(mode="json") for item in result["hard_reject_records"]])
            (course_dir / "hard_reject_audit_summary.json").write_text(
                json.dumps(result["hard_reject_audit_summary"], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (course_dir / "policy_metrics.json").write_text(json.dumps(result["metrics"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            validated_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["validated_correct_all"])
            visible_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["visible_curated"])
            hidden_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["hidden_correct"])
            warning_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["coverage_warnings"])
            canonical_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["canonical_groups"])
            cache_entry_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in cache_entries)
            reject_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["hard_reject_records"])
            metrics_rows.append({"course_id": course.course_id, **result["metrics"], **result["hard_reject_audit_summary"]})
        except Exception as exc:  # noqa: BLE001
            error_rows.append({"course_id": course.course_id, "error": str(exc)})
    outputs = {
        "validated_correct_all": run_dir / "validated_correct_all.jsonl",
        "visible_curated": run_dir / "visible_curated.jsonl",
        "hidden_correct": run_dir / "hidden_correct.jsonl",
        "coverage_warnings": run_dir / "coverage_warnings.jsonl",
        "canonical_groups": run_dir / "canonical_groups.jsonl",
        "cache_entries": run_dir / "cache_entries.jsonl",
        "hard_reject_records": run_dir / "hard_reject_records.jsonl",
        "policy_metrics": run_dir / "policy_metrics.jsonl",
        "report": run_dir / "question_gen_v4_1_report.md",
        "errors": run_dir / "question_gen_v4_1_errors.jsonl",
    }
    write_jsonl(outputs["validated_correct_all"], validated_rows)
    write_jsonl(outputs["visible_curated"], visible_rows)
    write_jsonl(outputs["hidden_correct"], hidden_rows)
    write_jsonl(outputs["coverage_warnings"], warning_rows)
    write_jsonl(outputs["canonical_groups"], canonical_rows)
    write_jsonl(outputs["cache_entries"], cache_entry_rows)
    write_jsonl(outputs["hard_reject_records"], reject_rows)
    write_jsonl(outputs["policy_metrics"], metrics_rows)
    write_jsonl(outputs["errors"], error_rows)
    write_policy_report(run_dir, per_course)
    return outputs


def build_question_generation_v4_1_review_bundle(
    run_dir: Path,
    source_run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    per_course: dict[str, dict] = {}
    for course in course_rows:
        artifact_dir = run_dir / "course_artifacts" / course.course_id
        per_course[course.course_id] = {
            "validated_correct_all": [
                CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "validated_correct_all.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "visible_curated": [
                CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "visible_curated.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "hidden_correct": [
                CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "hidden_correct.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "coverage_warnings": [
                CoverageWarning.model_validate_json(line)
                for line in (artifact_dir / "coverage_warnings.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "cache_entries": [
                CacheEntry.model_validate_json(line)
                for line in (artifact_dir / "cache_entries.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "metrics": json.loads((artifact_dir / "policy_metrics.json").read_text(encoding="utf-8")),
            "hard_reject_audit_summary": json.loads((artifact_dir / "hard_reject_audit_summary.json").read_text(encoding="utf-8")),
        }
    return build_policy_review_bundle(run_dir, settings, course_rows, per_course)


def run_question_ledger_v6(
    source_run_dir: Path,
    settings: Settings,
    run_id: str,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    run_dir = ensure_dir(settings.output_root / run_id)
    per_course: dict[str, dict] = {}
    all_rows: list[dict] = []
    visible_rows: list[dict] = []
    cache_rows: list[dict] = []
    alias_rows: list[dict] = []
    anchor_summary_rows: list[dict] = []
    error_rows: list[dict] = []
    inspection_sections: list[str] = []
    for course in course_rows:
        try:
            v3_payload = load_candidate_course_artifacts_for_ledger(source_run_dir, course.course_id)
            result = build_question_ledger_for_course(v3_payload)
            per_course[course.course_id] = result
            course_dir = ensure_dir(run_dir / "course_artifacts" / course.course_id)
            write_jsonl(course_dir / "all_questions.jsonl", [item.model_dump(mode="json") for item in result["all_questions"]])
            write_jsonl(course_dir / "visible_curated.jsonl", [item.model_dump(mode="json") for item in result["visible_curated"]])
            write_jsonl(course_dir / "cache_servable.jsonl", [item.model_dump(mode="json") for item in result["cache_servable"]])
            write_jsonl(course_dir / "aliases.jsonl", [item.model_dump(mode="json") for item in result["aliases"]])
            (course_dir / "anchors_summary.json").write_text(
                json.dumps([item.model_dump(mode="json") for item in result["anchor_summaries"]], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (course_dir / "inspection_report.md").write_text(result["inspection_report"], encoding="utf-8")
            all_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["all_questions"])
            visible_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["visible_curated"])
            cache_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["cache_servable"])
            alias_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["aliases"])
            anchor_summary_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["anchor_summaries"])
            inspection_sections.append(f"# Course {course.course_id}\n\n{result['inspection_report'].strip()}\n")
        except Exception as exc:  # noqa: BLE001
            error_rows.append({"course_id": course.course_id, "error": str(exc)})
    outputs = {
        "all_questions": run_dir / "all_questions.jsonl",
        "visible_curated": run_dir / "visible_curated.jsonl",
        "cache_servable": run_dir / "cache_servable.jsonl",
        "aliases": run_dir / "aliases.jsonl",
        "anchors_summary": run_dir / "anchors_summary.json",
        "inspection_report": run_dir / "inspection_report.md",
        "report": run_dir / "question_ledger_v6_report.md",
        "errors": run_dir / "question_ledger_v6_errors.jsonl",
    }
    write_jsonl(outputs["all_questions"], all_rows)
    write_jsonl(outputs["visible_curated"], visible_rows)
    write_jsonl(outputs["cache_servable"], cache_rows)
    write_jsonl(outputs["aliases"], alias_rows)
    outputs["anchors_summary"].write_text(json.dumps(anchor_summary_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    outputs["inspection_report"].write_text("\n\n".join(section.strip() for section in inspection_sections).rstrip() + "\n", encoding="utf-8")
    write_jsonl(outputs["errors"], error_rows)
    write_ledger_run_report(run_dir, per_course)
    return outputs


def build_question_ledger_v6_review_bundle(
    run_dir: Path,
    source_run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    course_rows = [
        NormalizedCourse.model_validate_json(line)
        for line in (source_run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        course_rows = [course for course in course_rows if course.course_id in allowed]
    per_course: dict[str, dict] = {}
    for course in course_rows:
        artifact_dir = run_dir / "course_artifacts" / course.course_id
        per_course[course.course_id] = {
            "all_questions": [
                LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "all_questions.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "visible_curated": [
                LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "visible_curated.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "cache_servable": [
                LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "cache_servable.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "aliases": [
                LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "aliases.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "anchor_summaries": [
                AnchorSummary.model_validate(item)
                for item in json.loads((artifact_dir / "anchors_summary.json").read_text(encoding="utf-8"))
            ],
            "inspection_report": (artifact_dir / "inspection_report.md").read_text(encoding="utf-8"),
        }
    return build_ledger_review_bundle(run_dir, course_rows, per_course)
