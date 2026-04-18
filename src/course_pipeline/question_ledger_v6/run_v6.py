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
        lines = _render_course_bundle(course, result)
        (bundle_dir / f"{course.course_id}_{slugify(course.title)}.md").write_text(
            "\n".join(lines).rstrip() + "\n",
            encoding="utf-8",
        )
    return {"review_bundle": bundle_dir}


def _render_course_bundle(course: NormalizedCourse, result: dict) -> list[str]:
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
        "## All Questions",
        "",
    ]
    for row in result["all_questions"]:
        lines.extend(_render_ledger_row(row))
    lines.extend(
        [
            "## Course Content",
            "",
            "### Summary",
            "",
            course.summary.strip() if course.summary else "_None_",
            "",
            "### Overview",
            "",
            course.overview.strip() if course.overview else "_None_",
            "",
            "### Syllabus",
            "",
        ]
    )
    if course.chapters:
        for chapter in course.chapters:
            lines.append(f"- Chapter {chapter.chapter_index}: {chapter.title}")
            lines.append(f"  summary: {chapter.summary}")
    else:
        lines.append("_None_")
    lines.extend(
        [
            "",
            "## Inspection Report",
            "",
            result["inspection_report"].strip(),
            "",
        ]
    )
    return lines


def _render_ledger_row(row) -> list[str]:
    scores_json = json.dumps(row.scores.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    source_refs_json = json.dumps(row.source_refs, ensure_ascii=False)
    non_visible_json = json.dumps(row.non_visible_reasons, ensure_ascii=False)
    reject_reasons_json = json.dumps(row.reject_reasons, ensure_ascii=False)
    tags_json = json.dumps(row.tags, ensure_ascii=False)
    answer_text = row.answer_text.strip() if row.answer_text else ""
    canonical_target = row.canonical_target if row.canonical_target else "null"
    return [
        f"### {row.question_text}",
        "",
        f"- question_id: {row.question_id}",
        f"- anchor_id: {row.anchor_id}",
        f"- anchor_label: {row.anchor_label}",
        f"- tracked_topics: {json.dumps(row.tracked_topics, ensure_ascii=False)}",
        f"- anchor_type: {row.anchor_type}",
        f"- question_family: {row.question_family}",
        f"- question_type: {row.question_type}",
        f"- mastery_band: {row.mastery_band}",
        f"- canonical: {str(row.canonical).lower()}",
        f"- alias: {str(row.alias).lower()}",
        f"- canonical_target: {canonical_target}",
        f"- required_entry: {str(row.required_entry).lower()}",
        f"- validated_correct: {str(row.validated_correct).lower()}",
        f"- grounded: {str(row.grounded).lower()}",
        f"- serviceable: {str(row.serviceable).lower()}",
        f"- delivery_class: {row.delivery_class}",
        f"- visible: {str(row.visible).lower()}",
        f"- non_visible_reasons: {non_visible_json}",
        f"- reject_reasons: {reject_reasons_json}",
        f"- tags: {tags_json}",
        f"- scores: {scores_json}",
        f"- source_refs: {source_refs_json}",
        f"- answer_text: {answer_text if answer_text else 'null'}",
        "",
    ]
