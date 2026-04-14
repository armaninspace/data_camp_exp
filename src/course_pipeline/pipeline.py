from __future__ import annotations

from pathlib import Path

import yaml

from course_pipeline.config import Settings
from course_pipeline.normalize import iter_courses
from course_pipeline.schemas import NormalizedCourse
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
