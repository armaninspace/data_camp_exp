from __future__ import annotations

import re

from course_pipeline.semantic_schemas import (
    AliasGroupRecord,
    AnchorCandidate,
    FrictionRecord,
    SemanticDecisionRecord,
    SemanticValidationReport,
    TopicRecord,
)
from course_pipeline.utils import slugify


GENERIC_LABELS = {
    "introduction",
    "overview",
    "advanced methods",
    "methods",
    "data",
}


def validate_and_sanitize_semantics(
    *,
    course_id: str,
    topic_records: list[TopicRecord],
    anchor_candidates: list[AnchorCandidate],
    alias_groups: list[AliasGroupRecord],
    friction_records: list[FrictionRecord] | None = None,
) -> dict:
    friction_records = friction_records or []
    topic_by_id = {record.topic_id: record for record in topic_records}
    kept_topics: list[TopicRecord] = []
    kept_anchors: list[AnchorCandidate] = []
    kept_alias_groups: list[AliasGroupRecord] = []
    kept_friction_records: list[FrictionRecord] = []
    decisions: list[SemanticDecisionRecord] = []
    warnings: list[str] = []

    merged_anchor_count = 0
    suspicious_anchor_count = 0
    rewritten_count = 0

    canonical_anchor_by_label: dict[str, AnchorCandidate] = {}
    dropped_topic_ids: set[str] = set()
    kept_anchor_ids: set[str] = set()

    for topic in topic_records:
        label_check = _label_quality_reason(topic.label)
        if label_check is None:
            kept_topics.append(topic)
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="topic",
                    entity_id=topic.topic_id,
                    action="keep",
                    reason="topic_label_passed_sanitation",
                    source_fields=list(topic.source_fields),
                    evidence_spans=list(topic.evidence_spans),
                    confidence=topic.confidence,
                )
            )
            continue
        dropped_topic_ids.add(topic.topic_id)
        suspicious_anchor_count += 1
        warnings.append(f"dropped topic `{topic.label}`: {label_check}")
        decisions.append(
            SemanticDecisionRecord(
                course_id=course_id,
                entity_type="topic",
                entity_id=topic.topic_id,
                action="drop",
                reason=label_check,
                provenance_note="Rejected during deterministic semantic sanitation.",
                source_fields=list(topic.source_fields),
                evidence_spans=list(topic.evidence_spans),
                confidence=topic.confidence,
            )
        )

    for anchor in anchor_candidates:
        label_check = _label_quality_reason(anchor.label)
        if label_check is not None:
            suspicious_anchor_count += 1
            warnings.append(f"dropped anchor `{anchor.label}`: {label_check}")
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="anchor",
                    entity_id=anchor.anchor_id,
                    action="drop",
                    reason=label_check,
                    provenance_note="Rejected during deterministic semantic sanitation.",
                    source_fields=list(anchor.source_fields),
                    evidence_spans=list(anchor.evidence_spans),
                    confidence=anchor.confidence,
                )
            )
            continue
        if anchor.anchor_id in dropped_topic_ids:
            warnings.append(f"dropped anchor `{anchor.label}` because topic `{anchor.anchor_id}` was removed")
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="anchor",
                    entity_id=anchor.anchor_id,
                    action="drop",
                    reason="topic_removed_during_sanitation",
                    provenance_note="Anchor removed with its topic.",
                    source_fields=list(anchor.source_fields),
                    evidence_spans=list(anchor.evidence_spans),
                    confidence=anchor.confidence,
                )
            )
            continue

        normalized_label = slugify(anchor.label)
        dedupe_key = _dedupe_anchor_key(anchor.label)
        existing = canonical_anchor_by_label.get(normalized_label)
        if existing is None:
            existing = canonical_anchor_by_label.get(dedupe_key)
        sanitized_anchor = anchor.model_copy(update={"normalized_label": normalized_label})
        eligibility_reason = _entry_anchor_eligibility_reason(sanitized_anchor)
        if sanitized_anchor.requires_entry_question and eligibility_reason is not None:
            sanitized_anchor = sanitized_anchor.model_copy(update={"requires_entry_question": False})
            rewritten_count += 1
            warnings.append(f"demoted required-entry anchor `{sanitized_anchor.label}`: {eligibility_reason}")
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="anchor",
                    entity_id=sanitized_anchor.anchor_id,
                    action="rewrite",
                    reason=eligibility_reason,
                    provenance_note="Deterministic anchor eligibility rules demoted entry coverage requirement.",
                    source_fields=list(sanitized_anchor.source_fields),
                    evidence_spans=list(sanitized_anchor.evidence_spans),
                    confidence=sanitized_anchor.confidence,
                )
            )
        if existing is None:
            canonical_anchor_by_label[normalized_label] = sanitized_anchor
            canonical_anchor_by_label[dedupe_key] = sanitized_anchor
            kept_anchors.append(sanitized_anchor)
            kept_anchor_ids.add(sanitized_anchor.anchor_id)
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="anchor",
                    entity_id=sanitized_anchor.anchor_id,
                    action="keep",
                    reason="anchor_label_passed_sanitation",
                    source_fields=list(sanitized_anchor.source_fields),
                    evidence_spans=list(sanitized_anchor.evidence_spans),
                    confidence=sanitized_anchor.confidence,
                )
            )
            continue

        merged_anchor_count += 1
        warnings.append(
            f"merged near-duplicate anchor `{anchor.label}` into `{existing.label}`"
        )
        decisions.append(
            SemanticDecisionRecord(
                course_id=course_id,
                entity_type="anchor",
                entity_id=anchor.anchor_id,
                action="merge",
                reason="near_duplicate_normalized_label",
                provenance_note="Merged conservatively by normalized label.",
                source_fields=list(anchor.source_fields),
                evidence_spans=list(anchor.evidence_spans),
                confidence=anchor.confidence,
                merged_into_id=existing.anchor_id,
            )
        )

    for alias_group in alias_groups:
        canonical_slug = slugify(alias_group.canonical_label)
        if canonical_slug in GENERIC_LABELS or canonical_slug.startswith("overview-segment-"):
            suspicious_anchor_count += 1
            warnings.append(f"dropped alias group `{alias_group.canonical_label}`")
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="alias_group",
                    entity_id=canonical_slug or alias_group.canonical_label,
                    action="drop",
                    reason="alias_group_canonical_label_failed_sanitation",
                    provenance_note="Alias group removed because canonical label is not learner-facing.",
                    source_fields=list(alias_group.source_fields),
                    evidence_spans=list(alias_group.evidence_spans),
                    confidence=alias_group.confidence,
                )
            )
            continue
        kept_alias_groups.append(alias_group)
        decisions.append(
            SemanticDecisionRecord(
                course_id=course_id,
                entity_type="alias_group",
                entity_id=canonical_slug or alias_group.canonical_label,
                action="keep",
                reason="alias_group_passed_sanitation",
                source_fields=list(alias_group.source_fields),
                evidence_spans=list(alias_group.evidence_spans),
                confidence=alias_group.confidence,
            )
        )

    for friction in friction_records:
        if friction.anchor_id not in kept_anchor_ids:
            decisions.append(
                SemanticDecisionRecord(
                    course_id=course_id,
                    entity_type="friction",
                    entity_id=f"{friction.anchor_id}:{friction.friction_type}",
                    action="drop",
                    reason="anchor_removed_during_sanitation",
                    provenance_note="Friction removed because its anchor did not survive sanitation.",
                    source_fields=list(friction.source_fields),
                    evidence_spans=list(friction.evidence_spans),
                    confidence=friction.confidence,
                )
            )
            continue
        kept_friction_records.append(friction)
        decisions.append(
            SemanticDecisionRecord(
                course_id=course_id,
                entity_type="friction",
                entity_id=f"{friction.anchor_id}:{friction.friction_type}",
                action="keep",
                reason="friction_anchor_passed_sanitation",
                source_fields=list(friction.source_fields),
                evidence_spans=list(friction.evidence_spans),
                confidence=friction.confidence,
            )
        )

    report = SemanticValidationReport(
        course_id=course_id,
        topic_count=len(topic_records),
        anchor_count=len(anchor_candidates),
        alias_group_count=len(alias_groups),
        friction_count=len(friction_records),
        kept_count=sum(1 for decision in decisions if decision.action == "keep"),
        dropped_count=sum(1 for decision in decisions if decision.action == "drop"),
        merged_count=sum(1 for decision in decisions if decision.action == "merge"),
        rewritten_count=rewritten_count,
        suspicious_anchor_count=suspicious_anchor_count,
        warnings=warnings,
        decisions=decisions,
    )
    return {
        "topic_records": kept_topics,
        "anchor_candidates": kept_anchors,
        "alias_groups": kept_alias_groups,
        "friction_records": kept_friction_records,
        "report": report,
        "kept_anchor_ids": sorted(kept_anchor_ids),
        "merged_anchor_count": merged_anchor_count,
    }


def _label_quality_reason(label: str) -> str | None:
    normalized = label.strip().lower()
    if not normalized:
        return "empty_label"
    if "http://" in normalized or "https://" in normalized or "www." in normalized or ".com" in normalized:
        return "domain_or_url_like_label"
    if re.match(r"overview[- ]segment[- ]\d+", normalized):
        return "placeholder_overview_segment_label"
    if normalized in GENERIC_LABELS:
        return "generic_non_pedagogical_label"
    return None


def _dedupe_anchor_key(label: str) -> str:
    normalized = slugify(label)
    normalized = re.sub(r"-(models?|methods?|tests?)$", "", normalized)
    return normalized


def _entry_anchor_eligibility_reason(anchor: AnchorCandidate) -> str | None:
    if not anchor.requires_entry_question:
        return None
    if not anchor.foundational_candidate or not anchor.learner_facing:
        return "entry_requirement_removed_non_foundational_or_non_learner_facing"
    if anchor.confidence < 0.72:
        return "entry_requirement_removed_low_confidence"
    structural_fields = {"sections", "chapters", "section_title", "chapter_title", "course_structure"}
    source_fields = {field.strip().lower() for field in anchor.source_fields}
    has_structural_support = bool(source_fields & structural_fields)
    repeated_support = len(source_fields) >= 2 or len({span.excerpt.strip() for span in anchor.evidence_spans if span.excerpt.strip()}) >= 2
    summary_only = bool(source_fields) and source_fields <= {"summary", "overview", "learning_outcomes", "skills"}
    if summary_only and not has_structural_support and not repeated_support and anchor.confidence < 0.9:
        return "entry_requirement_removed_incidental_summary_only_support"
    return None
