from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.question_gen_v3.models import TopicNode
from course_pipeline.question_gen_v4_1.run_v4_1_policy import (
    load_v3_course_artifacts,
    run_question_gen_v4_1_policy,
)
from course_pipeline.question_ledger_v6.build_ledger import (
    build_anchor_summaries,
    build_inspection_report,
    build_ledger_rows,
    derive_views,
)
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.utils import ensure_dir, slugify, write_jsonl


def build_question_ledger_v6_for_course(v3_payload: dict) -> dict:
    result = run_question_gen_v4_1_policy(v3_payload)
    topics_by_id: dict[str, TopicNode] = {topic.topic_id: topic for topic in v3_payload["topics"]}
    ledger_rows = build_ledger_rows(
        validated_correct_all=result["validated_correct_all"],
        hard_reject_records=result["hard_reject_records"],
        topics_by_id=topics_by_id,
    )
    views = derive_views(ledger_rows)
    anchor_summaries = build_anchor_summaries(ledger_rows)
    inspection_report = build_inspection_report(ledger_rows, anchor_summaries)
    return {
        "all_questions": ledger_rows,
        "visible_curated": views["visible_curated"],
        "cache_servable": views["cache_servable"],
        "aliases": views["aliases"],
        "anchor_summaries": anchor_summaries,
        "inspection_report": inspection_report,
        "v4_1_result": result,
    }


def write_v6_run_report(run_dir: Path, per_course: dict[str, dict]) -> Path:
    lines = ["# Question Ledger V6 Report", ""]
    for course_id, result in per_course.items():
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- all questions: {len(result['all_questions'])}")
        lines.append(f"- visible curated: {len(result['visible_curated'])}")
        lines.append(f"- cache-servable: {len(result['cache_servable'])}")
        lines.append(f"- aliases: {len(result['aliases'])}")
        lines.append(
            "- anchors with non-pass coverage: "
            f"{sum(1 for row in result['anchor_summaries'] if row.coverage_status != 'PASS')}"
        )
        lines.append("")
    path = run_dir / "question_ledger_v6_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_v6_review_bundle(
    run_dir: Path,
    courses: list[NormalizedCourse],
    per_course: dict[str, dict],
) -> dict[str, Path]:
    bundle_dir = ensure_dir(run_dir / "review_bundle")
    for course in courses:
        result = per_course[course.course_id]
        lines = [
            f"# {course.title} (`{course.course_id}`)",
            "",
            "## Ledger Summary",
            "",
            f"- all questions: {len(result['all_questions'])}",
            f"- visible curated: {len(result['visible_curated'])}",
            f"- cache-servable: {len(result['cache_servable'])}",
            f"- aliases: {len(result['aliases'])}",
            "",
            "## Inspection Report",
            "",
            result["inspection_report"].strip(),
            "",
        ]
        (bundle_dir / f"{course.course_id}_{slugify(course.title)}.md").write_text(
            "\n".join(lines).rstrip() + "\n",
            encoding="utf-8",
        )
    return {"review_bundle": bundle_dir}
