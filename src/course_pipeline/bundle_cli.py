from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.bundle_builder import BundleBuildError, build_inspection_bundle


app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def run(
    run_id: str = typer.Option(..., help="Pipeline run ID to bundle"),
    output_root: Path = typer.Option(Path("/code/data/pipeline_runs"), help="Pipeline runs root"),
    output_dir: Path | None = typer.Option(None, help="Destination bundle directory"),
    course_id: list[str] | None = typer.Option(None, help="Explicit scoped course IDs"),
    strict: bool = typer.Option(False, help="Fail on blocking validation issues"),
    dry_run: bool = typer.Option(False, help="Validate without writing bundle files"),
) -> None:
    target_dir = output_dir or (Path("/code/docs") / f"inspection_bundle_{run_id}")
    try:
        bundle_dir = build_inspection_bundle(
            run_id=run_id,
            output_dir=target_dir,
            output_root=output_root,
            course_ids=course_id or None,
            strict=strict,
            dry_run=dry_run,
        )
    except BundleBuildError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"bundle={bundle_dir}")


if __name__ == "__main__":
    app()
