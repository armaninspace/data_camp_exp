from __future__ import annotations

from course_pipeline.prefect_pipeline.artifacts import publish_markdown
from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary
from course_pipeline.prefect_pipeline.tasks.finalize import finalize_run_manifest
from course_pipeline.prefect_pipeline.tasks.prepare import prepare_run_context

try:
    from prefect import flow
except Exception:  # noqa: BLE001
    def flow(*args, **kwargs):  # type: ignore
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        def decorator(func):
            return func
        return decorator


@flow(name="question-generation-pipeline", log_prints=True)
def question_generation_pipeline_flow(config: RunConfig):
    context = prepare_run_context(config)
    stage_summaries = [
        StageSummary(
            stage_name="prepare_run_context",
            started_at=context.started_at,
            finished_at=context.started_at,
            duration_seconds=0.0,
            status="completed",
            artifact_paths=[str(context.manifest_path)],
        )
    ]
    publish_markdown(
        key=f"{context.run_id}-overview",
        markdown=(
            f"# Run Overview\n\n"
            f"- run_id: `{context.run_id}`\n"
            f"- strict_mode: `{context.strict_mode}`\n"
            f"- input_root: `{context.input_root}`\n"
            f"- output_root: `{context.output_root}`\n"
        ),
    )
    artifact_index: list[dict[str, str | int | None]] = []
    return finalize_run_manifest(
        context=context,
        stage_summaries=stage_summaries,
        artifact_index=artifact_index,
        status="completed",
        blocking_failure=None,
    )
