from __future__ import annotations

from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow
from course_pipeline.prefect_pipeline.models.run_config import RunConfig


def build_default_deployment(config: RunConfig):
    return question_generation_pipeline_flow, config
