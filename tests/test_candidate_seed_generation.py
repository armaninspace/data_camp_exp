from __future__ import annotations

from course_pipeline.questions.candidates.generate_candidates import generate_candidates
from course_pipeline.questions.candidates.models import CanonicalDocument, TopicNode


def test_foundational_metric_special_case_keeps_plain_definition_entry_candidates() -> None:
    doc = CanonicalDocument(
        doc_id="24370",
        title="Statistician in R",
        summary="Track summary",
        overview="Track overview",
        sections=[],
    )
    topics = [
        TopicNode(
            topic_id="unemployment",
            label="unemployment",
            aliases=[],
            topic_type="metric",
            description="Finding a job after unemployment.",
            source_section_ids=[10],
            confidence=0.78,
        )
    ]

    candidates = generate_candidates(
        doc,
        topics,
        edges=[],
        pedagogy=[],
        frictions=[],
        config={"generation": {"target_final_per_course": 8}},
    )

    definition_questions = [candidate.question_text for candidate in candidates if candidate.question_type == "definition"]
    assert "What is unemployment?" in definition_questions
    assert any(candidate.question_type == "comparison" for candidate in candidates)
