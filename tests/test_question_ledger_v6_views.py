from course_pipeline.question_gen_v3.models import TopicNode
from course_pipeline.question_gen_v4.policy_models import PolicyScores
from course_pipeline.question_gen_v4_1.policy_models import CandidateRecord
from course_pipeline.question_ledger_v6.build_ledger import (
    build_anchor_summaries,
    build_inspection_report,
    build_ledger_rows,
    derive_views,
)


def _scores(**overrides) -> PolicyScores:
    base = PolicyScores(
        correctness=0.9,
        groundedness=0.92,
        contradiction_risk=0.1,
        coherence=0.9,
        query_likelihood=0.9,
        pedagogical_value=0.8,
        answer_richness=0.7,
        mastery_fit=0.9,
        distinctiveness=0.5,
        serviceability=0.82,
        context_dependence=0.2,
        answer_stability=0.85,
    )
    return base.model_copy(update=overrides)


def _candidate(**overrides) -> CandidateRecord:
    base = CandidateRecord(
        candidate_id="q1",
        question="What is seasonality?",
        answer="",
        topic_ids=["seasonality"],
        canonical_id="q1",
        is_correct=True,
        is_grounded=True,
        delivery_class="curated_visible",
        visible=True,
        non_visible_reasons=[],
        scores=_scores(),
        source_refs=["src1"],
        is_foundational_anchor=True,
        is_required_entry_candidate=True,
        is_canonical=True,
        is_alias=False,
        question_type="definition",
        mastery_band="novice",
        family_tags=["entry"],
    )
    return base.model_copy(update=overrides)


def _topics() -> dict[str, TopicNode]:
    seasonality = TopicNode(
        topic_id="seasonality",
        label="Seasonality",
        aliases=[],
        topic_type="concept",
        description="A repeating pattern.",
        source_section_ids=[1],
        confidence=0.9,
    )
    trend = TopicNode(
        topic_id="trend",
        label="Trend",
        aliases=[],
        topic_type="concept",
        description="A long-run movement.",
        source_section_ids=[1],
        confidence=0.9,
    )
    return {"seasonality": seasonality, "trend": trend}


def test_build_ledger_rows_preserves_all_candidates():
    validated = [
        _candidate(),
        _candidate(
            candidate_id="q2",
            question="What does seasonality mean?",
            canonical_id="q1",
            delivery_class="alias_only",
            visible=False,
            non_visible_reasons=["alias_of_canonical"],
            is_required_entry_candidate=False,
            is_canonical=False,
            is_alias=True,
        ),
        _candidate(
            candidate_id="q3",
            question="How is seasonality different from trend?",
            delivery_class="cache_servable",
            visible=False,
            non_visible_reasons=["quota_displacement"],
            is_required_entry_candidate=False,
            question_type="comparison",
            mastery_band="developing",
            family_tags=["bridge"],
        ),
    ]
    hard_rejects = [
        _candidate(
            candidate_id="q4",
            question="Malformed seasonality question",
            delivery_class="hard_reject",
            visible=False,
            non_visible_reasons=["invalid_low_correctness"],
            is_correct=False,
            is_grounded=False,
            is_required_entry_candidate=False,
            is_canonical=False,
            family_tags=["entry"],
        )
    ]
    rows = build_ledger_rows(validated, hard_rejects, _topics())
    assert len(rows) == 4
    assert {row.question_id for row in rows} == {"q1", "q2", "q3", "q4"}
    assert any(row.alias and row.canonical_target == "q1" for row in rows)
    assert any(row.delivery_class == "hard_reject" for row in rows)
    assert next(row for row in rows if row.question_id == "q1").tracked_topics == ["seasonality"]
    assert next(row for row in rows if row.question_id == "q3").tracked_topics == ["seasonality", "trend"]


def test_derive_views_are_reconstructible_from_ledger():
    rows = build_ledger_rows(
        [
            _candidate(),
            _candidate(
                candidate_id="q2",
                delivery_class="cache_servable",
                visible=False,
                non_visible_reasons=["quota_displacement"],
                is_required_entry_candidate=False,
                question_type="comparison",
                family_tags=["bridge"],
            ),
            _candidate(
                candidate_id="q3",
                canonical_id="q1",
                delivery_class="alias_only",
                visible=False,
                non_visible_reasons=["alias_of_canonical"],
                is_required_entry_candidate=False,
                is_canonical=False,
                is_alias=True,
            ),
        ],
        [],
        _topics(),
    )
    views = derive_views(rows)
    assert len(views["visible_curated"]) == 1
    assert len(views["cache_servable"]) == 1
    assert len(views["aliases"]) == 1
    assert all(row.delivery_class == "alias_only" for row in views["aliases"])


def test_anchor_summaries_capture_required_entry_visibility():
    rows = build_ledger_rows(
        [
            _candidate(),
            _candidate(
                candidate_id="q2",
                question="What is trend?",
                topic_ids=["trend"],
                canonical_id="q2",
                question_type="definition",
                delivery_class="analysis_only",
                visible=False,
                non_visible_reasons=["analysis_only_low_distinctiveness"],
            ),
        ],
        [],
        _topics(),
    )
    summaries = build_anchor_summaries(rows)
    by_anchor = {summary.anchor_id: summary for summary in summaries}
    assert by_anchor["seasonality"].coverage_status == "PASS"
    assert by_anchor["seasonality"].required_entry_visible is True
    assert by_anchor["trend"].coverage_status == "WARN"
    assert by_anchor["trend"].required_entry_exists is True
    assert by_anchor["trend"].required_entry_visible is False


def test_inspection_report_includes_hidden_reasons():
    rows = build_ledger_rows(
        [
            _candidate(),
            _candidate(
                candidate_id="q2",
                delivery_class="analysis_only",
                visible=False,
                non_visible_reasons=["analysis_only_low_distinctiveness"],
            ),
        ],
        [],
        _topics(),
    )
    report = build_inspection_report(rows, build_anchor_summaries(rows))
    assert "analysis_only_low_distinctiveness" in report
    assert "## Anchor: Seasonality" in report
    assert "tracked_topics: ['seasonality']" in report
