from __future__ import annotations

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


@task
def run_standardization(context, config):
    courses, errors = iter_courses(config.input_root)
    selected = courses
    if config.course_ids:
        allowed = {course_id.strip() for course_id in config.course_ids if course_id.strip()}
        selected = [course for course in selected if course.course_id in allowed]
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
        "errors": errors,
        "course_rows": course_rows,
        "chapter_rows": chapter_rows,
        "artifact_paths": list(outputs.values()) + list(stage_outputs.values()),
    }
