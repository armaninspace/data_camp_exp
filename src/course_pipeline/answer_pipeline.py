from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.answer_generate_llm import generate_answers_with_llm
from course_pipeline.answer_validate_llm import build_review_answers, validate_answers_with_llm
from course_pipeline.config import Settings
from course_pipeline.questions.policy.models import CandidateRecord
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.utils import ensure_dir, write_jsonl, write_yaml


def run_answer_generation_for_course(
    *,
    course: NormalizedCourse,
    candidate_rows: list[CandidateRecord],
    settings: Settings | None,
    run_dir: Path | None,
) -> dict:
    generated_answers, generation_payload = generate_answers_with_llm(
        settings=settings,
        run_dir=run_dir,
        course=course,
        candidate_rows=candidate_rows,
    )
    validation_records, validation_payload = validate_answers_with_llm(
        settings=settings,
        run_dir=run_dir,
        course=course,
        candidate_rows=candidate_rows,
        generated_answers=generated_answers,
    )
    review_answers = build_review_answers(generated_answers, validation_records)
    return {
        "generated_answers": generated_answers,
        "answer_validation_logs": validation_records,
        "review_answers": review_answers,
        "answer_generate_payload": generation_payload,
        "answer_validate_payload": validation_payload,
    }


def write_answer_artifacts(run_dir: Path, course_id: str, result: dict, *, base_dir: Path | None = None) -> Path:
    target_root = ensure_dir(base_dir or (run_dir / "course_artifacts" / course_id))
    write_jsonl(
        target_root / "generated_answers.jsonl",
        [item.model_dump(mode="json") for item in result["generated_answers"]],
    )
    write_jsonl(
        target_root / "answer_validation_logs.jsonl",
        [item.model_dump(mode="json") for item in result["answer_validation_logs"]],
    )
    write_jsonl(
        target_root / "review_answers.jsonl",
        [item.model_dump(mode="json") for item in result["review_answers"]],
    )
    yaml_dir = ensure_dir(target_root / "answer_yaml")
    payload = {
        "course_id": course_id,
        "generated_answers": [item.model_dump(mode="json") for item in result["generated_answers"]],
        "answer_validation_logs": [item.model_dump(mode="json") for item in result["answer_validation_logs"]],
    }
    write_yaml(yaml_dir / f"{course_id}.yaml", payload, width=100)
    return target_root


def write_answer_run_summary(run_dir: Path, per_course: dict[str, dict]) -> Path:
    lines = ["# Answer Generation Report", ""]
    for course_id, result in per_course.items():
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- generated answers: {len(result['generated_answers'])}")
        accepted = sum(1 for item in result["answer_validation_logs"] if item.validation_status == "accepted")
        lines.append(f"- accepted answers: {accepted}")
        lines.append(f"- rejected answers: {len(result['answer_validation_logs']) - accepted}")
        lines.append("")
    path = run_dir / "answer_generation_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_answer_aggregate_artifacts(run_dir: Path, per_course: dict[str, dict]) -> dict[str, Path]:
    generated_rows: list[dict] = []
    validation_rows: list[dict] = []
    review_rows: list[dict] = []
    for course_id, result in per_course.items():
        generated_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["generated_answers"])
        validation_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["answer_validation_logs"])
        review_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["review_answers"])
    outputs = {
        "generated_answers": run_dir / "generated_answers.jsonl",
        "answer_validation_logs": run_dir / "answer_validation_logs.jsonl",
        "review_answers": run_dir / "review_answers.jsonl",
        "report": run_dir / "answer_generation_report.md",
    }
    write_jsonl(outputs["generated_answers"], generated_rows)
    write_jsonl(outputs["answer_validation_logs"], validation_rows)
    write_jsonl(outputs["review_answers"], review_rows)
    write_answer_run_summary(run_dir, per_course)
    return outputs
