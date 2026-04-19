from __future__ import annotations

import json
from pathlib import Path

import yaml

from course_pipeline.config import Settings
from course_pipeline.normalize import iter_courses
from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow
from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.question_seed_generate import generate_seed_candidates
from course_pipeline.questions.candidates import (
    ScoredCandidate,
    build_candidate_review_bundle,
    run_candidate_generation_for_course,
    write_candidate_course_artifacts,
    write_candidate_run_report,
)
from course_pipeline.questions.candidates.config import load_default_config
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
    build_cache_entries,
    build_policy_review_bundle,
    load_candidate_course_artifacts,
    run_policy_stage,
    write_policy_report,
)
from course_pipeline.schemas import (
    NormalizedCourse,
)
from course_pipeline.semantic_pipeline import (
    run_semantic_stage_for_course,
    write_semantic_course_yaml,
    write_semantic_stage_artifacts,
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
            result = run_candidate_generation_for_course(course, settings=settings, run_dir=run_dir)
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


def _select_courses(
    courses: list[NormalizedCourse],
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> list[NormalizedCourse]:
    selected = courses
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        selected = [course for course in selected if course.course_id in allowed]
    if limit:
        selected = selected[:limit]
    return selected


def _write_courses_and_chapters(run_dir: Path, selected: list[NormalizedCourse]) -> tuple[Path, Path]:
    courses_path = run_dir / "courses.jsonl"
    chapters_path = run_dir / "chapters.jsonl"
    write_jsonl(courses_path, [course.model_dump(mode="json") for course in selected])
    write_jsonl(
        chapters_path,
        [
            {
                "course_id": course.course_id,
                "course_title": course.title,
                **chapter.model_dump(mode="json"),
            }
            for course in selected
            for chapter in course.chapters
        ],
    )
    return courses_path, chapters_path


def run_semantic_extract_llm_stage(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    courses, errors = ingest_all(input_dir, storage, run_id)
    selected = _select_courses(courses, limit=limit, course_ids=course_ids)
    run_dir = ensure_dir(settings.output_root / run_id)
    courses_path, chapters_path = _write_courses_and_chapters(run_dir, selected)
    per_course: dict[str, dict] = {}
    semantic_topics: list[dict] = []
    semantic_anchors: list[dict] = []
    semantic_alias_groups: list[dict] = []
    semantic_frictions: list[dict] = []
    topics: list[dict] = []
    edges: list[dict] = []
    pedagogy: list[dict] = []
    friction_points: list[dict] = []
    validation_reports: list[dict] = []
    for course in selected:
        result = run_semantic_stage_for_course(raw_course=course, settings=settings, run_dir=run_dir)
        per_course[course.course_id] = result
        course_dir = run_dir / "course_artifacts" / course.course_id
        write_semantic_stage_artifacts(run_dir, course.course_id, result, base_dir=course_dir)
        write_semantic_course_yaml(run_dir, course.course_id, result, base_dir=course_dir)
        semantic_topics.extend(item.model_dump(mode="json") for item in result.semantic_topic_records)
        semantic_anchors.extend(item.model_dump(mode="json") for item in result.semantic_anchor_candidates)
        semantic_alias_groups.extend(item.model_dump(mode="json") for item in result.semantic_alias_groups)
        semantic_frictions.extend(item.model_dump(mode="json") for item in result.semantic_friction_records)
        topics.extend(item.model_dump(mode="json") for item in result.topics)
        edges.extend(item.model_dump(mode="json") for item in result.edges)
        pedagogy.extend(item.model_dump(mode="json") for item in result.pedagogy)
        friction_points.extend(item.model_dump(mode="json") for item in result.frictions)
        validation_reports.append(result.semantic_validation_report.model_dump(mode="json"))
    outputs = {
        "courses": courses_path,
        "chapters": chapters_path,
        "semantic_topics": run_dir / "semantic_topics.jsonl",
        "semantic_anchors": run_dir / "semantic_anchors.jsonl",
        "semantic_alias_groups": run_dir / "semantic_alias_groups.jsonl",
        "semantic_frictions": run_dir / "semantic_frictions.jsonl",
        "topics": run_dir / "topics.jsonl",
        "edges": run_dir / "edges.jsonl",
        "pedagogy": run_dir / "pedagogy.jsonl",
        "friction_points": run_dir / "friction_points.jsonl",
        "semantic_validation_reports": run_dir / "semantic_validation_reports.jsonl",
        "errors": run_dir / "semantic_extract_errors.jsonl",
        "report": run_dir / "semantic_run_report.md",
    }
    write_jsonl(outputs["semantic_topics"], semantic_topics)
    write_jsonl(outputs["semantic_anchors"], semantic_anchors)
    write_jsonl(outputs["semantic_alias_groups"], semantic_alias_groups)
    write_jsonl(outputs["semantic_frictions"], semantic_frictions)
    write_jsonl(outputs["topics"], topics)
    write_jsonl(outputs["edges"], edges)
    write_jsonl(outputs["pedagogy"], pedagogy)
    write_jsonl(outputs["friction_points"], friction_points)
    write_jsonl(outputs["semantic_validation_reports"], validation_reports)
    write_jsonl(outputs["errors"], list(errors))
    inspect_semantic_run(run_dir)
    return outputs


def run_question_seed_generation_stage(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    courses, errors = ingest_all(input_dir, storage, run_id)
    selected = _select_courses(courses, limit=limit, course_ids=course_ids)
    run_dir = ensure_dir(settings.output_root / run_id)
    courses_path, chapters_path = _write_courses_and_chapters(run_dir, selected)
    seed_rows: list[dict] = []
    for course in selected:
        semantic_result = run_semantic_stage_for_course(raw_course=course, settings=settings, run_dir=run_dir)
        course_dir = run_dir / "course_artifacts" / course.course_id
        write_semantic_stage_artifacts(run_dir, course.course_id, semantic_result, base_dir=course_dir)
        write_semantic_course_yaml(run_dir, course.course_id, semantic_result, base_dir=course_dir)
        seeds = generate_seed_candidates(
            semantic_result.normalized_document,
            semantic_result.topics,
            semantic_result.edges,
            semantic_result.pedagogy,
            semantic_result.frictions,
            load_default_config(),
            anchors=semantic_result.sanitized_anchor_candidates,
        )
        write_jsonl(course_dir / "seed_candidates.jsonl", [item.model_dump(mode="json") for item in seeds["candidates"]])
        (course_dir / "seed_invariant_report.json").write_text(
            seeds["invariant_report"].model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        seed_rows.extend(item.model_dump(mode="json") for item in seeds["candidates"])
    outputs = {
        "courses": courses_path,
        "chapters": chapters_path,
        "seed_candidates": run_dir / "seed_candidates.jsonl",
        "errors": run_dir / "question_seed_errors.jsonl",
        "report": run_dir / "question_refine_report.md",
    }
    write_jsonl(outputs["seed_candidates"], seed_rows)
    write_jsonl(outputs["errors"], list(errors))
    inspect_question_refine_run(run_dir)
    return outputs


def run_question_repair_stage(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    outputs = run_question_generation_v3(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=course_ids,
    )
    inspect_question_refine_run(settings.output_root / run_id)
    return outputs


def run_question_expand_stage(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    outputs = run_question_generation_v3(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=course_ids,
    )
    inspect_question_refine_run(settings.output_root / run_id)
    return outputs


def inspect_semantic_run(run_dir: Path) -> Path:
    reports_path = run_dir / "semantic_validation_reports.jsonl"
    report_rows = [
        json.loads(line)
        for line in reports_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ] if reports_path.exists() else []
    lines = ["# Semantic Run Report", ""]
    lines.append(f"- courses: {len(report_rows)}")
    lines.append(f"- semantic topics: {_jsonl_count(run_dir / 'semantic_topics.jsonl')}")
    lines.append(f"- sanitized topics: {_jsonl_count(run_dir / 'topics.jsonl')}")
    lines.append(f"- suspicious anchors: {sum(int(row.get('suspicious_anchor_count', 0)) for row in report_rows)}")
    lines.append("")
    for row in report_rows:
        lines.append(f"## Course `{row.get('course_id')}`")
        lines.append("")
        lines.append(f"- kept: {row.get('kept_count', 0)}")
        lines.append(f"- dropped: {row.get('dropped_count', 0)}")
        lines.append(f"- merged: {row.get('merged_count', 0)}")
        lines.append("")
    path = run_dir / "semantic_run_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def inspect_question_refine_run(run_dir: Path) -> Path:
    lines = ["# Question Refine Report", ""]
    lines.append(f"- seed candidates: {_jsonl_count(run_dir / 'seed_candidates.jsonl')}")
    lines.append(f"- candidate repairs: {_jsonl_count(run_dir / 'candidate_repairs.jsonl')}")
    lines.append(f"- candidate expansions: {_jsonl_count(run_dir / 'candidate_expansions.jsonl')}")
    lines.append(f"- merged candidates: {_jsonl_count(run_dir / 'merged_candidates.jsonl')}")
    lines.append("")
    path = run_dir / "question_refine_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def run_pipeline_refactor(
    input_dir: Path,
    settings: Settings,
    run_id: str,
    *,
    limit: int | None = None,
    course_ids: list[str] | None = None,
    include_answers: bool = True,
) -> Path:
    config = RunConfig(
        run_label=run_id,
        input_root=input_dir,
        output_root=settings.output_root,
        course_ids=course_ids,
        max_courses=limit,
        strict_mode=True,
        enable_answer_generation=include_answers,
        overwrite_existing=True,
    )
    result = question_generation_pipeline_flow(config)
    return settings.output_root / result.run_id


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
    return run_question_generation_v4_1_policy(
        source_run_dir=source_run_dir,
        settings=settings,
        run_id=run_id,
        course_ids=course_ids,
    )


def build_question_generation_v4_review_bundle(
    run_dir: Path,
    source_run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    return build_question_generation_v4_1_review_bundle(
        run_dir=run_dir,
        source_run_dir=source_run_dir,
        settings=settings,
        course_ids=course_ids,
    )


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
