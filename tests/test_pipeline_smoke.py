from importlib import import_module
from pathlib import Path


def test_live_pipeline_modules_import_cleanly() -> None:
    modules = [
        "course_pipeline.cli",
        "course_pipeline.pipeline",
        "course_pipeline.questions.candidates",
        "course_pipeline.questions.policy",
        "course_pipeline.questions.ledger",
        "course_pipeline.questions.inspection",
        "course_pipeline.prefect_pipeline.flows",
        "course_pipeline.question_gen_v3.pipeline",
        "course_pipeline.question_gen_v4.run_v4_policy",
        "course_pipeline.question_gen_v4_1.run_v4_1_policy",
        "course_pipeline.question_ledger_v6.run_v6",
    ]

    for module_name in modules:
        import_module(module_name)


def test_orchestration_layers_use_stable_questions_package_imports() -> None:
    repo_root = Path("/code")
    targets = [
        repo_root / "src/course_pipeline/pipeline.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/semantics.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/candidates.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/policy.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/ledger.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/bundles.py",
        repo_root / "src/course_pipeline/prefect_pipeline/tasks/views.py",
    ]
    banned_import_fragments = [
        "from course_pipeline.question_gen_v3",
        "from course_pipeline.question_gen_v4",
        "from course_pipeline.question_gen_v4_1",
        "from course_pipeline.question_ledger_v6",
    ]

    for target in targets:
        text = target.read_text(encoding="utf-8")
        for fragment in banned_import_fragments:
            assert fragment not in text, f"{target} still imports legacy module {fragment}"


def test_candidate_stage_package_no_longer_imports_question_gen_v3() -> None:
    package_root = Path("/code/src/course_pipeline/questions/candidates")
    banned_fragment = "course_pipeline.question_gen_v3"

    for target in sorted(package_root.glob("*.py")):
        text = target.read_text(encoding="utf-8")
        assert banned_fragment not in text, f"{target} still imports {banned_fragment}"
