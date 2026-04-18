from __future__ import annotations

from course_pipeline.config import get_settings
from course_pipeline.semantic_pipeline import (
    run_semantic_stage_for_course,
    write_semantic_course_yaml,
    write_semantic_stage_artifacts,
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
def run_semantics(context, standardized_result):
    settings = get_settings()
    semantic_topic_rows: list[dict] = []
    semantic_anchor_rows: list[dict] = []
    semantic_alias_rows: list[dict] = []
    semantic_friction_rows: list[dict] = []
    topic_rows: list[dict] = []
    edge_rows: list[dict] = []
    pedagogy_rows: list[dict] = []
    friction_rows: list[dict] = []
    per_course: dict[str, dict] = {}

    for course in standardized_result["courses"]:
        result = run_semantic_stage_for_course(raw_course=course, settings=settings, run_dir=context.run_root)
        per_course[course.course_id] = result
        course_dir = ensure_dir(context.semantics_dir / "course_artifacts" / course.course_id)
        write_semantic_stage_artifacts(context.semantics_dir, course.course_id, result, base_dir=course_dir)
        write_semantic_course_yaml(context.semantics_dir, course.course_id, result, base_dir=course_dir)
        semantic_topic_rows.extend(item.model_dump(mode="json") for item in result["semantic_topic_records"])
        semantic_anchor_rows.extend(item.model_dump(mode="json") for item in result["semantic_anchor_candidates"])
        semantic_alias_rows.extend(item.model_dump(mode="json") for item in result["semantic_alias_groups"])
        semantic_friction_rows.extend(item.model_dump(mode="json") for item in result["semantic_friction_records"])
        topic_rows.extend(item.model_dump(mode="json") for item in result["topics"])
        edge_rows.extend(item.model_dump(mode="json") for item in result["edges"])
        pedagogy_rows.extend(item.model_dump(mode="json") for item in result["pedagogy"])
        friction_rows.extend(item.model_dump(mode="json") for item in result["frictions"])

    outputs = {
        "semantic_topics": context.semantics_dir / "semantic_topics.jsonl",
        "semantic_anchors": context.semantics_dir / "semantic_anchors.jsonl",
        "semantic_alias_groups": context.semantics_dir / "semantic_alias_groups.jsonl",
        "semantic_frictions": context.semantics_dir / "semantic_frictions.jsonl",
        "topics": context.semantics_dir / "topics.jsonl",
        "edges": context.semantics_dir / "edges.jsonl",
        "pedagogy": context.semantics_dir / "pedagogy.jsonl",
        "friction_points": context.semantics_dir / "friction_points.jsonl",
    }
    write_jsonl(outputs["semantic_topics"], semantic_topic_rows)
    write_jsonl(outputs["semantic_anchors"], semantic_anchor_rows)
    write_jsonl(outputs["semantic_alias_groups"], semantic_alias_rows)
    write_jsonl(outputs["semantic_frictions"], semantic_friction_rows)
    write_jsonl(outputs["topics"], topic_rows)
    write_jsonl(outputs["edges"], edge_rows)
    write_jsonl(outputs["pedagogy"], pedagogy_rows)
    write_jsonl(outputs["friction_points"], friction_rows)
    return {
        "per_course": per_course,
        "artifact_paths": list(outputs.values()),
        "topic_count": len(topic_rows),
    }
