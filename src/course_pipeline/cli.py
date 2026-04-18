from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.config import get_settings
from course_pipeline.pipeline import (
    build_question_generation_v3_review_bundle,
    build_question_generation_v4_review_bundle,
    build_question_generation_v4_1_review_bundle,
    build_question_ledger_v6_review_bundle,
    export_standardized,
    ingest_all,
    run_question_ledger_v6,
    run_question_generation_v3,
    run_question_generation_v4_policy,
    run_question_generation_v4_1_policy,
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

if __name__ == "__main__":
    app()
