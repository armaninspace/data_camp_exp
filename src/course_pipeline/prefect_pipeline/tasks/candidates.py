from __future__ import annotations

from course_pipeline.questions.candidates import write_candidate_run_report
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
def run_candidate_generation(context, standardized_result, semantics_result):
    raw_candidate_rows: list[dict] = []
    rejected_rows: list[dict] = []
    scored_rows: list[dict] = []
    duplicate_rows: list[dict] = []
    final_rows: list[dict] = []
    summary_rows: list[dict] = []

    for course in standardized_result["courses"]:
        result = semantics_result["per_course"][course.course_id]
        course_dir = ensure_dir(context.candidates_dir / "course_artifacts" / course.course_id)
        write_jsonl(course_dir / "raw_candidates.jsonl", [item.model_dump(mode="json") for item in result["raw_candidates"]])
        write_jsonl(course_dir / "rejected_candidates.jsonl", [item.model_dump(mode="json") for item in result["rejected_candidates"]])
        write_jsonl(course_dir / "scored_candidates.jsonl", [item.model_dump(mode="json") for item in result["scored_candidates"]])
        write_jsonl(course_dir / "duplicate_clusters.jsonl", [item.model_dump(mode="json") for item in result["duplicate_clusters"]])
        write_jsonl(course_dir / "final_selected.jsonl", [item.model_dump(mode="json") for item in result["final_selected"]])
        raw_candidate_rows.extend(item.model_dump(mode="json") for item in result["raw_candidates"])
        rejected_rows.extend(item.model_dump(mode="json") for item in result["rejected_candidates"])
        scored_rows.extend(item.model_dump(mode="json") for item in result["scored_candidates"])
        duplicate_rows.extend(item.model_dump(mode="json") for item in result["duplicate_clusters"])
        final_rows.extend(item.model_dump(mode="json") for item in result["final_selected"])
        summary_rows.append(result["selection_summary"].model_dump(mode="json") | {"course_id": course.course_id})

    outputs = {
        "raw_candidates": context.candidates_dir / "raw_candidates.jsonl",
        "rejected_candidates": context.candidates_dir / "rejected_candidates.jsonl",
        "scored_candidates": context.candidates_dir / "scored_candidates.jsonl",
        "duplicate_clusters": context.candidates_dir / "duplicate_clusters.jsonl",
        "final_selected": context.candidates_dir / "final_selected.jsonl",
        "selection_summaries": context.candidates_dir / "selection_summaries.jsonl",
    }
    write_jsonl(outputs["raw_candidates"], raw_candidate_rows)
    write_jsonl(outputs["rejected_candidates"], rejected_rows)
    write_jsonl(outputs["scored_candidates"], scored_rows)
    write_jsonl(outputs["duplicate_clusters"], duplicate_rows)
    write_jsonl(outputs["final_selected"], final_rows)
    write_jsonl(outputs["selection_summaries"], summary_rows)
    write_candidate_run_report(context.candidates_dir, semantics_result["per_course"])
    return {
        "per_course": semantics_result["per_course"],
        "artifact_paths": list(outputs.values()) + [context.candidates_dir / "question_gen_v3_report.md"],
        "candidate_count": len(scored_rows),
    }
