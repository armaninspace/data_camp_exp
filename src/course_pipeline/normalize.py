from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

from course_pipeline.schemas import ChapterOut, NormalizedCourse
from course_pipeline.utils import slugify


LEVEL_MAP = {
    "beginner": "beginner",
    "introductory": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
}


def parse_duration_hours(value: str | None) -> float | None:
    if not value:
        return None
    text = value.lower()
    total = 0.0
    day_match = re.search(r"(\d+(?:\.\d+)?)\s+day", text)
    hour_match = re.search(r"(\d+(?:\.\d+)?)\s+hour", text)
    minute_match = re.search(r"(\d+(?:\.\d+)?)\s+minute", text)
    if day_match:
        total += float(day_match.group(1)) * 24
    if hour_match:
        total += float(hour_match.group(1))
    if minute_match:
        total += float(minute_match.group(1)) / 60
    return total or None


def normalize_level(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    for key, normalized in LEVEL_MAP.items():
        if key in text:
            return normalized
    return text or None


def clean_subjects(subjects: list[str] | None) -> list[str]:
    if not subjects:
        return []
    cleaned = []
    for subject in subjects:
        value = " ".join(str(subject).split()).strip()
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned


def infer_course_id(payload: dict, yaml_path: Path) -> str:
    for key in ("final_url", "source_url"):
        url = payload.get(key)
        if isinstance(url, str):
            match = re.search(r"-(\d+)$", url.rstrip("/"))
            if match:
                return match.group(1)
    return slugify(yaml_path.stem)


def recover_chapters(payload: dict) -> list[ChapterOut]:
    syllabus = payload.get("syllabus") or []
    chapters: list[ChapterOut] = []
    if isinstance(syllabus, list) and syllabus:
        for index, item in enumerate(syllabus, start=1):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            summary = item.get("summary")
            if title:
                chapters.append(
                    ChapterOut(
                        chapter_index=index,
                        title=title,
                        summary=str(summary).strip() if summary else None,
                        source="syllabus",
                        confidence=1.0,
                    )
                )
    if chapters:
        return chapters
    return infer_chapters_from_overview(str(payload.get("overview") or ""))


def infer_chapters_from_overview(overview: str) -> list[ChapterOut]:
    text = overview.strip()
    if not text:
        return []

    raw_lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in raw_lines if line]
    chapters: list[ChapterOut] = []
    current_title: str | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_parts
        if current_title:
            chapters.append(
                ChapterOut(
                    chapter_index=len(chapters) + 1,
                    title=current_title,
                    summary=" ".join(current_parts).strip() or None,
                    source="overview_inferred",
                    confidence=0.7,
                )
            )
        current_title = None
        current_parts = []

    for line in lines:
        heading = line.lstrip("#").strip()
        is_heading = line.startswith("#") or (
            len(heading.split()) <= 8
            and not heading.endswith(".")
            and heading[:1].isupper()
            and line == heading
        )
        if is_heading:
            flush()
            current_title = heading
            continue
        if current_title is None:
            current_title = "Overview"
        current_parts.append(line)
    flush()

    if len(chapters) == 1 and chapters[0].title == "Overview":
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            chapters = []
            for index, paragraph in enumerate(paragraphs, start=1):
                title = f"Overview Segment {index}"
                chapters.append(
                    ChapterOut(
                        chapter_index=index,
                        title=title,
                        summary=paragraph,
                        source="overview_inferred",
                        confidence=0.5,
                    )
                )
    return chapters


def load_course(yaml_path: Path) -> NormalizedCourse:
    payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{yaml_path} did not parse to a mapping")

    details = payload.get("details") or {}
    if not isinstance(details, dict):
        details = {}

    fetched_at = payload.get("fetched_at")
    parsed_fetched_at = None
    if isinstance(fetched_at, str):
        parsed_fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))

    course = NormalizedCourse(
        course_id=infer_course_id(payload, yaml_path),
        source_url=str(payload.get("source_url") or ""),
        final_url=str(payload.get("final_url")) if payload.get("final_url") else None,
        provider=str(payload.get("provider") or details.get("provider") or "unknown"),
        title=str(payload.get("title") or "").strip(),
        summary=str(payload.get("summary")).strip() if payload.get("summary") else None,
        overview=str(payload.get("overview")).strip() if payload.get("overview") else None,
        subjects=clean_subjects(payload.get("subjects")),
        level=normalize_level(details.get("level")),
        duration_hours=parse_duration_hours(details.get("duration_workload")),
        pricing=str(details.get("pricing")).strip() if details.get("pricing") else None,
        language=str(details.get("languages")).strip() if details.get("languages") else None,
        chapters=recover_chapters({**payload, "details": details}),
        raw_yaml_path=str(yaml_path),
        fetched_at=parsed_fetched_at,
        ratings=payload.get("ratings") or {},
        details=details,
    )
    if not course.source_url or not course.title:
        raise ValidationError.from_exception_data(
            "NormalizedCourse",
            [
                {"loc": ("source_url",), "msg": "source_url required", "type": "value_error"}
                if not course.source_url
                else {"loc": ("title",), "msg": "title required", "type": "value_error"}
            ],
        )
    return course


def iter_courses(input_dir: Path) -> tuple[list[NormalizedCourse], list[dict]]:
    courses: list[NormalizedCourse] = []
    errors: list[dict] = []
    for yaml_path in sorted(input_dir.glob("*.yaml")):
        try:
            courses.append(load_course(yaml_path))
        except Exception as exc:  # noqa: BLE001
            errors.append({"path": str(yaml_path), "error": str(exc)})
    return courses, errors

