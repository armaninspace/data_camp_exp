from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.answer_schemas import GeneratedAnswerRecord
from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.questions.policy.models import CandidateRecord
from course_pipeline.schemas import NormalizedCourse


ANSWER_GENERATE_SYSTEM_PROMPT = """You write short grounded learner answers for validated course questions.

Return JSON only.

Rules:
- Answer directly and briefly.
- Stay grounded in the supplied course fields and source refs.
- Do not invent unsupported steps, tools, or examples.
- If support is weak, return an empty answer for that item.
"""


def build_answer_generate_payload(course: NormalizedCourse, candidate_rows: list[CandidateRecord]) -> dict:
    return {
        "course": {
            "course_id": course.course_id,
            "title": course.title,
            "summary": course.summary,
            "overview": course.overview,
            "sections": [{"title": chapter.title, "summary": chapter.summary} for chapter in course.chapters],
        },
        "questions": [
            {
                "candidate_id": row.candidate_id,
                "question_text": row.question,
                "question_type": row.question_type,
                "mastery_band": row.mastery_band,
                "source_refs": row.source_refs,
            }
            for row in candidate_rows
        ],
    }


def generate_answers_with_llm(
    *,
    settings: Settings | None,
    run_dir: Path | None,
    course: NormalizedCourse,
    candidate_rows: list[CandidateRecord],
) -> tuple[list[GeneratedAnswerRecord], dict]:
    payload = build_answer_generate_payload(course, candidate_rows)
    if not settings or not settings.openai_api_key or run_dir is None:
        return [], payload
    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="answer_generate",
        prompt_version="answer_generate_v1",
    )
    try:
        content = client.invoke_json(
            ANSWER_GENERATE_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, indent=2),
            course_id=course.course_id,
            entity_ids=[item.candidate_id for item in candidate_rows],
        )
    except Exception:
        return [], payload
    return _parse_generated_answers(content, course.course_id, candidate_rows), payload


def _parse_generated_answers(content: str, course_id: str, candidate_rows: list[CandidateRecord]) -> list[GeneratedAnswerRecord]:
    payload = json.loads(content)
    candidate_by_id = {row.candidate_id: row for row in candidate_rows}
    records: list[GeneratedAnswerRecord] = []
    for item in payload.get("answers", []):
        candidate_id = str(item.get("candidate_id") or item.get("question_id") or "")
        candidate = candidate_by_id.get(candidate_id)
        if candidate is None:
            continue
        answer = (item.get("answer_markdown") or item.get("answer") or item.get("response") or "").strip()
        records.append(
            GeneratedAnswerRecord(
                course_id=course_id,
                candidate_id=candidate_id,
                question_text=candidate.question,
                answer_markdown=answer,
                source_refs=list(candidate.source_refs),
                generation_rationale=item.get("generation_rationale") or "llm_generated_answer",
                confidence=float(item.get("confidence") or 0.0),
                generated_by_llm=True,
            )
        )
    return records
