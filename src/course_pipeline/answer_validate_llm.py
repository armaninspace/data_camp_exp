from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.answer_schemas import AnswerValidationRecord, GeneratedAnswerRecord, ReviewAnswerRecord
from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.questions.policy.models import CandidateRecord
from course_pipeline.schemas import NormalizedCourse


ANSWER_VALIDATE_SYSTEM_PROMPT = """You validate generated course answers for fit and grounding.

Return JSON only.

Rules:
- Reject empty or unsupported answers.
- Accept only answers grounded in the supplied course fields and source refs.
- Keep validation strict and conservative.
"""


def build_answer_validate_payload(
    course: NormalizedCourse,
    candidate_rows: list[CandidateRecord],
    generated_answers: list[GeneratedAnswerRecord],
) -> dict:
    candidate_by_id = {row.candidate_id: row for row in candidate_rows}
    return {
        "course": {
            "course_id": course.course_id,
            "title": course.title,
            "summary": course.summary,
            "overview": course.overview,
        },
        "answers": [
            {
                "candidate_id": record.candidate_id,
                "question_text": record.question_text,
                "answer_markdown": record.answer_markdown,
                "source_refs": candidate_by_id.get(record.candidate_id).source_refs if record.candidate_id in candidate_by_id else [],
            }
            for record in generated_answers
        ],
    }


def validate_answers_with_llm(
    *,
    settings: Settings | None,
    run_dir: Path | None,
    course: NormalizedCourse,
    candidate_rows: list[CandidateRecord],
    generated_answers: list[GeneratedAnswerRecord],
) -> tuple[list[AnswerValidationRecord], dict]:
    payload = build_answer_validate_payload(course, candidate_rows, generated_answers)
    if not generated_answers:
        return [], payload
    if not settings or not settings.openai_api_key or run_dir is None:
        return _fallback_validation(course.course_id, generated_answers), payload
    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="answer_validate",
        prompt_version="answer_validate_v1",
    )
    try:
        content = client.invoke_json(
            ANSWER_VALIDATE_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, indent=2),
            course_id=course.course_id,
            entity_ids=[item.candidate_id for item in generated_answers],
        )
    except Exception:
        return _fallback_validation(course.course_id, generated_answers), payload
    return _parse_validation(content, course.course_id, generated_answers), payload


def _fallback_validation(course_id: str, generated_answers: list[GeneratedAnswerRecord]) -> list[AnswerValidationRecord]:
    records: list[AnswerValidationRecord] = []
    for record in generated_answers:
        reasons: list[str] = []
        if not record.answer_markdown.strip():
            reasons.append("empty_answer")
        if len(record.answer_markdown.split()) < 4:
            reasons.append("answer_too_short")
        accepted = not reasons
        records.append(
            AnswerValidationRecord(
                course_id=course_id,
                candidate_id=record.candidate_id,
                validation_status="accepted" if accepted else "rejected",
                answer_fit_status="accepted" if accepted else "rejected",
                grounding_status="accepted" if accepted and record.source_refs else "rejected",
                reasons=reasons or (["accepted_deterministic_fallback"] if accepted else reasons),
                confidence=0.55 if accepted else 0.9,
            )
        )
    return records


def _parse_validation(content: str, course_id: str, generated_answers: list[GeneratedAnswerRecord]) -> list[AnswerValidationRecord]:
    payload = json.loads(content)
    answer_ids = {record.candidate_id for record in generated_answers}
    parsed: list[AnswerValidationRecord] = []
    for item in payload.get("validations", []):
        candidate_id = str(item.get("candidate_id") or "")
        if candidate_id not in answer_ids:
            continue
        status = "accepted" if item.get("validation_status") == "accepted" else "rejected"
        parsed.append(
            AnswerValidationRecord(
                course_id=course_id,
                candidate_id=candidate_id,
                validation_status=status,
                answer_fit_status="accepted" if item.get("answer_fit_status") == "accepted" else "rejected",
                grounding_status="accepted" if item.get("grounding_status") == "accepted" else "rejected",
                reasons=list(item.get("reasons") or []),
                confidence=float(item.get("confidence") or 0.0),
            )
        )
    parsed_ids = {record.candidate_id for record in parsed}
    fallback_needed = [record for record in generated_answers if record.candidate_id not in parsed_ids]
    return parsed + _fallback_validation(course_id, fallback_needed)


def build_review_answers(
    generated_answers: list[GeneratedAnswerRecord],
    validation_records: list[AnswerValidationRecord],
) -> list[ReviewAnswerRecord]:
    validation_by_id = {record.candidate_id: record for record in validation_records}
    review_rows: list[ReviewAnswerRecord] = []
    for record in generated_answers:
        validation = validation_by_id.get(record.candidate_id)
        if validation is None or validation.validation_status != "accepted":
            continue
        review_rows.append(
            ReviewAnswerRecord(
                course_id=record.course_id,
                candidate_id=record.candidate_id,
                question_text=record.question_text,
                answer_markdown=record.answer_markdown,
                validation_status="accepted",
            )
        )
    return review_rows
