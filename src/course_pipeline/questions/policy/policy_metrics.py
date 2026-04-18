from __future__ import annotations

from collections import Counter

from course_pipeline.questions.policy.models import CanonicalGroup, PolicyDecision


def compute_policy_metrics(decisions: list[PolicyDecision], canonical_groups: list[CanonicalGroup]) -> dict:
    buckets = Counter(decision.policy_bucket for decision in decisions)
    family_counts = Counter(tag for decision in decisions for tag in decision.family_tags)
    reason_counts = Counter(reason for decision in decisions for reason in decision.reason_codes)
    canonical_count = len(canonical_groups)
    alias_count = sum(len(group.alias_candidate_ids) for group in canonical_groups)
    total = len(decisions) or 1
    cache_servable_rate = (buckets["cache_servable"] + buckets["curated_core"]) / total
    analysis_only_rate = buckets["analysis_only"] / total
    hard_reject_rate = buckets["hard_reject"] / total
    entry_share = family_counts["entry"] / max(1, sum(family_counts.values()))
    friction_share = family_counts["friction"] / max(1, sum(family_counts.values()))
    return {
        "bucket_distribution": dict(buckets),
        "family_coverage": dict(family_counts),
        "canonical_count": canonical_count,
        "alias_count": alias_count,
        "curated_core_count": buckets["curated_core"],
        "cache_servable_rate": round(cache_servable_rate, 4),
        "analysis_only_rate": round(analysis_only_rate, 4),
        "hard_reject_rate": round(hard_reject_rate, 4),
        "entry_share": round(entry_share, 4),
        "friction_share": round(friction_share, 4),
        "top_reason_codes": dict(reason_counts.most_common(8)),
    }
