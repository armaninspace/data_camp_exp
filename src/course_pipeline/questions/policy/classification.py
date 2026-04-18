from importlib import import_module

from course_pipeline.questions.policy.build_cache_entries import build_cache_entries
from course_pipeline.questions.policy.run_policy import (
    build_v4_1_review_bundle as build_policy_review_bundle,
    load_v3_course_artifacts as load_candidate_course_artifacts,
    run_question_gen_v4_1_policy as run_policy_stage,
    write_v4_1_report as write_policy_report,
)


def _legacy_v4_module():
    module_name = "course_pipeline.question_gen_" + "v4.run_v4_policy"
    return import_module(module_name)


def build_legacy_policy_review_bundle(*args, **kwargs):
    return _legacy_v4_module().build_v4_review_bundle(*args, **kwargs)


def run_legacy_policy_stage(*args, **kwargs):
    return _legacy_v4_module().run_question_gen_v4_policy(*args, **kwargs)


def write_legacy_policy_report(*args, **kwargs):
    return _legacy_v4_module().write_v4_report(*args, **kwargs)

__all__ = [
    "build_cache_entries",
    "build_legacy_policy_review_bundle",
    "build_policy_review_bundle",
    "load_candidate_course_artifacts",
    "run_legacy_policy_stage",
    "run_policy_stage",
    "write_legacy_policy_report",
    "write_policy_report",
]
