from __future__ import annotations

from course_pipeline.semantic_schemas import (
    AliasGroupRecord,
    AnchorCandidate,
    EvidenceSpan,
    TopicRecord,
)
from course_pipeline.semantic_validate import validate_and_sanitize_semantics


def _evidence() -> list[EvidenceSpan]:
    return [EvidenceSpan(field="overview", excerpt="Overview excerpt")]


def test_validate_and_sanitize_semantics_drops_placeholder_and_url_like_labels() -> None:
    result = validate_and_sanitize_semantics(
        course_id="7631",
        topic_records=[
            TopicRecord(
                course_id="7631",
                topic_id="overview-segment-1",
                label="overview-segment-1",
                aliases=[],
                topic_type="concept",
                description="Placeholder heading",
                source_fields=["chapters"],
                evidence_spans=_evidence(),
                confidence=0.7,
            ),
            TopicRecord(
                course_id="7631",
                topic_id="numpy",
                label="NumPy",
                aliases=[],
                topic_type="tool",
                description="Core Python array package",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.9,
            ),
        ],
        anchor_candidates=[
            AnchorCandidate(
                course_id="7631",
                anchor_id="www-example-com",
                label="www.example.com",
                normalized_label="www-example-com",
                anchor_type="contextual_topic",
                foundational_candidate=False,
                learner_facing=False,
                requires_entry_question=False,
                rationale="Bad anchor",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.5,
            ),
            AnchorCandidate(
                course_id="7631",
                anchor_id="numpy",
                label="NumPy",
                normalized_label="numpy",
                anchor_type="tool",
                foundational_candidate=True,
                learner_facing=True,
                requires_entry_question=True,
                rationale="Good anchor",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.95,
            ),
        ],
        alias_groups=[],
    )

    assert [record.label for record in result["topic_records"]] == ["NumPy"]
    assert [record.label for record in result["anchor_candidates"]] == ["NumPy"]
    assert result["report"].dropped_count >= 2
    assert result["report"].suspicious_anchor_count >= 2
    assert any(decision.reason == "placeholder_overview_segment_label" for decision in result["report"].decisions)
    assert any(decision.reason == "domain_or_url_like_label" for decision in result["report"].decisions)


def test_validate_and_sanitize_semantics_merges_near_duplicate_anchors() -> None:
    result = validate_and_sanitize_semantics(
        course_id="7630",
        topic_records=[
            TopicRecord(
                course_id="7630",
                topic_id="arima",
                label="ARIMA",
                aliases=[],
                topic_type="concept",
                description="Forecasting family",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.9,
            )
        ],
        anchor_candidates=[
            AnchorCandidate(
                course_id="7630",
                anchor_id="arima",
                label="ARIMA",
                normalized_label="arima",
                anchor_type="foundational_vocabulary",
                foundational_candidate=True,
                learner_facing=True,
                requires_entry_question=True,
                rationale="Primary concept",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.95,
            ),
            AnchorCandidate(
                course_id="7630",
                anchor_id="arima-models",
                label="ARIMA Models",
                normalized_label="arima-models",
                anchor_type="foundational_vocabulary",
                foundational_candidate=True,
                learner_facing=True,
                requires_entry_question=True,
                rationale="Near duplicate concept label",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.93,
            ),
        ],
        alias_groups=[
            AliasGroupRecord(
                course_id="7630",
                canonical_label="ARIMA",
                aliases=["autoregressive integrated moving average"],
                rationale="Expanded acronym",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.8,
            )
        ],
    )

    assert len(result["anchor_candidates"]) == 1
    assert result["merged_anchor_count"] == 1
    assert result["report"].merged_count == 1
    assert any(decision.action == "merge" for decision in result["report"].decisions)


def test_validate_and_sanitize_semantics_demotes_incidental_summary_only_required_entry() -> None:
    result = validate_and_sanitize_semantics(
        course_id="9900",
        topic_records=[
            TopicRecord(
                course_id="9900",
                topic_id="tourism",
                label="Tourism",
                aliases=[],
                topic_type="concept",
                description="Mentioned in course overview.",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.8,
            )
        ],
        anchor_candidates=[
            AnchorCandidate(
                course_id="9900",
                anchor_id="tourism",
                label="Tourism",
                normalized_label="tourism",
                anchor_type="foundational_vocabulary",
                foundational_candidate=True,
                learner_facing=True,
                requires_entry_question=True,
                rationale="Mentioned once in overview.",
                source_fields=["overview"],
                evidence_spans=_evidence(),
                confidence=0.8,
            )
        ],
        alias_groups=[],
    )

    assert len(result["anchor_candidates"]) == 1
    assert result["anchor_candidates"][0].requires_entry_question is False
    assert result["report"].rewritten_count == 1
    assert any(decision.reason == "entry_requirement_removed_incidental_summary_only_support" for decision in result["report"].decisions)
