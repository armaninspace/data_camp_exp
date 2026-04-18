from __future__ import annotations

import pytest

from course_pipeline.foundational_entry_questions import (
    acronym_companion_question,
    plain_definition_question,
)
from course_pipeline.question_gen_v3.generate_candidates import generate_candidates
from course_pipeline.question_gen_v3.models import (
    CandidateScore,
    CanonicalDocument,
    QuestionCandidate,
    ScoredCandidate,
    Section,
    TopicNode,
)
from course_pipeline.question_gen_v3.filters import filter_candidates
from course_pipeline.question_gen_v4_1.config import load_default_config
from course_pipeline.question_gen_v4_1.anchors import detect_foundational_anchors
from course_pipeline.question_gen_v4_1.run_v4_1_policy import run_question_gen_v4_1_policy


def test_plain_definition_question_prefers_beginner_forms():
    assert plain_definition_question("ARIMA models") == "What is ARIMA?"
    assert acronym_companion_question("ARIMA models") == "What does ARIMA stand for?"
    assert plain_definition_question("Ljung-Box test") == "What is the Ljung-Box test?"
    assert plain_definition_question("seasonality") == "What is seasonality?"
    assert plain_definition_question("trend") == "What is trend?"
    assert plain_definition_question("repeated cycles") == "What are repeated cycles?"


def test_generate_candidates_emits_plain_foundational_definitions():
    doc = CanonicalDocument(
        doc_id="24491",
        title="Forecasting in R",
        sections=[
            Section(section_index=1, title="Exploring and visualizing time series", summary="Plot data to discover trend and seasonality.", source="explicit"),
            Section(section_index=2, title="Forecasting with ARIMA models", summary="ARIMA models are introduced alongside exponential smoothing and the Ljung-Box test.", source="explicit"),
        ],
    )
    topics = [
        TopicNode(topic_id="arima-models", label="ARIMA models", aliases=[], topic_type="concept", description="ARIMA models", source_section_ids=[2], confidence=0.9),
        TopicNode(topic_id="exponential-smoothing", label="exponential smoothing", aliases=[], topic_type="concept", description="exponential smoothing", source_section_ids=[2], confidence=0.9),
        TopicNode(topic_id="ljung-box-test", label="Ljung-Box test", aliases=[], topic_type="diagnostic", description="Ljung-Box test", source_section_ids=[2], confidence=0.9),
        TopicNode(topic_id="trend", label="trend", aliases=[], topic_type="concept", description="trend", source_section_ids=[1], confidence=0.9),
        TopicNode(topic_id="seasonality", label="seasonality", aliases=[], topic_type="concept", description="seasonality", source_section_ids=[1], confidence=0.9),
    ]
    generated = generate_candidates(doc, topics, [], [], [], {})
    texts = {candidate.question_text for candidate in generated}
    assert "What is ARIMA?" in texts
    assert "What does ARIMA stand for?" in texts
    assert "What is exponential smoothing?" in texts
    assert "What is the Ljung-Box test?" in texts
    assert "What is trend?" in texts
    assert "What is seasonality?" in texts


def test_filter_candidates_keeps_plain_foundational_definitions():
    topics = [
        TopicNode(topic_id="arima-models", label="ARIMA models", aliases=[], topic_type="concept", description="ARIMA models", source_section_ids=[1], confidence=0.9),
        TopicNode(topic_id="benchmark-methods", label="benchmark methods", aliases=[], topic_type="comparison_axis", description="benchmark methods", source_section_ids=[1], confidence=0.9),
        TopicNode(topic_id="trend", label="trend", aliases=[], topic_type="concept", description="trend", source_section_ids=[1], confidence=0.9),
    ]
    candidates = [
        QuestionCandidate(candidate_id="a", topic_id="arima-models", slot="novice_definition", mastery_band="novice", question_type="definition", question_text="What is ARIMA?", rationale="test", source_support=["support"], linked_friction_ids=[], section_ids=[1]),
        QuestionCandidate(candidate_id="b", topic_id="benchmark-methods", slot="novice_definition", mastery_band="novice", question_type="definition", question_text="What are benchmark methods?", rationale="test", source_support=["support"], linked_friction_ids=[], section_ids=[1]),
        QuestionCandidate(candidate_id="c", topic_id="trend", slot="novice_definition", mastery_band="novice", question_type="definition", question_text="What is trend?", rationale="test", source_support=["support"], linked_friction_ids=[], section_ids=[1]),
    ]
    kept, rejected = filter_candidates(candidates, topics, {})
    assert {candidate.question_text for candidate in kept} == {
        "What is ARIMA?",
        "What are benchmark methods?",
        "What is trend?",
    }
    assert rejected == []


def test_detect_foundational_anchors_dedupes_duplicate_labels_and_skips_generic_labels():
    topics = [
        TopicNode(topic_id="arima-models", label="ARIMA models", aliases=[], topic_type="concept", description="ARIMA models", source_section_ids=[1], confidence=0.82),
        TopicNode(topic_id="arima", label="ARIMA", aliases=[], topic_type="concept", description="ARIMA overview mention", source_section_ids=[1], confidence=0.74),
        TopicNode(topic_id="advanced-methods", label="Advanced methods", aliases=[], topic_type="concept", description="generic heading", source_section_ids=[2], confidence=0.82),
    ]
    anchors = detect_foundational_anchors(topics)
    assert sorted(anchors) == ["arima-models"]


def test_run_v4_1_policy_promotes_protected_plain_definitions():
    cfg = load_default_config()
    topic = TopicNode(
        topic_id="arima-models",
        label="ARIMA models",
        aliases=[],
        topic_type="concept",
        description="ARIMA models are used for forecasting.",
        source_section_ids=[1],
        confidence=0.9,
    )
    v3_result = {
        "topics": [topic],
        "frictions": [],
        "scored_candidates": [
            _scored_candidate(
                topic_id="arima-models",
                question_text="What is ARIMA?",
                question_type="definition",
                mastery_band="novice",
                slot="novice_definition",
                novelty=0.4,
            ),
            _scored_candidate(
                topic_id="arima-models",
                question_text="What does ARIMA stand for?",
                question_type="definition",
                mastery_band="novice",
                slot="novice_definition",
                novelty=0.45,
            ),
            _scored_candidate(
                topic_id="arima-models",
                question_text="How is ARIMA different from exponential smoothing?",
                question_type="comparison",
                mastery_band="developing",
                slot="developing_comparison",
                novelty=0.88,
            ),
        ],
    }
    result = run_question_gen_v4_1_policy(v3_result, cfg)
    by_question = {row.question: row for row in result["validated_correct_all"]}
    arima = by_question["What is ARIMA?"]
    assert arima.visible is True
    assert arima.delivery_class == "curated_visible"
    assert arima.is_required_entry_candidate is True
    assert "analysis_only_low_distinctiveness" not in arima.non_visible_reasons


def test_run_v4_1_policy_strict_mode_fails_without_visible_plain_definition():
    cfg = load_default_config()
    topic = TopicNode(
        topic_id="seasonality",
        label="seasonality",
        aliases=[],
        topic_type="concept",
        description="Seasonality affects repeated patterns.",
        source_section_ids=[1],
        confidence=0.9,
    )
    v3_result = {
        "topics": [topic],
        "frictions": [],
        "scored_candidates": [
            _scored_candidate(
                topic_id="seasonality",
                question_text="How would I apply seasonality to the kind of data used here?",
                question_type="procedure",
                mastery_band="developing",
                slot="developing_procedural",
                novelty=0.85,
            )
        ],
    }
    with pytest.raises(RuntimeError, match="Strict foundational entry coverage failed"):
        run_question_gen_v4_1_policy(v3_result, cfg)


def _scored_candidate(
    *,
    topic_id: str,
    question_text: str,
    question_type: str,
    mastery_band: str,
    slot: str,
    novelty: float,
) -> ScoredCandidate:
    return ScoredCandidate(
        candidate=QuestionCandidate(
            candidate_id=f"{topic_id}-{slot}-{question_text.lower().replace(' ', '-')}",
            topic_id=topic_id,
            slot=slot,  # type: ignore[arg-type]
            mastery_band=mastery_band,  # type: ignore[arg-type]
            question_type=question_type,  # type: ignore[arg-type]
            question_text=question_text,
            rationale="test",
            source_support=["grounded support"],
            linked_friction_ids=[],
            section_ids=[1],
        ),
        score=CandidateScore(
            friction_value=0.7,
            specificity=0.8,
            answer_richness=0.8,
            mastery_fit=0.8,
            novelty=novelty,
            groundedness=0.82,
            total=0.8,
        ),
        rejection_flags=[],
    )
