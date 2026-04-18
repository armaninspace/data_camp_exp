from __future__ import annotations

from pathlib import Path

import typer

from course_pipeline.config import get_settings
from course_pipeline.inspect_question_cache import launch_question_cache_inspector
from course_pipeline.inspect_learning import launch_learning_inspector
from course_pipeline.pipeline import (
    build_question_generation_review_bundle,
    build_question_generation_v3_review_bundle,
    build_question_generation_v4_review_bundle,
    build_question_generation_v4_1_review_bundle,
    build_question_ledger_v6_review_bundle,
    build_question_cache,
    export_standardized,
    ingest_all,
    render_question_cache_yaml,
    render_learning_outcomes_yaml,
    run_question_ledger_v6,
    run_question_generation_v2,
    run_question_generation_v3,
    run_question_generation_v4_policy,
    run_question_generation_v4_1_policy,
    run_learning_outcomes,
)
from course_pipeline.question_cache import QuestionCacheFallback, QuestionCacheIndex
from course_pipeline.storage import Storage
from course_pipeline.webapp import serve_web_app


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


@app.command("run-learning-outcomes")
def run_learning_outcomes_command(
    input_dir: Path,
    limit: int = typer.Option(5, help="Course limit for bounded semantic extraction"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "learning_outcomes", "limit": limit},
    )
    outputs = run_learning_outcomes(
        input_dir,
        settings,
        storage,
        run_id,
        limit=limit,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("inspect-learning-run")
def inspect_learning_run(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    launch_learning_inspector(run_dir)


@app.command("render-learning-yaml")
def render_learning_yaml_command(
    run_id: str,
    width: int = typer.Option(80, help="Preferred YAML wrap width"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    out_dir = render_learning_outcomes_yaml(run_dir, width=width)
    typer.echo(f"learning_outcomes_yaml: {out_dir}")


@app.command("build-question-cache")
def build_question_cache_command(
    learning_run_id: str,
    limit: int | None = typer.Option(None, help="Optional course limit"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    source_run_dir = settings.output_root / learning_run_id
    if not source_run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {source_run_dir}")
    run_id = storage.create_run(
        str(source_run_dir),
        notes={"mode": "question_cache", "source_run_id": learning_run_id, "limit": limit},
    )
    outputs = build_question_cache(
        source_run_dir=source_run_dir,
        settings=settings,
        storage=storage,
        run_id=run_id,
        limit=limit,
    )
    typer.echo(f"run_id={run_id}")
    for name, path in outputs.items():
        typer.echo(f"{name}: {path}")


@app.command("run-question-gen-v2")
def run_question_gen_v2_command(
    input_dir: Path,
    limit: int | None = typer.Option(None, help="Optional course limit"),
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    run_id = storage.create_run(
        str(input_dir),
        notes={"mode": "question_gen_v2", "limit": limit, "course_ids": parsed_course_ids},
    )
    outputs = run_question_generation_v2(
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


@app.command("build-question-gen-review-bundle")
def build_question_gen_review_bundle_command(
    run_id: str,
    course_ids: str | None = typer.Option(None, help="Optional comma-separated course IDs"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    parsed_course_ids = [part.strip() for part in course_ids.split(",")] if course_ids else None
    outputs = build_question_generation_review_bundle(
        run_dir=run_dir,
        settings=settings,
        course_ids=parsed_course_ids,
    )
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


@app.command("render-question-cache-yaml")
def render_question_cache_yaml_command(
    run_id: str,
    width: int = typer.Option(80, help="Preferred YAML wrap width"),
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    out_dir = render_question_cache_yaml(run_dir, width=width)
    typer.echo(f"question_cache_yaml: {out_dir}")


@app.command("inspect-question-cache-run")
def inspect_question_cache_run(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    launch_question_cache_inspector(run_dir)


@app.command("ask-question-cache")
def ask_question_cache(
    run_id: str,
    question: str = typer.Argument(..., help="Learner question to resolve"),
    course_id: str | None = typer.Option(None, help="Optional course scope"),
) -> None:
    settings = get_settings()
    storage = Storage(settings)
    run_dir = settings.output_root / run_id
    index = QuestionCacheIndex.from_run_dir(run_dir)
    result = index.match(question, course_id=course_id)
    if result.resolved_as_hit:
        storage.log_question_cache_match(result)
        typer.echo(f"hit=true method={result.match_method} score={result.match_score}")
        typer.echo(result.answer_markdown or "")
        return

    nearest_group = index.groups.get(result.question_group_id or "") if result.question_group_id else None
    nearest_answer = index.answers.get(result.canonical_answer_id or "") if result.canonical_answer_id else None
    answer = QuestionCacheFallback(settings).answer(
        question=question,
        match_result=result,
        nearest_group=nearest_group,
        nearest_answer=nearest_answer,
    )
    result.answer_markdown = answer
    storage.log_question_cache_match(result)
    storage.log_question_cache_fallback(result)
    typer.echo(f"hit=false reason={result.fallback_reason} score={result.match_score}")
    typer.echo(answer)


@app.command("replay-question-cache-eval")
def replay_question_cache_eval(
    run_id: str,
    fixture_path: Path,
) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    if not run_dir.exists():
        raise typer.BadParameter(f"run directory not found: {run_dir}")
    index = QuestionCacheIndex.from_run_dir(run_dir)
    fixture = fixture_path.read_text(encoding="utf-8")
    import yaml

    payload = yaml.safe_load(fixture) or {}
    examples = payload.get("examples") or []
    total = len(examples)
    passed = 0
    for example in examples:
        result = index.match(example["question"], course_id=example.get("course_id"))
        expected_hit = bool(example.get("expected_hit"))
        expected_group = example.get("expected_question_group_id")
        if result.resolved_as_hit == expected_hit and (expected_group is None or result.question_group_id == expected_group):
            passed += 1
        typer.echo(
            f"question={example['question']!r} hit={result.resolved_as_hit} "
            f"group={result.question_group_id} score={result.match_score}"
        )
    typer.echo(f"passed={passed}/{total}")


@app.command("validate-question-cache")
def validate_question_cache(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    validation_path = run_dir / "question_cache_validation_logs.jsonl"
    if not validation_path.exists():
        raise typer.BadParameter(f"validation log not found: {validation_path}")
    import json

    rows = [json.loads(line) for line in validation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    totals: dict[str, int] = {}
    for row in rows:
        key = f"{row['validator_type']}:{row['decision']}"
        totals[key] = totals.get(key, 0) + 1
    for key in sorted(totals):
        typer.echo(f"{key}={totals[key]}")


@app.command("audit-question-cache-coverage")
def audit_question_cache_coverage(run_id: str) -> None:
    settings = get_settings()
    run_dir = settings.output_root / run_id
    audit_path = run_dir / "claim_coverage_audit.jsonl"
    if not audit_path.exists():
        raise typer.BadParameter(f"coverage audit not found: {audit_path}")
    import json

    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    missing = [row for row in rows if not row["produced_question_groups"]]
    typer.echo(f"claims={len(rows)} uncovered={len(missing)}")
    for row in missing:
        typer.echo(
            f"{row['course_id']}:{row['claim_id']} no_groups_reason={row.get('no_groups_reason')}"
        )


@app.command("serve-web-app")
def serve_web_app_command(
    input_dir: Path,
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    learning_run_id: str | None = typer.Option(None, help="Optional completed learning run id"),
    question_cache_run_id: str | None = typer.Option(None, help="Optional completed question-cache run id"),
) -> None:
    settings = get_settings()
    serve_web_app(
        settings=settings,
        input_dir=input_dir,
        host=host,
        port=port,
        learning_run_id=learning_run_id,
        question_cache_run_id=question_cache_run_id,
    )


if __name__ == "__main__":
    app()
