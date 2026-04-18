from __future__ import annotations

from course_pipeline.prefect_pipeline.context import create_run_context
from course_pipeline.prefect_pipeline.models.run_config import RunConfig

try:
    from prefect import task
except Exception:  # noqa: BLE001
    def task(*args, **kwargs):  # type: ignore
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        def decorator(func):
            return func
        return decorator


@task(retries=0)
def prepare_run_context(config: RunConfig):
    return create_run_context(config)
