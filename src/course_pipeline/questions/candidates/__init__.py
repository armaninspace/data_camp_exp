from course_pipeline.questions.candidates.models import ScoredCandidate, TopicNode


def build_candidate_review_bundle(*args, **kwargs):
    from course_pipeline.questions.candidates.pipeline import build_review_bundle

    return build_review_bundle(*args, **kwargs)


def run_candidate_generation_for_course(*args, **kwargs):
    from course_pipeline.questions.candidates.pipeline import run_question_gen_v3_for_course

    return run_question_gen_v3_for_course(*args, **kwargs)


def write_candidate_course_artifacts(*args, **kwargs):
    from course_pipeline.questions.candidates.pipeline import write_course_artifacts

    return write_course_artifacts(*args, **kwargs)


def write_candidate_run_report(*args, **kwargs):
    from course_pipeline.questions.candidates.pipeline import write_run_report

    return write_run_report(*args, **kwargs)


__all__ = [
    "ScoredCandidate",
    "TopicNode",
    "build_candidate_review_bundle",
    "run_candidate_generation_for_course",
    "write_candidate_course_artifacts",
    "write_candidate_run_report",
]
