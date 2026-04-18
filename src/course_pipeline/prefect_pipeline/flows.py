from __future__ import annotations

from course_pipeline.prefect_pipeline.artifacts import publish_markdown
from course_pipeline.prefect_pipeline.artifacts import build_artifact_index_entries
from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary
from course_pipeline.prefect_pipeline.states import StrictCoverageError
from course_pipeline.prefect_pipeline.tasks.bundles import render_bundle
from course_pipeline.prefect_pipeline.tasks.candidates import run_candidate_generation
from course_pipeline.prefect_pipeline.tasks.finalize import finalize_run_manifest
from course_pipeline.prefect_pipeline.tasks.ledger import build_ledger
from course_pipeline.prefect_pipeline.tasks.policy import run_policy
from course_pipeline.prefect_pipeline.tasks.prepare import prepare_run_context
from course_pipeline.prefect_pipeline.tasks.promote import promote_reference_data
from course_pipeline.prefect_pipeline.tasks.standardize import run_standardization
from course_pipeline.prefect_pipeline.tasks.semantics import run_semantics
from course_pipeline.prefect_pipeline.tasks.views import derive_views

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
    artifact_index: list[dict[str, str | int | None]] = []
    stage_summaries = []
    stage_summaries.append(
        StageSummary(
            stage_name="prepare_run_context",
            started_at=context.started_at,
            finished_at=context.started_at,
            duration_seconds=0.0,
            status="completed",
            artifact_paths=[str(context.manifest_path)],
            metrics={"strict_mode": context.strict_mode},
        )
    )
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
    blocking_failure = None
    status = "completed"
    promoted_ref = False
    try:
        standardized_result = run_standardization(context, config)
        stage_summaries.append(
            StageSummary(
                stage_name="standardize_courses",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                input_count=len(standardized_result["courses"]),
                output_count=len(standardized_result["course_rows"]),
                artifact_paths=[str(path) for path in standardized_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("standardize_courses", standardized_result["artifact_paths"], context.run_root))

        semantics_result = run_semantics(context, standardized_result)
        stage_summaries.append(
            StageSummary(
                stage_name="extract_semantics",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                input_count=len(standardized_result["courses"]),
                output_count=semantics_result["topic_count"],
                artifact_paths=[str(path) for path in semantics_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("extract_semantics", semantics_result["artifact_paths"], context.run_root))

        candidate_result = run_candidate_generation(context, standardized_result, semantics_result)
        stage_summaries.append(
            StageSummary(
                stage_name="generate_candidates",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                input_count=len(standardized_result["courses"]),
                output_count=candidate_result["candidate_count"],
                artifact_paths=[str(path) for path in candidate_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("generate_candidates", candidate_result["artifact_paths"], context.run_root))

        policy_result = run_policy(context, standardized_result, candidate_result)
        if context.strict_mode and policy_result["warning_messages"]:
            raise StrictCoverageError("; ".join(policy_result["warning_messages"]))
        stage_summaries.append(
            StageSummary(
                stage_name="apply_policy",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                input_count=len(standardized_result["courses"]),
                output_count=policy_result["warning_count"],
                warnings=policy_result["warning_messages"],
                artifact_paths=[str(path) for path in policy_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("apply_policy", policy_result["artifact_paths"], context.run_root))

        ledger_result = build_ledger(context, standardized_result, candidate_result, policy_result)
        stage_summaries.append(
            StageSummary(
                stage_name="build_ledger",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                input_count=len(standardized_result["courses"]),
                output_count=ledger_result["all_count"],
                artifact_paths=[str(path) for path in ledger_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("build_ledger", ledger_result["artifact_paths"], context.run_root))

        views_result = derive_views(context, ledger_result)
        stage_summaries.append(
            StageSummary(
                stage_name="derive_views",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                output_count=views_result["visible_count"],
                artifact_paths=[str(path) for path in views_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("derive_views", views_result["artifact_paths"], context.run_root))

        bundle_result = render_bundle(context, standardized_result, ledger_result)
        stage_summaries.append(
            StageSummary(
                stage_name="render_inspection_bundle",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed",
                artifact_paths=[str(path) for path in bundle_result["artifact_paths"]],
            )
        )
        artifact_index.extend(build_artifact_index_entries("render_inspection_bundle", bundle_result["artifact_paths"], context.run_root))

        promotion_result = promote_reference_data(context, standardized_result, ledger_result)
        promoted_ref = bool(promotion_result["promoted"])
        stage_summaries.append(
            StageSummary(
                stage_name="promote_ref_data",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="completed" if promoted_ref else "skipped",
                output_count=promotion_result["course_count"],
                warnings=[] if promoted_ref else [str(promotion_result["reason"])],
                artifact_paths=[str(path) for path in promotion_result["artifact_paths"]],
                metrics={"promoted_ref": promoted_ref, "run_mode": context.run_mode},
            )
        )
        artifact_index.extend(build_artifact_index_entries("promote_ref_data", promotion_result["artifact_paths"], context.run_root))
    except Exception as exc:  # noqa: BLE001
        status = "failed"
        blocking_failure = str(exc)
        stage_summaries.append(
            StageSummary(
                stage_name="failed",
                started_at=context.started_at,
                finished_at=context.started_at,
                duration_seconds=0.0,
                status="failed",
                warnings=[blocking_failure],
            )
        )
    publish_markdown(
        key=f"{context.run_id}-stage-table",
        markdown="\n".join(
            [
                "# Stage Summary",
                "",
                "| Stage | Status | Warnings |",
                "|---|---|---|",
                *[
                    f"| {stage.stage_name} | {stage.status} | {len(stage.warnings)} |"
                    for stage in stage_summaries
                ],
            ]
        ),
    )
    return finalize_run_manifest(
        context=context,
        stage_summaries=stage_summaries,
        artifact_index=artifact_index,
        status=status,
        blocking_failure=blocking_failure,
        promoted_ref=promoted_ref,
        selection_metadata={
            "selected_course_ids": standardized_result.get("selected_course_ids", []) if "standardized_result" in locals() else [],
            "skipped_existing_course_ids": standardized_result.get("skipped_existing_course_ids", []) if "standardized_result" in locals() else [],
            "selection_counts": standardized_result.get("selection_counts", {}) if "standardized_result" in locals() else {},
        },
    )
