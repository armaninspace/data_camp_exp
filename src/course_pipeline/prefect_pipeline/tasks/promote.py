from __future__ import annotations

from course_pipeline.prefect_pipeline.ref_data import promote_ref_data

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
def promote_reference_data(context, standardized_result, ledger_result):
    return promote_ref_data(context, standardized_result, ledger_result)
