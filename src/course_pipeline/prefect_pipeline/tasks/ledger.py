from __future__ import annotations

import json

from course_pipeline.question_gen_v3.models import TopicNode
from course_pipeline.question_ledger_v6.build_ledger import (
    build_anchor_summaries,
    build_inspection_report,
    build_ledger_rows,
    derive_views,
)
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
def build_ledger(context, standardized_result, candidate_result, policy_result):
    per_course: dict[str, dict] = {}
    all_rows: list[dict] = []
    inspection_sections: list[str] = []

    for course in standardized_result["courses"]:
        v3_payload = candidate_result["per_course"][course.course_id]
        v4_result = policy_result["per_course"][course.course_id]
        topics_by_id: dict[str, TopicNode] = {topic.topic_id: topic for topic in v3_payload["topics"]}
        ledger_rows = build_ledger_rows(
            validated_correct_all=v4_result["validated_correct_all"],
            hard_reject_records=v4_result["hard_reject_records"],
            topics_by_id=topics_by_id,
        )
        views = derive_views(ledger_rows)
        anchor_summaries = build_anchor_summaries(ledger_rows)
        inspection_report = build_inspection_report(ledger_rows, anchor_summaries)
        result = {
            "all_questions": ledger_rows,
            "visible_curated": views["visible_curated"],
            "cache_servable": views["cache_servable"],
            "aliases": views["aliases"],
            "anchor_summaries": anchor_summaries,
            "inspection_report": inspection_report,
            "v4_1_result": v4_result,
        }
        per_course[course.course_id] = result
        course_dir = ensure_dir(context.ledger_dir / "course_artifacts" / course.course_id)
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
        inspection_sections.append(f"# Course {course.course_id}\n\n{result['inspection_report'].strip()}\n")

    outputs = {
        "all_questions": context.run_root / "all_questions.jsonl",
        "ledger_all_questions": context.ledger_dir / "all_questions.jsonl",
        "inspection_report": context.ledger_dir / "inspection_report.md",
    }
    write_jsonl(outputs["all_questions"], all_rows)
    write_jsonl(outputs["ledger_all_questions"], all_rows)
    outputs["inspection_report"].write_text("\n\n".join(section.strip() for section in inspection_sections).rstrip() + "\n", encoding="utf-8")
    return {
        "per_course": per_course,
        "artifact_paths": list(outputs.values()),
        "all_count": len(all_rows),
    }
