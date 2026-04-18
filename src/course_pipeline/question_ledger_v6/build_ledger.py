from __future__ import annotations

from collections import defaultdict

from course_pipeline.questions.candidates.models import TopicNode
from course_pipeline.questions.policy.models import CandidateRecord
from course_pipeline.question_ledger_v6.models import AnchorSummary, LedgerRow, LedgerScores
from course_pipeline.question_ledger_v6.normalize import (
    ledger_tags,
    normalize_question_text,
    normalize_question_type,
    normalize_topic_slug,
    normalized_topic_variants,
    question_mentions_topic,
    select_question_family,
)


def _anchor_type(record: CandidateRecord, topic: TopicNode | None) -> str:
    if record.is_foundational_anchor:
        return "foundational_vocabulary"
    if topic is not None:
        return topic.topic_type
    return "contextual_topic"


def _ledger_scores(record: CandidateRecord) -> LedgerScores:
    return LedgerScores(
        groundedness=record.scores.groundedness,
        correctness=record.scores.correctness,
        query_likelihood=record.scores.query_likelihood,
        pedagogical_value=record.scores.pedagogical_value,
        serviceability=record.scores.serviceability,
        distinctiveness=record.scores.distinctiveness,
    )


def build_ledger_rows(
    validated_correct_all: list[CandidateRecord],
    hard_reject_records: list[CandidateRecord],
    topics_by_id: dict[str, TopicNode],
) -> list[LedgerRow]:
    topic_variants_by_id = {
        topic_id: normalized_topic_variants(topic.label, topic_id)
        for topic_id, topic in topics_by_id.items()
    }
    rows: list[LedgerRow] = []
    for record in validated_correct_all + hard_reject_records:
        anchor_id = record.topic_ids[0] if record.topic_ids else "unknown_anchor"
        topic = topics_by_id.get(anchor_id)
        normalized_question = normalize_question_text(record.question)
        question_type = normalize_question_type(record.question_type)
        question_family = select_question_family(record.family_tags, record.question_type)
        delivery_class = record.delivery_class
        visible = delivery_class == "curated_visible"
        canonical_target = record.canonical_id if record.is_alias and record.canonical_id else None
        rows.append(
            LedgerRow(
                question_id=record.candidate_id,
                question_text=normalized_question,
                answer_text=record.answer,
                anchor_id=anchor_id,
                anchor_label=topic.label if topic is not None else anchor_id,
                tracked_topics=_tracked_topics(
                    anchor_id=anchor_id,
                    anchor_label=topic.label if topic is not None else anchor_id,
                    question_text=normalized_question,
                    topics_by_id=topics_by_id,
                    topic_variants_by_id=topic_variants_by_id,
                ),
                anchor_type=_anchor_type(record, topic),
                question_family=question_family,
                question_type=question_type,
                mastery_band=record.mastery_band,
                canonical=record.is_canonical,
                alias=record.is_alias,
                canonical_target=canonical_target,
                required_entry=record.is_required_entry_candidate,
                validated_correct=record.is_correct and record.is_grounded,
                grounded=record.is_grounded,
                serviceable=delivery_class in {"curated_visible", "cache_servable"},
                delivery_class=delivery_class,
                visible=visible,
                non_visible_reasons=[] if visible else list(record.non_visible_reasons),
                reject_reasons=list(record.non_visible_reasons if delivery_class == "hard_reject" else []),
                tags=ledger_tags(record, family=question_family, question_type=question_type),
                scores=_ledger_scores(record),
                source_refs=list(record.source_refs),
            )
        )
    return sorted(rows, key=lambda row: (row.anchor_id, row.canonical_target or row.question_id, row.question_id))


def _tracked_topics(
    anchor_id: str,
    anchor_label: str,
    question_text: str,
    topics_by_id: dict[str, TopicNode],
    topic_variants_by_id: dict[str, list[str]],
) -> list[str]:
    primary_topic = normalize_topic_slug(anchor_label if anchor_label else anchor_id)
    tracked = [primary_topic] if primary_topic else []
    seen = set(tracked)
    for topic_id, topic in topics_by_id.items():
        candidate_slug = normalize_topic_slug(topic.label)
        if not candidate_slug or candidate_slug in seen:
            continue
        if question_mentions_topic(question_text, topic_variants_by_id.get(topic_id, [])):
            tracked.append(candidate_slug)
            seen.add(candidate_slug)
    return tracked


def derive_views(rows: list[LedgerRow]) -> dict[str, list[LedgerRow]]:
    return {
        "visible_curated": [row for row in rows if row.delivery_class == "curated_visible"],
        "cache_servable": [row for row in rows if row.delivery_class == "cache_servable"],
        "aliases": [row for row in rows if row.delivery_class == "alias_only"],
    }


def build_anchor_summaries(rows: list[LedgerRow]) -> list[AnchorSummary]:
    grouped: dict[str, list[LedgerRow]] = defaultdict(list)
    for row in rows:
        grouped[row.anchor_id].append(row)

    summaries: list[AnchorSummary] = []
    for anchor_id, anchor_rows in sorted(grouped.items()):
        first = anchor_rows[0]
        required_entry_exists = any(row.required_entry for row in anchor_rows)
        required_entry_visible = any(
            row.required_entry and row.visible and row.canonical and row.delivery_class == "curated_visible"
            for row in anchor_rows
        )
        if first.anchor_type == "foundational_vocabulary":
            if required_entry_visible:
                coverage_status = "PASS"
            elif required_entry_exists:
                coverage_status = "WARN"
            else:
                coverage_status = "FAIL"
        else:
            coverage_status = "PASS" if any(row.visible for row in anchor_rows) else "WARN"
        summaries.append(
            AnchorSummary(
                anchor_id=anchor_id,
                anchor_label=first.anchor_label,
                anchor_type=first.anchor_type,
                coverage_status=coverage_status,
                generated_count=len(anchor_rows),
                validated_correct_count=sum(1 for row in anchor_rows if row.validated_correct),
                visible_count=sum(1 for row in anchor_rows if row.visible),
                cache_servable_count=sum(1 for row in anchor_rows if row.delivery_class == "cache_servable"),
                analysis_only_count=sum(1 for row in anchor_rows if row.delivery_class == "analysis_only"),
                hard_reject_count=sum(1 for row in anchor_rows if row.delivery_class == "hard_reject"),
                required_entry_exists=required_entry_exists,
                required_entry_visible=required_entry_visible,
            )
        )
    return summaries


def build_inspection_report(rows: list[LedgerRow], anchor_summaries: list[AnchorSummary]) -> str:
    rows_by_anchor: dict[str, list[LedgerRow]] = defaultdict(list)
    for row in rows:
        rows_by_anchor[row.anchor_id].append(row)

    lines = ["# Question Ledger V6 Inspection Report", ""]
    for summary in anchor_summaries:
        lines.append(f"## Anchor: {summary.anchor_label}")
        lines.append(f"anchor_id: {summary.anchor_id}")
        lines.append(f"anchor_type: {summary.anchor_type}")
        lines.append(f"coverage_status: {summary.coverage_status}")
        lines.append(f"required_entry_visible: {str(summary.required_entry_visible).lower()}")
        lines.append(f"generated_count: {summary.generated_count}")
        lines.append(f"validated_correct_count: {summary.validated_correct_count}")
        lines.append(f"visible_count: {summary.visible_count}")
        lines.append(f"cache_servable_count: {summary.cache_servable_count}")
        lines.append(f"analysis_only_count: {summary.analysis_only_count}")
        lines.append(f"hard_reject_count: {summary.hard_reject_count}")
        lines.append("")
        lines.append("### Questions")
        lines.append("")
        for index, row in enumerate(rows_by_anchor[summary.anchor_id], 1):
            lines.append(f"{index}. {row.question_text}")
            lines.append(f"   - question_id: {row.question_id}")
            lines.append(f"   - type: {row.question_type}")
            lines.append(f"   - family: {row.question_family}")
            lines.append(f"   - mastery: {row.mastery_band}")
            lines.append(f"   - canonical: {str(row.canonical).lower()}")
            lines.append(f"   - alias: {str(row.alias).lower()}")
            if row.canonical_target:
                lines.append(f"   - canonical_target: {row.canonical_target}")
            lines.append(f"   - required_entry: {str(row.required_entry).lower()}")
            lines.append(f"   - tracked_topics: {row.tracked_topics}")
            lines.append(f"   - delivery_class: {row.delivery_class}")
            lines.append(f"   - visible: {str(row.visible).lower()}")
            if row.non_visible_reasons:
                lines.append(f"   - non_visible_reasons: {row.non_visible_reasons}")
            lines.append(f"   - tags: {row.tags}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
