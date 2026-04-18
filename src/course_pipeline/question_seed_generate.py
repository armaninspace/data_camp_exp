from __future__ import annotations

from course_pipeline.questions.candidates.generate_candidates import generate_candidates
from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    QuestionCandidate,
    TopicEdge,
    TopicNode,
)


def generate_seed_candidates(
    doc: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    config: dict,
) -> list[QuestionCandidate]:
    return generate_candidates(doc, topics, edges, pedagogy, frictions, config)
