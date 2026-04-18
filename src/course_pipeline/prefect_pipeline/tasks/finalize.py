from __future__ import annotations

from course_pipeline.prefect_pipeline.manifests import build_run_result
from course_pipeline.prefect_pipeline.models.run_context import RunContext
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary

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
def finalize_run_manifest(
    context: RunContext,
    stage_summaries: list[StageSummary],
    artifact_index: list[dict[str, str | int | None]],
    status: str,
    blocking_failure: str | None = None,
):
    return build_run_result(context, stage_summaries, artifact_index, status=status, blocking_failure=blocking_failure)
