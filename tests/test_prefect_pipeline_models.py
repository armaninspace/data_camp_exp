from __future__ import annotations

from pathlib import Path

from course_pipeline.prefect_pipeline.context import create_run_context
from course_pipeline.prefect_pipeline.manifests import build_run_result
from course_pipeline.prefect_pipeline.models.run_config import RunConfig
from course_pipeline.prefect_pipeline.models.stage_summary import StageSummary


def test_run_config_defaults(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    assert config.strict_mode is True
    assert config.run_mode == "dev"
    assert config.promote_ref is True
    assert config.standardized_output_subdir == "standardized"


def test_create_run_context_creates_stage_directories(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    context = create_run_context(config)
    assert context.run_root.exists()
    assert context.ref_root == tmp_path / "ref"
    assert context.standardized_dir.exists()
    assert context.bundle_dir.exists()


def test_build_run_result_writes_manifest(tmp_path: Path) -> None:
    config = RunConfig(input_root=tmp_path / "in", output_root=tmp_path / "out")
    context = create_run_context(config)
    stage = StageSummary(stage_name="prepare", started_at=context.started_at, status="completed")
    result = build_run_result(context, [stage], [], status="completed")
    assert result.status == "completed"
    assert result.promoted_ref is False
    assert context.manifest_path.exists()
