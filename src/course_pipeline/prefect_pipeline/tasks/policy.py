from __future__ import annotations

import json

from course_pipeline.questions.policy.config_coverage import load_default_config
from course_pipeline.questions.policy import build_cache_entries, run_policy_stage
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
def run_policy(context, standardized_result, candidate_result):
    per_course: dict[str, dict] = {}
    validated_rows: list[dict] = []
    visible_rows: list[dict] = []
    hidden_rows: list[dict] = []
    warning_rows: list[dict] = []
    canonical_rows: list[dict] = []
    cache_entry_rows: list[dict] = []
    reject_rows: list[dict] = []
    metrics_rows: list[dict] = []

    for course in standardized_result["courses"]:
        v3_payload = candidate_result["per_course"][course.course_id]
        policy_config = load_default_config()
        policy_config.setdefault("coverage_audit", {})["strict_mode"] = context.strict_mode
        result = run_policy_stage(v3_payload, policy_config)
        scored_by_id = {row.candidate.candidate_id: row for row in v3_payload["scored_candidates"]}
        cache_entries = build_cache_entries(
            candidates_by_id=scored_by_id,
            decisions=result["policy_decisions"],
            answers_by_candidate_id={},
            alias_ids_by_canonical=result["alias_ids_by_canonical"],
        )
        result["cache_entries"] = cache_entries
        per_course[course.course_id] = result

        course_dir = ensure_dir(context.policy_dir / "course_artifacts" / course.course_id)
        write_jsonl(course_dir / "validated_correct_all.jsonl", [item.model_dump(mode="json") for item in result["validated_correct_all"]])
        write_jsonl(course_dir / "visible_curated.jsonl", [item.model_dump(mode="json") for item in result["visible_curated"]])
        write_jsonl(course_dir / "hidden_correct.jsonl", [item.model_dump(mode="json") for item in result["hidden_correct"]])
        write_jsonl(course_dir / "coverage_warnings.jsonl", [item.model_dump(mode="json") for item in result["coverage_warnings"]])
        write_jsonl(course_dir / "canonical_groups.jsonl", [item.model_dump(mode="json") for item in result["canonical_groups"]])
        write_jsonl(course_dir / "cache_entries.jsonl", [item.model_dump(mode="json") for item in cache_entries])
        write_jsonl(course_dir / "hard_reject_records.jsonl", [item.model_dump(mode="json") for item in result["hard_reject_records"]])
        (course_dir / "hard_reject_audit_summary.json").write_text(
            json.dumps(result["hard_reject_audit_summary"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (course_dir / "policy_metrics.json").write_text(
            json.dumps(result["metrics"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        validated_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["validated_correct_all"])
        visible_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["visible_curated"])
        hidden_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["hidden_correct"])
        warning_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["coverage_warnings"])
        canonical_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["canonical_groups"])
        cache_entry_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in cache_entries)
        reject_rows.extend(item.model_dump(mode="json") | {"course_id": course.course_id} for item in result["hard_reject_records"])
        metrics_rows.append({"course_id": course.course_id, **result["metrics"], **result["hard_reject_audit_summary"]})

    outputs = {
        "validated_correct_all": context.policy_dir / "validated_correct_all.jsonl",
        "visible_curated": context.policy_dir / "visible_curated.jsonl",
        "hidden_correct": context.policy_dir / "hidden_correct.jsonl",
        "coverage_warnings": context.policy_dir / "coverage_warnings.jsonl",
        "canonical_groups": context.policy_dir / "canonical_groups.jsonl",
        "cache_entries": context.policy_dir / "cache_entries.jsonl",
        "hard_reject_records": context.policy_dir / "hard_reject_records.jsonl",
        "policy_metrics": context.policy_dir / "policy_metrics.jsonl",
    }
    write_jsonl(outputs["validated_correct_all"], validated_rows)
    write_jsonl(outputs["visible_curated"], visible_rows)
    write_jsonl(outputs["hidden_correct"], hidden_rows)
    write_jsonl(outputs["coverage_warnings"], warning_rows)
    write_jsonl(outputs["canonical_groups"], canonical_rows)
    write_jsonl(outputs["cache_entries"], cache_entry_rows)
    write_jsonl(outputs["hard_reject_records"], reject_rows)
    write_jsonl(outputs["policy_metrics"], metrics_rows)
    warnings = [
        warning["message"]
        for warning in warning_rows
        if warning["warning_type"] in {
            "missing_visible_canonical_entry",
            "only_hidden_correct_entry_exists",
            "only_alias_entry_exists",
            "definition_generation_failed",
        }
    ]
    return {
        "per_course": per_course,
        "artifact_paths": list(outputs.values()),
        "warning_messages": warnings,
        "warning_count": len(warning_rows),
    }
