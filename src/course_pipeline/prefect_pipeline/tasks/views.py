from __future__ import annotations

import json

from course_pipeline.question_ledger_v6.run_v6 import write_v6_run_report
from course_pipeline.utils import write_jsonl

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
def derive_views(context, ledger_result):
    visible_rows: list[dict] = []
    cache_rows: list[dict] = []
    alias_rows: list[dict] = []
    anchor_summary_rows: list[dict] = []
    for course_id, result in ledger_result["per_course"].items():
        visible_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["visible_curated"])
        cache_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["cache_servable"])
        alias_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["aliases"])
        anchor_summary_rows.extend(item.model_dump(mode="json") | {"course_id": course_id} for item in result["anchor_summaries"])

    outputs = {
        "visible_curated": context.run_root / "visible_curated.jsonl",
        "cache_servable": context.run_root / "cache_servable.jsonl",
        "aliases": context.run_root / "aliases.jsonl",
        "anchors_summary": context.run_root / "anchors_summary.json",
        "report": context.run_root / "question_ledger_v6_report.md",
    }
    write_jsonl(outputs["visible_curated"], visible_rows)
    write_jsonl(outputs["cache_servable"], cache_rows)
    write_jsonl(outputs["aliases"], alias_rows)
    outputs["anchors_summary"].write_text(json.dumps(anchor_summary_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_v6_run_report(context.run_root, ledger_result["per_course"])
    return {
        "artifact_paths": list(outputs.values()),
        "visible_count": len(visible_rows),
    }
