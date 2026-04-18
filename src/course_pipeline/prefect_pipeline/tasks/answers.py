from __future__ import annotations

from course_pipeline.answer_pipeline import run_answer_generation_for_course, write_answer_aggregate_artifacts, write_answer_artifacts
from course_pipeline.config import get_settings

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
def run_answer_generation(context, standardized_result, policy_result):
    if not context.enable_answer_generation:
        return {"per_course": {}, "artifact_paths": [], "answer_count": 0, "status": "skipped_disabled"}

    settings = get_settings()
    if not settings.openai_api_key:
        return {"per_course": {}, "artifact_paths": [], "answer_count": 0, "status": "skipped_no_openai_key"}

    per_course: dict[str, dict] = {}
    for course in standardized_result["courses"]:
        result = policy_result["per_course"].get(course.course_id)
        if not result:
            continue
        course_answers = run_answer_generation_for_course(
            course=course,
            candidate_rows=result["validated_correct_all"],
            settings=settings,
            run_dir=context.run_root,
        )
        per_course[course.course_id] = course_answers
        write_answer_artifacts(
            context.answer_dir,
            course.course_id,
            course_answers,
            base_dir=context.answer_dir / "course_artifacts" / course.course_id,
        )

    outputs = write_answer_aggregate_artifacts(context.answer_dir, per_course)
    return {
        "per_course": per_course,
        "artifact_paths": list(outputs.values()),
        "answer_count": sum(len(result["generated_answers"]) for result in per_course.values()),
        "status": "completed",
    }
