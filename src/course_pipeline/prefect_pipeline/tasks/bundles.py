from __future__ import annotations

from course_pipeline.config import get_settings
from course_pipeline.questions.inspection import build_ledger_review_bundle
from course_pipeline.questions.policy.run_policy import build_v4_1_review_bundle

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
def render_bundle(context, standardized_result, ledger_result, policy_result):
    settings = get_settings()
    if settings.openai_api_key:
        outputs = build_v4_1_review_bundle(
            context.run_root,
            settings,
            standardized_result["courses"],
            policy_result["per_course"],
        )
    else:
        outputs = build_ledger_review_bundle(context.run_root, standardized_result["courses"], ledger_result["per_course"])
    target_bundle = context.bundle_dir
    source_bundle = outputs["review_bundle"]
    if not target_bundle.exists():
        target_bundle.mkdir(parents=True, exist_ok=True)
    for path in source_bundle.iterdir():
        (target_bundle / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    artifact_paths = [source_bundle, target_bundle]
    for key in ("review_answers", "llm_metering"):
        path = outputs.get(key)
        if path is not None and path.exists():
            artifact_paths.append(path)
    return {"artifact_paths": artifact_paths}
