from __future__ import annotations

import json
from pathlib import Path

import yaml

from course_pipeline.config import Settings
from course_pipeline.learning import LearningOutcomeExtractor
from course_pipeline.normalize import iter_courses
from course_pipeline.schemas import (
    CandidateQuestionOut,
    LearnerFrictionCandidateOut,
    LearningOutcomeExtractionOut,
    NormalizedCourse,
    TopicOut,
)
from course_pipeline.question_gen_v2 import (
    QuestionGenerationV2,
    load_question_gen_v2_run,
    write_question_gen_v2_report,
    write_review_answers_jsonl,
)
from course_pipeline.question_gen_v3.pipeline import (
    build_review_bundle as build_question_gen_v3_review_bundle_internal,
    run_question_gen_v3_for_course,
    write_course_artifacts as write_question_gen_v3_course_artifacts,
    write_run_report as write_question_gen_v3_report,
)
from course_pipeline.question_gen_v4.build_cache_entries import build_cache_entries
from course_pipeline.question_gen_v4.run_v4_policy import (
    build_v4_review_bundle as build_question_gen_v4_review_bundle_internal,
    load_v3_course_artifacts,
    run_question_gen_v4_policy,
    write_v4_report,
)
from course_pipeline.question_gen_v4_1.run_v4_1_policy import (
    build_v4_1_review_bundle as build_question_gen_v4_1_review_bundle_internal,
    load_v3_course_artifacts as load_v3_course_artifacts_v4_1,
    run_question_gen_v4_1_policy,
    write_v4_1_report,
)
from course_pipeline.question_ledger_v6.run_v6 import (
    build_question_ledger_v6_for_course,
    build_v6_review_bundle as build_question_ledger_v6_review_bundle_internal,
    load_v3_course_artifacts as load_v3_course_artifacts_v6,
    write_v6_run_report,
)
from course_pipeline.question_cache import (
    QuestionCacheGenerator,
    load_learning_outcome_run,
)
from course_pipeline.storage import Storage
from course_pipeline.utils import ensure_dir, slugify, write_jsonl, write_yaml


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


def run_learning_outcomes(
    input_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    limit: int | None = None,
) -> dict[str, Path]:
    courses, errors = ingest_all(input_dir, storage, run_id)
    selected = courses[:limit] if limit else courses
    run_dir = ensure_dir(settings.output_root / run_id)
    learning_yaml_dir = ensure_dir(run_dir / "learning_outcomes_yaml")
    extractor = LearningOutcomeExtractor(settings)

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
    extraction_rows: list[dict] = []
    error_rows = list(errors)

    for course in selected:
        try:
            extraction = extractor.extract(course)
            storage.upsert_learning_outcome_extraction(run_id, extraction)
            extraction_payload = extraction.model_dump(mode="json")
            extraction_rows.append(extraction_payload)
            write_yaml(
                learning_yaml_dir / f"{course.course_id}.yaml",
                extraction_payload,
                width=80,
            )
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
        "learning_outcomes": run_dir / "learning_outcomes.jsonl",
        "learning_outcomes_yaml": learning_yaml_dir,
        "errors": run_dir / "learning_outcome_errors.jsonl",
    }
    write_jsonl(outputs["courses"], course_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(outputs["learning_outcomes"], extraction_rows)
    write_jsonl(outputs["errors"], error_rows)
    return outputs


def render_learning_outcomes_yaml(run_dir: Path, width: int = 80) -> Path:
    learning_jsonl = run_dir / "learning_outcomes.jsonl"
    if not learning_jsonl.exists():
        raise FileNotFoundError(f"missing artifact: {learning_jsonl}")
    yaml_dir = ensure_dir(run_dir / "learning_outcomes_yaml")
    rows = [
        yaml.safe_load(line)
        for line in learning_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for row in rows:
        course_id = str(row["course_id"])
        write_yaml(yaml_dir / f"{course_id}.yaml", row, width=width)
    return yaml_dir


def build_question_cache(
    source_run_dir: Path,
    settings: Settings,
    storage: Storage,
    run_id: str,
    limit: int | None = None,
) -> dict[str, Path]:
    source_extractions = load_learning_outcome_run(source_run_dir)
    selected = source_extractions[:limit] if limit else source_extractions
    run_dir = ensure_dir(settings.output_root / run_id)
    yaml_dir = ensure_dir(run_dir / "question_cache_yaml")
    generator = QuestionCacheGenerator(settings)

    group_rows: list[dict] = []
    variation_rows: list[dict] = []
    answer_rows: list[dict] = []
    validation_rows: list[dict] = []
    coverage_rows: list[dict] = []
    error_rows: list[dict] = []

    for extraction in selected:
        course_yaml_payload = {
            "course_id": extraction.course_id,
            "course_title": extraction.course_title,
            "claims": [],
        }
        for claim in extraction.learning_outcomes:
            try:
                generated, validation_logs, coverage_audit = generator.generate_for_claim(
                    extraction=extraction,
                    claim=claim,
                    source_run_id=source_run_dir.name,
                )
                storage.upsert_claim_coverage_audit(coverage_audit)
                coverage_rows.append(coverage_audit.model_dump(mode="json"))
                for log in validation_logs:
                    storage.log_question_cache_validation(log)
                    validation_rows.append(log.model_dump(mode="json"))
                for group in generated.question_groups:
                    storage.upsert_question_group(group)
                    group_rows.append(group.model_dump(mode="json"))
                for variation in generated.variations:
                    storage.upsert_question_variation(variation)
                    variation_rows.append(variation.model_dump(mode="json"))
                for answer in generated.canonical_answers:
                    storage.upsert_canonical_answer(answer)
                    answer_rows.append(answer.model_dump(mode="json"))
                course_yaml_payload["claims"].append(generated.model_dump(mode="json"))
            except Exception as exc:  # noqa: BLE001
                error_rows.append(
                    {
                        "course_id": extraction.course_id,
                        "claim_id": claim.id,
                        "error": str(exc),
                    }
                )
        write_yaml(yaml_dir / f"{extraction.course_id}.yaml", course_yaml_payload, width=80)

    outputs = {
        "claim_question_groups": run_dir / "claim_question_groups.jsonl",
        "question_group_variations": run_dir / "question_group_variations.jsonl",
        "canonical_answers": run_dir / "canonical_answers.jsonl",
        "question_cache_validation_logs": run_dir / "question_cache_validation_logs.jsonl",
        "claim_coverage_audit": run_dir / "claim_coverage_audit.jsonl",
        "question_cache_yaml": yaml_dir,
        "errors": run_dir / "question_cache_errors.jsonl",
    }
    write_jsonl(outputs["claim_question_groups"], group_rows)
    write_jsonl(outputs["question_group_variations"], variation_rows)
    write_jsonl(outputs["canonical_answers"], answer_rows)
    write_jsonl(outputs["question_cache_validation_logs"], validation_rows)
    write_jsonl(outputs["claim_coverage_audit"], coverage_rows)
    write_jsonl(outputs["errors"], error_rows)
    return outputs


def run_question_generation_v2(
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
    generator = QuestionGenerationV2(settings)

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
    friction_rows: list[dict] = []
    question_rows: list[dict] = []
    error_rows = list(errors)

    for course in selected:
        try:
            topics, frictions, questions = generator.generate(course)
            topic_rows.extend(topic.model_dump(mode="json") for topic in topics)
            friction_rows.extend(candidate.model_dump(mode="json") for candidate in frictions)
            question_rows.extend(question.model_dump(mode="json") for question in questions)
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
        "learner_friction_candidates": run_dir / "learner_friction_candidates.jsonl",
        "candidate_questions": run_dir / "candidate_questions.jsonl",
        "report": run_dir / "question_gen_v2_report.md",
        "errors": run_dir / "question_gen_v2_errors.jsonl",
    }
    write_jsonl(outputs["courses"], course_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(outputs["topics"], topic_rows)
    write_jsonl(outputs["learner_friction_candidates"], friction_rows)
    write_jsonl(outputs["candidate_questions"], question_rows)
    write_jsonl(outputs["errors"], error_rows)
    write_question_gen_v2_report(
        run_dir,
        questions=[CandidateQuestionOut.model_validate(row) for row in question_rows],
        topics=[TopicOut.model_validate(row) for row in topic_rows],
        frictions=[LearnerFrictionCandidateOut.model_validate(row) for row in friction_rows],
    )
    return outputs


def build_question_generation_review_bundle(
    run_dir: Path,
    settings: Settings,
    course_ids: list[str] | None = None,
) -> dict[str, Path]:
    courses, questions = load_question_gen_v2_run(run_dir)
    selected_courses = courses
    if course_ids:
        allowed = {course_id.strip() for course_id in course_ids if course_id.strip()}
        selected_courses = [course for course in selected_courses if course.course_id in allowed]
    questions_by_course: dict[str, list] = {}
    for question in questions:
        questions_by_course.setdefault(question.course_id, []).append(question)

    generator = QuestionGenerationV2(settings)
    bundle_dir = ensure_dir(run_dir / "review_bundle")
    answer_rows: list[dict] = []

    for course in selected_courses:
        course_questions = sorted(
            questions_by_course.get(course.course_id, []),
            key=lambda item: (item.chapter_id, item.mastery_band, -item.score, item.question_text.lower()),
        )
        if not course_questions:
            continue
        answers = generator.answer_questions_for_review(course, course_questions)
        answer_rows.extend(
            {
                "course_id": course.course_id,
                "question_id": question.question_id,
                "question_text": question.question_text,
                "answer_markdown": answers.get(question.question_id, ""),
            }
            for question in course_questions
        )
        lines = [f"# {course.title} (`{course.course_id}`)", "", "## Q/A Pairs", ""]
        for question in course_questions:
            lines.append(f"Q: {question.question_text}  ")
            lines.append(f"A: {answers.get(question.question_id, '').strip()}".rstrip())
            lines.append("")
        lines.extend(
            [
                "## Scraped Course Description",
                "",
                "### Summary",
                "",
                (course.summary or "").strip(),
                "",
                "### Overview",
                "",
                (course.overview or "").strip(),
                "",
                "### Syllabus",
                "",
            ]
        )
        for chapter in course.chapters:
            lines.append(f"{chapter.chapter_index}. {chapter.title}  ")
            lines.append((chapter.summary or "").strip())
            lines.append("")
        (bundle_dir / f"{course.course_id}_{slugify(course.title)}.md").write_text(
            "\n".join(lines).rstrip() + "\n",
            encoding="utf-8",
        )

    outputs = {
        "review_bundle": bundle_dir,
        "review_answers": run_dir / "review_answers.jsonl",
    }
    write_review_answers_jsonl(outputs["review_answers"], answer_rows)
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
            result = run_question_gen_v3_for_course(course)
            per_course[course.course_id] = result
            write_question_gen_v3_course_artifacts(run_dir, course.course_id, result)
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
    write_question_gen_v3_report(run_dir, per_course)
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
                __import__("course_pipeline.question_gen_v3.models", fromlist=["ScoredCandidate"]).ScoredCandidate.model_validate_json(line)
                for line in (artifact_dir / "final_selected.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        }
    return build_question_gen_v3_review_bundle_internal(run_dir, settings, course_rows, per_course)


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
            v3_payload = load_v3_course_artifacts(source_run_dir, course.course_id)
            result = run_question_gen_v4_policy(v3_payload)
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
    write_v4_report(run_dir, per_course)
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
        v3_payload = load_v3_course_artifacts(source_run_dir, course.course_id)
        scored_by_id = {row.candidate.candidate_id: row for row in v3_payload["scored_candidates"]}
        decisions = [
            __import__("course_pipeline.question_gen_v4.policy_models", fromlist=["PolicyDecision"]).PolicyDecision.model_validate_json(line)
            for line in (run_dir / "course_artifacts" / course.course_id / "policy_decisions.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        cache_entries = [
            __import__("course_pipeline.question_gen_v4.policy_models", fromlist=["CacheEntry"]).CacheEntry.model_validate_json(line)
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
    return build_question_gen_v4_review_bundle_internal(run_dir, settings, course_rows, per_course)


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
            v3_payload = load_v3_course_artifacts_v4_1(source_run_dir, course.course_id)
            result = run_question_gen_v4_1_policy(v3_payload)
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
    write_v4_1_report(run_dir, per_course)
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
                __import__("course_pipeline.question_gen_v4_1.policy_models", fromlist=["CandidateRecord"]).CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "validated_correct_all.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "visible_curated": [
                __import__("course_pipeline.question_gen_v4_1.policy_models", fromlist=["CandidateRecord"]).CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "visible_curated.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "hidden_correct": [
                __import__("course_pipeline.question_gen_v4_1.policy_models", fromlist=["CandidateRecord"]).CandidateRecord.model_validate_json(line)
                for line in (artifact_dir / "hidden_correct.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "coverage_warnings": [
                __import__("course_pipeline.question_gen_v4_1.policy_models", fromlist=["CoverageWarning"]).CoverageWarning.model_validate_json(line)
                for line in (artifact_dir / "coverage_warnings.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "cache_entries": [
                __import__("course_pipeline.question_gen_v4.policy_models", fromlist=["CacheEntry"]).CacheEntry.model_validate_json(line)
                for line in (artifact_dir / "cache_entries.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "metrics": json.loads((artifact_dir / "policy_metrics.json").read_text(encoding="utf-8")),
            "hard_reject_audit_summary": json.loads((artifact_dir / "hard_reject_audit_summary.json").read_text(encoding="utf-8")),
        }
    return build_question_gen_v4_1_review_bundle_internal(run_dir, settings, course_rows, per_course)


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
            v3_payload = load_v3_course_artifacts_v6(source_run_dir, course.course_id)
            result = build_question_ledger_v6_for_course(v3_payload)
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
    write_v6_run_report(run_dir, per_course)
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
                __import__("course_pipeline.question_ledger_v6.models", fromlist=["LedgerRow"]).LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "all_questions.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "visible_curated": [
                __import__("course_pipeline.question_ledger_v6.models", fromlist=["LedgerRow"]).LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "visible_curated.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "cache_servable": [
                __import__("course_pipeline.question_ledger_v6.models", fromlist=["LedgerRow"]).LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "cache_servable.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "aliases": [
                __import__("course_pipeline.question_ledger_v6.models", fromlist=["LedgerRow"]).LedgerRow.model_validate_json(line)
                for line in (artifact_dir / "aliases.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ],
            "anchor_summaries": [
                __import__("course_pipeline.question_ledger_v6.models", fromlist=["AnchorSummary"]).AnchorSummary.model_validate(item)
                for item in json.loads((artifact_dir / "anchors_summary.json").read_text(encoding="utf-8"))
            ],
            "inspection_report": (artifact_dir / "inspection_report.md").read_text(encoding="utf-8"),
        }
    return build_question_ledger_v6_review_bundle_internal(run_dir, course_rows, per_course)


def render_question_cache_yaml(run_dir: Path, width: int = 80) -> Path:
    groups_path = run_dir / "claim_question_groups.jsonl"
    variations_path = run_dir / "question_group_variations.jsonl"
    answers_path = run_dir / "canonical_answers.jsonl"
    validation_path = run_dir / "question_cache_validation_logs.jsonl"
    coverage_path = run_dir / "claim_coverage_audit.jsonl"
    if not groups_path.exists():
        raise FileNotFoundError(f"missing artifact: {groups_path}")
    groups = [yaml.safe_load(line) for line in groups_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variations = [yaml.safe_load(line) for line in variations_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    answers = [yaml.safe_load(line) for line in answers_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    validations = [yaml.safe_load(line) for line in validation_path.read_text(encoding="utf-8").splitlines() if line.strip()] if validation_path.exists() else []
    coverage = [yaml.safe_load(line) for line in coverage_path.read_text(encoding="utf-8").splitlines() if line.strip()] if coverage_path.exists() else []
    yaml_dir = ensure_dir(run_dir / "question_cache_yaml")

    groups_by_course: dict[str, list[dict]] = {}
    variations_by_group: dict[str, list[dict]] = {}
    answers_by_group: dict[str, list[dict]] = {}
    validations_by_entity: dict[str, list[dict]] = {}
    coverage_by_claim: dict[str, dict] = {}
    for group in groups:
        groups_by_course.setdefault(group["course_id"], []).append(group)
    for variation in variations:
        variations_by_group.setdefault(variation["question_group_id"], []).append(variation)
    for answer in answers:
        answers_by_group.setdefault(answer["question_group_id"], []).append(answer)
    for validation in validations:
        validations_by_entity.setdefault(validation["entity_id"], []).append(validation)
    for audit in coverage:
        coverage_by_claim[f"{audit['course_id']}:{audit['claim_id']}"] = audit

    for course_id, course_groups in groups_by_course.items():
        payload = {
            "course_id": course_id,
            "question_groups": [],
            "coverage_audit": [],
        }
        for group in course_groups:
            payload["question_groups"].append(
                {
                    **group,
                    "group_validations": validations_by_entity.get(group["question_group_id"], []),
                    "variations": variations_by_group.get(group["question_group_id"], []),
                    "answers": [
                        {
                            **answer,
                            "answer_validations": validations_by_entity.get(answer["canonical_answer_id"], []),
                        }
                        for answer in answers_by_group.get(group["question_group_id"], [])
                    ],
                }
            )
        claim_ids = sorted({group["claim_id"] for group in course_groups})
        payload["coverage_audit"] = [
            coverage_by_claim.get(f"{course_id}:{claim_id}", {"course_id": course_id, "claim_id": claim_id})
            for claim_id in claim_ids
        ]
        write_yaml(yaml_dir / f"{course_id}.yaml", payload, width=width)
    return yaml_dir
