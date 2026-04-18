from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from course_pipeline.utils import ensure_dir, write_jsonl


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def promote_ref_data(context, standardized_result, ledger_result) -> dict:
    if context.run_mode != "prod" or not context.promote_ref:
        return {
            "promoted": False,
            "artifact_paths": [],
            "course_count": len(standardized_result["courses"]),
            "reason": "promotion_disabled_for_run_mode",
        }

    ref_root = ensure_dir(context.ref_root)
    current_root = ensure_dir(ref_root / "current")
    by_course_root = ensure_dir(current_root / "by_course")
    aggregate_root = ensure_dir(current_root / "aggregate")
    aggregate_bundle_root = aggregate_root / "inspection_bundle"
    final_deliverables_root = ensure_dir(current_root / "final_deliverables")
    promotions_root = ensure_dir(ref_root / "promotions")

    touched_course_ids: list[str] = []
    for course in standardized_result["courses"]:
        course_result = ledger_result["per_course"][course.course_id]
        course_dir = ensure_dir(by_course_root / course.course_id)
        touched_course_ids.append(course.course_id)

        course_payload = course.model_dump(mode="json")
        chapter_rows = [
            {
                "course_id": course.course_id,
                "course_title": course.title,
                **chapter.model_dump(mode="json"),
            }
            for chapter in course.chapters
        ]

        (course_dir / "course.json").write_text(
            json.dumps(course_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (course_dir / "chapters.json").write_text(
            json.dumps(chapter_rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_jsonl(course_dir / "all_questions.jsonl", [item.model_dump(mode="json") for item in course_result["all_questions"]])
        write_jsonl(course_dir / "visible_curated.jsonl", [item.model_dump(mode="json") for item in course_result["visible_curated"]])
        write_jsonl(course_dir / "cache_servable.jsonl", [item.model_dump(mode="json") for item in course_result["cache_servable"]])
        write_jsonl(course_dir / "aliases.jsonl", [item.model_dump(mode="json") for item in course_result["aliases"]])
        (course_dir / "anchors_summary.json").write_text(
            json.dumps([item.model_dump(mode="json") for item in course_result["anchor_summaries"]], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (course_dir / "inspection_report.md").write_text(course_result["inspection_report"], encoding="utf-8")

        bundle_path = context.bundle_dir / f"{course.course_id}_{course.title.lower().replace(' ', '-').replace('/', '-')}.md"
        if not bundle_path.exists():
            candidates = sorted(context.bundle_dir.glob(f"{course.course_id}_*.md"))
            if candidates:
                bundle_path = candidates[0]
        if bundle_path.exists():
            (course_dir / "inspection_bundle.md").write_text(bundle_path.read_text(encoding="utf-8"), encoding="utf-8")

    if aggregate_bundle_root.exists():
        shutil.rmtree(aggregate_bundle_root)
    ensure_dir(aggregate_bundle_root)

    courses_rows: list[dict] = []
    chapter_rows: list[dict] = []
    all_question_rows: list[dict] = []
    visible_rows: list[dict] = []
    cache_rows: list[dict] = []
    alias_rows: list[dict] = []
    anchor_rows: list[dict] = []

    course_ids: list[str] = []
    for course_dir in sorted(path for path in by_course_root.iterdir() if path.is_dir()):
        course_payload = _read_json(course_dir / "course.json", {})
        if not course_payload:
            continue
        course_id = str(course_payload["course_id"])
        course_ids.append(course_id)
        courses_rows.append(course_payload)
        chapter_rows.extend(_read_json(course_dir / "chapters.json", []))
        all_question_rows.extend(row | {"course_id": course_id} for row in _read_jsonl(course_dir / "all_questions.jsonl"))
        visible_rows.extend(row | {"course_id": course_id} for row in _read_jsonl(course_dir / "visible_curated.jsonl"))
        cache_rows.extend(row | {"course_id": course_id} for row in _read_jsonl(course_dir / "cache_servable.jsonl"))
        alias_rows.extend(row | {"course_id": course_id} for row in _read_jsonl(course_dir / "aliases.jsonl"))
        anchor_rows.extend(row | {"course_id": course_id} for row in _read_json(course_dir / "anchors_summary.json", []))

        bundle_src = course_dir / "inspection_bundle.md"
        if bundle_src.exists():
            bundle_target = aggregate_bundle_root / f"{course_id}_{course_payload['title'].lower().replace(' ', '-').replace('/', '-')}.md"
            bundle_target.write_text(bundle_src.read_text(encoding="utf-8"), encoding="utf-8")

    outputs = {
        "courses": aggregate_root / "courses.jsonl",
        "chapters": aggregate_root / "chapters.jsonl",
        "all_questions": aggregate_root / "all_questions.jsonl",
        "visible_curated": aggregate_root / "visible_curated.jsonl",
        "cache_servable": aggregate_root / "cache_servable.jsonl",
        "aliases": aggregate_root / "aliases.jsonl",
        "anchors_summary": aggregate_root / "anchors_summary.json",
        "final_all_questions": final_deliverables_root / "all_questions.jsonl",
        "ref_state": current_root / "ref_state.json",
        "promotion_manifest": promotions_root / f"{context.run_id}.json",
    }
    write_jsonl(outputs["courses"], courses_rows)
    write_jsonl(outputs["chapters"], chapter_rows)
    write_jsonl(outputs["all_questions"], all_question_rows)
    write_jsonl(outputs["visible_curated"], visible_rows)
    write_jsonl(outputs["cache_servable"], cache_rows)
    write_jsonl(outputs["aliases"], alias_rows)
    outputs["anchors_summary"].write_text(json.dumps(anchor_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_jsonl(outputs["final_all_questions"], all_question_rows)

    prior_state = _read_json(outputs["ref_state"], {})
    promoted_run_ids = list(dict.fromkeys([*(prior_state.get("promoted_run_ids") or []), context.run_id]))
    ref_state = {
        "schema_version": 1,
        "updated_at": datetime.now(UTC).isoformat(),
        "last_promoted_run_id": context.run_id,
        "promoted_run_ids": promoted_run_ids,
        "course_ids": sorted(course_ids),
        "course_count": len(course_ids),
        "run_mode": context.run_mode,
        "current_root": str(current_root),
    }
    outputs["ref_state"].write_text(json.dumps(ref_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    promotion_manifest = {
        "run_id": context.run_id,
        "promoted_at": datetime.now(UTC).isoformat(),
        "run_mode": context.run_mode,
        "promoted": True,
        "touched_course_ids": sorted(touched_course_ids),
        "current_course_ids": sorted(course_ids),
        "aggregate_counts": {
            "courses": len(courses_rows),
            "chapters": len(chapter_rows),
            "all_questions": len(all_question_rows),
            "visible_curated": len(visible_rows),
            "cache_servable": len(cache_rows),
            "aliases": len(alias_rows),
            "anchors_summary": len(anchor_rows),
        },
    }
    outputs["promotion_manifest"].write_text(
        json.dumps(promotion_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "promoted": True,
        "artifact_paths": [*outputs.values(), aggregate_bundle_root],
        "course_count": len(courses_rows),
        "reason": None,
    }
