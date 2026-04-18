from __future__ import annotations

from course_pipeline.question_ledger_v6.run_v6 import build_v6_review_bundle

try:
    from prefect import task
except Exception:  # noqa: BLE001
    def task(*args, **kwargs):  # type: ignore
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        def decorator(func):
            return func
        return decorator


@task
def render_bundle(context, standardized_result, ledger_result):
    outputs = build_v6_review_bundle(context.run_root, standardized_result["courses"], ledger_result["per_course"])
    target_bundle = context.bundle_dir
    source_bundle = outputs["review_bundle"]
    if not target_bundle.exists():
        target_bundle.mkdir(parents=True, exist_ok=True)
    for path in source_bundle.iterdir():
        (target_bundle / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return {"artifact_paths": [source_bundle, target_bundle]}
