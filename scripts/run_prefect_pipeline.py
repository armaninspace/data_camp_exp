from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow
from course_pipeline.prefect_pipeline.models.run_config import RunConfig


app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def run(
    run_mode: str = typer.Option("dev"),
    input_root: Path = typer.Option(...),
    output_root: Path = typer.Option(...),
    ref_root: Path | None = typer.Option(None),
    strict_mode: bool = typer.Option(True),
    offset: int = typer.Option(0),
    max_courses: int | None = typer.Option(None),
    course_id: list[str] | None = typer.Option(None),
    skip_existing_ref_courses: bool = typer.Option(False),
    overwrite_existing: bool = typer.Option(False),
    persist_to_db: bool = typer.Option(False),
    model_profile: str = typer.Option("default"),
    tag: list[str] | None = typer.Option(None),
) -> None:
    config = RunConfig(
        run_mode=run_mode,
        input_root=input_root,
        output_root=output_root,
        ref_root=ref_root,
        strict_mode=strict_mode,
        offset=offset,
        max_courses=max_courses,
        course_ids=course_id or None,
        skip_existing_ref_courses=skip_existing_ref_courses,
        overwrite_existing=overwrite_existing,
        persist_to_db=persist_to_db,
        model_profile=model_profile,
        tags=tag or [],
    )
    result = question_generation_pipeline_flow(config)
    typer.echo(f"run_id={result.run_id}")
    typer.echo(f"status={result.status}")
    typer.echo(f"manifest={result.manifest_path}")


if __name__ == "__main__":
    app()
