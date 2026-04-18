from __future__ import annotations

import json
import os
from pathlib import Path

from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow
from course_pipeline.prefect_pipeline.models.run_config import RunConfig


REPO_ROOT = Path("/code")
INPUT_ROOT = REPO_ROOT / "data" / "classcentral-datacamp-yaml"


def _run_24491(tmp_path: Path) -> list[dict]:
    os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "120")
    config = RunConfig(
        input_root=INPUT_ROOT,
        output_root=tmp_path,
        course_ids=["24491"],
        max_courses=1,
        strict_mode=True,
    )
    result = question_generation_pipeline_flow(config)
    run_root = tmp_path / result.run_id
    assert result.status == "completed"
    return [
        json.loads(line)
        for line in (run_root / "all_questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_24491_baseline_outputs_keep_protected_entry_questions_visible(tmp_path: Path) -> None:
    rows = _run_24491(tmp_path)
    by_question = {row["question_text"]: row for row in rows}

    assert len(rows) == 40

    for question_text, tracked_topics in [
        ("What is ARIMA?", ["arima"]),
        ("What is exponential smoothing?", ["exponential-smoothing"]),
        ("What is the Ljung-Box test?", ["ljung-box-test"]),
        ("What is trend?", ["trend"]),
        ("What is seasonality?", ["seasonality"]),
    ]:
        row = by_question[question_text]
        assert row["required_entry"] is True
        assert row["visible"] is True
        assert row["delivery_class"] == "curated_visible"
        assert row["tracked_topics"] == tracked_topics


def test_24491_baseline_outputs_keep_comparison_topic_tracking_and_no_hidden_required_entry_regression(
    tmp_path: Path,
) -> None:
    rows = _run_24491(tmp_path)
    by_question = {row["question_text"]: row for row in rows}

    comparison = by_question["How is ARIMA different from exponential smoothing?"]
    assert comparison["tracked_topics"] == ["arima", "exponential-smoothing"]
    assert comparison["visible"] is True
    assert comparison["delivery_class"] == "curated_visible"

    hidden_required_entry = [
        row
        for row in rows
        if row["required_entry"]
        and not row["visible"]
        and row["non_visible_reasons"] == ["analysis_only_low_distinctiveness"]
    ]
    assert hidden_required_entry == []
