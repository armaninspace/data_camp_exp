from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.config import get_settings
from course_pipeline.bundle_builder import BundleBuildError, build_inspection_bundle
from course_pipeline.pipeline import (
    build_question_generation_v3_review_bundle,
    build_question_generation_v4_review_bundle,
    build_question_generation_v4_1_review_bundle,
    build_question_ledger_v6_review_bundle,
    export_standardized,
    inspect_question_refine_run,
    inspect_semantic_run,
    ingest_all,
    run_pipeline_refactor,
    run_question_expand_stage,
    run_question_ledger_v6,
    run_question_generation_v3,
    run_question_repair_stage,
    run_question_generation_v4_policy,
    run_question_generation_v4_1_policy,
    run_question_seed_generation_stage,
    run_semantic_extract_llm_stage,
)
from course_pipeline.storage import Storage


app = typer.Typer(no_args_is_help=True)


@app.command("init-db")
def init_db() -> None:
    settings = get_settings()
    storage = Storage(settings)
    storage.init_db()
    typer.echo(f"initialized database at {settings.database_url}")


@app.command("ingest")
def ingest(input_dir: Path) -> None:
    settings = get_settings()
    storage = Storage(settings)
    run_id = storage.create_run(str(input_dir), notes={"mode": "ingest"})
    courses, errors = ingest_all(input_dir, storage, run_id)
    typer.echo(f"run_id={run_id} ingested {len(courses)} courses with {len(errors)} errors")


@app.command("export-standardized")
def export_standardized_command(input_dir: Path) -> None:
    settings = get_settings()
    storage = Storage(settings)
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "export_standardized"},
    )
    outputs = export_standardized(
        input_dir,
        settings,
        storage,
        run_id,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-semantic-extract-llm")
def run_semantic_extract_llm_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "semantic_extract_llm", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_semantic_extract_llm_stage(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("inspect-semantic-run")
def inspect_semantic_run_command(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    report = inspect_semantic_run(run_dir)
    typer.echo(f"report: {report}")


@app.command("run-question-seed-gen")
def run_question_seed_gen_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "question_seed_gen", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_question_seed_generation_stage(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")
 

@app.command("run-question-repair-llm")
def run_question_repair_llm_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "question_repair_llm", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_question_repair_stage(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-question-expand-llm")
def run_question_expand_llm_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "question_expand_llm", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_question_expand_stage(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("inspect-question-refine-run")
def inspect_question_refine_run_command(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    report = inspect_question_refine_run(run_dir)
    typer.echo(f"report: {report}")

@app.command("run-question-gen-v3")
def run_question_gen_v3_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "question_gen_v3", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_question_generation_v3(
        input_dir=input_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-pipeline-refactor")
def run_pipeline_refactor_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
    include_answers: bool = typer.Option(True, "--include-answers/--no-include-answers", help="Toggle downstream answer generation"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "pipeline_refactor", "limit": limit, "course_ids": parsed_course_ids, "include_answers": include_answers},
    )
    run_dir = run_pipeline_refactor(
        input_dir=input_dir,
        settings=settings,
        run_id=run_id,
        limit=limit,
        course_ids=parsed_course_ids,
        include_answers=include_answers,
    )
    typer.echo(f"run_root: {run_dir}")


@app.command("build-question-gen-v3-review-bundle")
def build_question_gen_v3_review_bundle_command(
    run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    outputs = build_question_generation_v3_review_bundle(
        run_dir=run_dir,
        settings=settings,
        course_ids=parsed_course_ids,
    )
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-question-gen-v4-policy")
def run_question_gen_v4_policy_command(
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    source_run_dir = settings.output_root / v3_run_id
    if not source_run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {source_run_dir}")
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(source_run_dir),
        notes={"mode": "question_gen_v4_policy", "source_run_id": v3_run_id, "course_ids": parsed_course_ids},
    )
    outputs = run_question_generation_v4_policy(
        source_run_dir=source_run_dir,
        settings=settings,
        run_id=run_id,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("build-question-gen-v4-review-bundle")
def build_question_gen_v4_review_bundle_command(
    run_id: str,
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    source_run_dir = settings.output_root / v3_run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    if not source_run_dir.exists():
        raise typer.BadParameter(f"source V3 run directory not found: {source_run_dir}")
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    outputs = build_question_generation_v4_review_bundle(
        run_dir=run_dir,
        source_run_dir=source_run_dir,
        settings=settings,
        course_ids=parsed_course_ids,
    )
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-question-gen-v4-1-policy")
def run_question_gen_v4_1_policy_command(
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    source_run_dir = settings.output_root / v3_run_id
    if not source_run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {source_run_dir}")
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(source_run_dir),
        notes={"mode": "question_gen_v4_1_policy", "source_run_id": v3_run_id, "course_ids": parsed_course_ids},
    )
    outputs = run_question_generation_v4_1_policy(
        source_run_dir=source_run_dir,
        settings=settings,
        run_id=run_id,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("build-question-gen-v4-1-review-bundle")
def build_question_gen_v4_1_review_bundle_command(
    run_id: str,
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    source_run_dir = settings.output_root / v3_run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    if not source_run_dir.exists():
        raise typer.BadParameter(f"source V3 run directory not found: {source_run_dir}")
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    outputs = build_question_generation_v4_1_review_bundle(
        run_dir=run_dir,
        source_run_dir=source_run_dir,
        settings=settings,
        course_ids=parsed_course_ids,
    )
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-question-ledger-v6")
def run_question_ledger_v6_command(
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    source_run_dir = settings.output_root / v3_run_id
    if not source_run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {source_run_dir}")
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(source_run_dir),
        notes={"mode": "question_ledger_v6", "source_run_id": v3_run_id, "course_ids": parsed_course_ids},
    )
    outputs = run_question_ledger_v6(
        source_run_dir=source_run_dir,
        settings=settings,
        run_id=run_id,
        course_ids=parsed_course_ids,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("build-question-ledger-v6-review-bundle")
def build_question_ledger_v6_review_bundle_command(
    run_id: str,
    v3_run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    source_run_dir = settings.output_root / v3_run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    if not source_run_dir.exists():
        raise typer.BadParameter(f"source V3 run directory not found: {source_run_dir}")
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    outputs = build_question_ledger_v6_review_bundle(
        run_dir=run_dir,
        source_run_dir=source_run_dir,
        settings=settings,
        course_ids=parsed_course_ids,
    )
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("build-inspection-bundle")
def build_inspection_bundle_command(
    run_id: str,
    output_root: Path = typer.Option(Path("/code/data/pipeline_runs"), help="Pipeline runs root"),
    output_dir: Path | None = typer.Option(None, help="Destination bundle directory"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
    strict: bool = typer.Option(False, help="Fail on blocking validation issues"),
    dry_run: bool = typer.Option(False, help="Validate without writing bundle files"),
) -> None:
    parsed_course_ids = [part.strip() for part in course_ids.split(",") if part.strip()] if course_ids else None
    target_dir = output_dir or (Path("/code/docs") / f"inspection_bundle_{run_id}")
    try:
        bundle_dir = build_inspection_bundle(
            run_id=run_id,
            output_dir=target_dir,
            output_root=output_root,
            course_ids=parsed_course_ids,
            strict=strict,
            dry_run=dry_run,
        )
    except BundleBuildError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"bundle={bundle_dir}")

if __name__ == "__main__":
    app()
