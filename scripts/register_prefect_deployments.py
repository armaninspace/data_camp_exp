from __future__ import annotations

import typer


app = typer.Typer(no_args_is_help=True)


@app.command()
def register(work_pool: str = "process") -> None:
    typer.echo("Deployment registration is not yet automated.")
    typer.echo(f"Recommended work pool: {work_pool}")


if __name__ == "__main__":
    app()
