from __future__ import annotations

from pathlib import Path

import yaml

from course_pipeline.normalize import iter_courses
from course_pipeline.utils import ensure_dir, write_jsonl

try:
    from prefect import task
except Exception:  # noqa: BLE001
    def task(*args, **kwargs):  # type: ignore
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        def decorator(func):
            return func
        return decorator


def _existing_ref_course_ids(ref_root: Path) -> set[str]:
    by_course_root = ref_root / "current" / "by_course"
    if not by_course_root.exists():
        return set()
    return {path.name for path in by_course_root.iterdir() if path.is_dir()}


@task
def run_standardization(context, config):
    courses, errors = iter_courses(config.input_root)
    selected = courses
    skipped_existing_course_ids: list[str] = []
    selected_after_course_id_filter = len(selected)
    if config.course_ids:
        allowed = {course_id.strip() for course_id in config.course_ids if course_id.strip()}
        selected = [course for course in selected if course.course_id in allowed]
        selected_after_course_id_filter = len(selected)
    if config.skip_existing_ref_courses:
        existing_course_ids = _existing_ref_course_ids(context.ref_root)
        skipped_existing_course_ids = sorted(
            [course.course_id for course in selected if course.course_id in existing_course_ids]
        )
        selected = [course for course in selected if course.course_id not in existing_course_ids]
    offset = max(config.offset, 0)
    if offset:
        selected = selected[offset:]
    if config.max_courses:
        selected = selected[: config.max_courses]

    standardized_exports = ensure_dir(context.standardized_dir / "standardized_courses")
    course_rows = []
    chapter_rows = []
    for course in selected:
        payload = course.model_dump(mode="json")
        course_rows.append(payload)
        (standardized_exports / f"{course.course_id}.yaml").write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
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
        "courses": context.run_root / "courses.jsonl",
        "chapters": context.run_root / "chapters.jsonl",
        "standardized_courses": standardized_exports,
        "errors": context.standardized_dir / "errors.jsonl",
    }
    stage_outputs = {
        "courses": context.standardized_dir / "courses.jsonl",
        "chapters": context.standardized_dir / "chapters.jsonl",
    }
    write_jsonl(outputs["courses"], course_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(stage_outputs["courses"], course_rows)
    write_jsonl(stage_outputs["chapters"], chapter_rows)
    write_jsonl(outputs["errors"], errors)
    return {
        "courses": selected,
        "selected_course_ids": [course.course_id for course in selected],
        "skipped_existing_course_ids": skipped_existing_course_ids,
        "selection_counts": {
            "available_courses": len(courses),
            "after_course_id_filter": selected_after_course_id_filter,
            "skipped_existing_ref_courses": len(skipped_existing_course_ids),
            "offset": offset,
            "selected_courses": len(selected),
        },
        "errors": errors,
        "course_rows": course_rows,
        "chapter_rows": chapter_rows,
        "artifact_paths": list(outputs.values()) + list(stage_outputs.values()),
    }
