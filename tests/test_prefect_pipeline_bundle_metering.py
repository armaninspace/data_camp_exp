from __future__ import annotations

from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.prefect_pipeline.tasks.bundles import render_bundle
from course_pipeline.prefect_pipeline.models.run_context import RunContext


def _context(tmp_path: Path) -> RunContext:
    run_root = tmp_path / "run-123"
    run_root.mkdir()
    bundle_dir = run_root / "inspection_bundle"
    bundle_dir.mkdir()
    return RunContext(
        run_id="run-123",
        started_at="2026-04-18T00:00:00+00:00",  # type: ignore[arg-type]
        input_root=tmp_path / "in",
        output_root=tmp_path / "out",
        ref_root=tmp_path / "ref",
        run_root=run_root,
        standardized_dir=run_root / "standardized",
        semantics_dir=run_root / "semantics",
        candidates_dir=run_root / "candidates",
        policy_dir=run_root / "policy",
        ledger_dir=run_root / "ledger",
        answer_dir=run_root / "answers",
        bundle_dir=bundle_dir,
        logs_dir=run_root / "logs",
        manifest_path=run_root / "run_manifest.json",
        run_mode="dev",
        promote_ref=False,
        strict_mode=False,
        persist_to_db=False,
        model_profile="default",
        tags=[],
        enable_answer_generation=True,
        plan_llm_metering=True,
        planned_llm_metering_stages=["candidate_review_answers", "policy_review_answers"],
    )


def _settings(with_key: bool) -> Settings:
    return Settings(
        openai_api_key="test-key" if with_key else None,
        openai_model="gpt-4.1",
        openai_timeout=30,
        openai_input_cost_per_million_tokens=2.0,
        openai_output_cost_per_million_tokens=8.0,
        database_url="postgresql+psycopg://agent@127.0.0.1:55432/course_pipeline",
        output_root=Path("/tmp/unused"),
    )


def test_render_bundle_uses_metered_policy_bundle_when_openai_key_present(monkeypatch, tmp_path: Path) -> None:
    context = _context(tmp_path)
    calls: list[str] = []

    def fake_get_settings():
        return _settings(with_key=True)

    def fake_build_v4_1_review_bundle(run_dir, settings, courses, per_course):
        calls.append("metered")
        bundle_dir = run_dir / "review_bundle"
        bundle_dir.mkdir(exist_ok=True)
        (bundle_dir / "course.md").write_text("metered bundle\n", encoding="utf-8")
        answers = run_dir / "review_answers.jsonl"
        answers.write_text('{"ok": true}\n', encoding="utf-8")
        metering = run_dir / "llm_metering.jsonl"
        metering.write_text('{"stage":"policy_review_answers","estimated_cost_usd":0.01}\n', encoding="utf-8")
        return {"review_bundle": bundle_dir, "review_answers": answers, "llm_metering": metering}

    def fake_build_ledger_review_bundle(run_dir, courses, per_course):
        calls.append("static")
        raise AssertionError("static bundle should not be used when OpenAI key is present")

    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.get_settings", fake_get_settings)
    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.build_v4_1_review_bundle", fake_build_v4_1_review_bundle)
    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.build_ledger_review_bundle", fake_build_ledger_review_bundle)

    result = render_bundle.fn(context, {"courses": []}, {"per_course": {}}, {"per_course": {}})

    assert calls == ["metered"]
    assert (context.bundle_dir / "course.md").exists()
    assert context.run_root / "llm_metering.jsonl" in result["artifact_paths"]


def test_render_bundle_falls_back_to_static_bundle_without_openai_key(monkeypatch, tmp_path: Path) -> None:
    context = _context(tmp_path)
    calls: list[str] = []

    def fake_get_settings():
        return _settings(with_key=False)

    def fake_build_v4_1_review_bundle(run_dir, settings, courses, per_course):
        calls.append("metered")
        raise AssertionError("metered bundle should not be used without OpenAI key")

    def fake_build_ledger_review_bundle(run_dir, courses, per_course):
        calls.append("static")
        bundle_dir = run_dir / "review_bundle"
        bundle_dir.mkdir(exist_ok=True)
        (bundle_dir / "course.md").write_text("static bundle\n", encoding="utf-8")
        return {"review_bundle": bundle_dir}

    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.get_settings", fake_get_settings)
    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.build_v4_1_review_bundle", fake_build_v4_1_review_bundle)
    monkeypatch.setattr("course_pipeline.prefect_pipeline.tasks.bundles.build_ledger_review_bundle", fake_build_ledger_review_bundle)

    result = render_bundle.fn(context, {"courses": []}, {"per_course": {}}, {"per_course": {}})

    assert calls == ["static"]
    assert (context.bundle_dir / "course.md").exists()
    assert all(path.name != "llm_metering.jsonl" for path in result["artifact_paths"])
