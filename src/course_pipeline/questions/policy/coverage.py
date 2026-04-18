from __future__ import annotations

from course_pipeline.questions.policy.models import CandidateRecord, CoverageWarning
from course_pipeline.utils import slugify


def audit_anchor_coverage(
    anchors: dict[str, object],
    records: list[CandidateRecord],
) -> list[CoverageWarning]:
    warnings: list[CoverageWarning] = []
    records_by_topic: dict[str, list[CandidateRecord]] = {}
    for record in records:
        for topic_id in record.topic_ids:
            records_by_topic.setdefault(topic_id, []).append(record)

    for concept_id, topic in anchors.items():
        candidates = records_by_topic.get(concept_id, [])
        definition_candidates = [row for row in candidates if row.is_required_entry_candidate]
        visible_canonical = [
            row for row in definition_candidates if row.visible and row.is_canonical and row.delivery_class == "curated_visible"
        ]
        if visible_canonical:
            continue

        warning_type = "missing_visible_canonical_entry"
        has_hidden_correct_variants = False
        candidate_ids: list[str] = []
        message = f"Foundational anchor '{topic.label}' lacks a visible canonical entry question."

        if not definition_candidates:
            warning_type = "definition_generation_failed"
            message = f"Foundational anchor '{topic.label}' has no generated definition candidate."
        else:
            candidate_ids = [row.candidate_id for row in definition_candidates]
            hidden_correct = [row for row in definition_candidates if row.delivery_class in {"cache_servable", "analysis_only"}]
            alias_only = [row for row in definition_candidates if row.delivery_class == "alias_only"]
            has_hidden_correct_variants = bool(hidden_correct or alias_only)
            if alias_only and not hidden_correct:
                warning_type = "only_alias_entry_exists"
                message = f"Foundational anchor '{topic.label}' only has alias entry variants and no visible canonical definition."
            elif hidden_correct:
                warning_type = "only_hidden_correct_entry_exists"
                message = f"Foundational anchor '{topic.label}' has hidden correct definition variants but no visible canonical entry."

        warnings.append(
            CoverageWarning(
                warning_id=slugify(f"{concept_id}-{warning_type}")[:80],
                concept_id=concept_id,
                concept_label=topic.label,
                warning_type=warning_type,
                has_hidden_correct_variants=has_hidden_correct_variants,
                candidate_ids=candidate_ids,
                message=message,
            )
        )
    return warnings
