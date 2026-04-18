from __future__ import annotations

from course_pipeline.schemas import NormalizedCourse
from course_pipeline.question_gen_v3.models import CanonicalDocument, Section


def normalize_document(raw_doc: NormalizedCourse) -> CanonicalDocument:
    sections: list[Section] = []
    for chapter in raw_doc.chapters:
        sections.append(
            Section(
                section_index=chapter.chapter_index,
                title=chapter.title,
                summary=chapter.summary or "",
                source="explicit" if chapter.source == "syllabus" else "inferred",
            )
        )
    if not sections:
        sections.append(
            Section(
                section_index=1,
                title=raw_doc.title,
                summary=(raw_doc.overview or raw_doc.summary or "").strip(),
                source="inferred",
            )
        )
    tooling = []
    if raw_doc.provider:
        tooling.append(raw_doc.provider)
    tooling.extend([subject for subject in raw_doc.subjects if subject in {"R Programming", "Python", "SQL", "Time Series Analysis"}])
    return CanonicalDocument(
        doc_id=raw_doc.course_id,
        title=raw_doc.title,
        summary=raw_doc.summary or "",
        overview=raw_doc.overview or "",
        level=raw_doc.level,
        tooling=tooling,
        subjects=raw_doc.subjects,
        sections=sections,
    )
