from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.config import get_settings
from course_pipeline.pipeline import export_standardized, ingest_all
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


if __name__ == "__main__":
    app()
