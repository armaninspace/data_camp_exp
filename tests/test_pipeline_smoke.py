from importlib import import_module


def test_live_pipeline_modules_import_cleanly() -> None:
    modules = [
        "course_pipeline.cli",
        "course_pipeline.pipeline",
        "course_pipeline.prefect_pipeline.flows",
        "course_pipeline.question_gen_v3.pipeline",
        "course_pipeline.question_gen_v4.run_v4_policy",
        "course_pipeline.question_gen_v4_1.run_v4_1_policy",
        "course_pipeline.question_ledger_v6.run_v6",
    ]

    for module_name in modules:
        import_module(module_name)
