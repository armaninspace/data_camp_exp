from course_pipeline.cli import app


def test_cli_exposes_only_current_pipeline_commands() -> None:
    names = {command.name for command in app.registered_commands}

    assert names == {
        "build-question-gen-v3-review-bundle",
        "build-question-gen-v4-1-review-bundle",
        "build-question-gen-v4-review-bundle",
        "build-question-ledger-v6-review-bundle",
        "export-standardized",
        "ingest",
        "init-db",
        "run-question-gen-v3",
        "run-question-gen-v4-1-policy",
        "run-question-gen-v4-policy",
        "run-question-ledger-v6",
    }


def test_cli_does_not_expose_removed_legacy_commands() -> None:
    names = {command.name for command in app.registered_commands}

    assert "run-learning-outcomes" not in names
    assert "build-question-cache" not in names
    assert "run-question-gen-v2" not in names
    assert "serve-web-app" not in names
