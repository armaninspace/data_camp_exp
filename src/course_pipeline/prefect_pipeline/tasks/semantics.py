from __future__ import annotations

from course_pipeline.question_gen_v3.pipeline import run_question_gen_v3_for_course
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
def run_semantics(context, standardized_result):
    topic_rows: list[dict] = []
    edge_rows: list[dict] = []
    pedagogy_rows: list[dict] = []
    friction_rows: list[dict] = []
    per_course: dict[str, dict] = {}

    for course in standardized_result["courses"]:
        result = run_question_gen_v3_for_course(course)
        per_course[course.course_id] = result
        course_dir = ensure_dir(context.semantics_dir / "course_artifacts" / course.course_id)
        write_jsonl(course_dir / "topics.jsonl", [item.model_dump(mode="json") for item in result["topics"]])
        write_jsonl(course_dir / "edges.jsonl", [item.model_dump(mode="json") for item in result["edges"]])
        write_jsonl(course_dir / "pedagogy.jsonl", [item.model_dump(mode="json") for item in result["pedagogy"]])
        write_jsonl(course_dir / "friction_points.jsonl", [item.model_dump(mode="json") for item in result["frictions"]])
        topic_rows.extend(item.model_dump(mode="json") for item in result["topics"])
        edge_rows.extend(item.model_dump(mode="json") for item in result["edges"])
        pedagogy_rows.extend(item.model_dump(mode="json") for item in result["pedagogy"])
        friction_rows.extend(item.model_dump(mode="json") for item in result["frictions"])

    outputs = {
        "topics": context.semantics_dir / "topics.jsonl",
        "edges": context.semantics_dir / "edges.jsonl",
        "pedagogy": context.semantics_dir / "pedagogy.jsonl",
        "friction_points": context.semantics_dir / "friction_points.jsonl",
    }
    write_jsonl(outputs["topics"], topic_rows)
    write_jsonl(outputs["edges"], edge_rows)
    write_jsonl(outputs["pedagogy"], pedagogy_rows)
    write_jsonl(outputs["friction_points"], friction_rows)
    return {
        "per_course": per_course,
        "artifact_paths": list(outputs.values()),
        "topic_count": len(topic_rows),
    }
