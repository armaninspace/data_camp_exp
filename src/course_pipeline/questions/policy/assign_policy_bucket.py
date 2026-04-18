from __future__ import annotations

from course_pipeline.questions.policy.models import PolicyDecision, PolicyScores


def validity_gate(scores: PolicyScores, config: dict) -> tuple[bool, list[str]]:
    thresholds = config["validity_thresholds"]
    reasons: list[str] = []
    valid = True
    if scores.correctness < thresholds["min_correctness"]:
        valid = False
        reasons.append("invalid_low_correctness")
    if scores.groundedness < thresholds["min_groundedness"]:
        valid = False
        reasons.append("invalid_low_groundedness")
    if scores.contradiction_risk > thresholds["max_contradiction_risk"]:
        valid = False
        reasons.append("invalid_contradiction_risk")
    if scores.coherence < thresholds["min_coherence"]:
        valid = False
        reasons.append("invalid_low_coherence")
    return valid, reasons


def _priority_score(item: dict) -> float:
    scores = item["scores"]
    family_tags = item["family_tags"].tags
    bonus = 0.0
    if "friction" in family_tags:
        bonus += 0.05
    if "diagnostic" in family_tags or "transfer" in family_tags:
        bonus += 0.04
    return (
        scores.pedagogical_value
        + 0.35 * scores.serviceability
        + 0.2 * scores.distinctiveness
        + bonus
    )


def _select_curated_candidate_ids(
    eligible_items: list[dict],
    config: dict,
) -> set[str]:
    if not eligible_items:
        return set()
    thresholds = config["curation_thresholds"]
    family_balance = config["family_balance"]
    max_curated = thresholds["max_curated_core_per_course"]
    selected_ids: list[str] = []
    protected_ids = [
        item["candidate"].candidate_id
        for item in sorted(eligible_items, key=_priority_score, reverse=True)
        if item.get("protected_entry")
    ]
    selected_ids.extend(protected_ids)

    def pick_best(predicate) -> None:
        for item in sorted(eligible_items, key=_priority_score, reverse=True):
            candidate_id = item["candidate"].candidate_id
            if candidate_id in selected_ids:
                continue
            if predicate(item):
                selected_ids.append(candidate_id)
                return

    pick_best(lambda item: "entry" in item["family_tags"].tags)
    pick_best(lambda item: "friction" in item["family_tags"].tags)
    pick_best(lambda item: "diagnostic" in item["family_tags"].tags or "transfer" in item["family_tags"].tags)

    for item in sorted(eligible_items, key=_priority_score, reverse=True):
        candidate_id = item["candidate"].candidate_id
        if candidate_id in selected_ids:
            continue
        non_protected_selected = sum(1 for item_id in selected_ids if item_id not in protected_ids)
        if non_protected_selected >= max_curated:
            break
        prospective_ids = selected_ids + [candidate_id]
        prospective_non_protected = [item_id for item_id in prospective_ids if item_id not in protected_ids]
        prospective_total = len(prospective_non_protected)
        prospective_entry = sum(
            1
            for row in eligible_items
            if row["candidate"].candidate_id in prospective_non_protected and "entry" in row["family_tags"].tags
        )
        if prospective_total and prospective_entry / prospective_total > family_balance["max_entry_share"]:
            continue
        selected_ids.append(candidate_id)
    return set(selected_ids)


def assign_policy_decisions(
    candidates: list[dict],
    config: dict,
) -> list[PolicyDecision]:
    curation_thresholds = config["curation_thresholds"]
    valid_cacheable: list[dict] = []
    hard_rejects: dict[str, PolicyDecision] = {}
    alias_decisions: dict[str, PolicyDecision] = {}
    quarantined_reasons: dict[str, list[str]] = {}

    for item in candidates:
        candidate = item["candidate"]
        scores = item["scores"]
        family_tags = item["family_tags"]
        canonical_id = item["canonical_id"]
        is_alias = item["is_alias"]
        servable = item["servable"]
        reason_codes = list(item["reason_codes"])
        valid, validity_reasons = validity_gate(scores, config)
        reason_codes.extend(validity_reasons)
        if not valid:
            hard_rejects[candidate.candidate_id] = PolicyDecision(
                candidate_id=candidate.candidate_id,
                canonical_id=canonical_id,
                family_tags=family_tags.tags,
                policy_bucket="hard_reject",
                servable=False,
                scores=scores,
                reason_codes=reason_codes or ["invalid_unsupported"],
            )
            continue
        if is_alias:
            reason_codes.append("alias_of_canonical")
            alias_decisions[candidate.candidate_id] = PolicyDecision(
                candidate_id=candidate.candidate_id,
                canonical_id=canonical_id,
                family_tags=family_tags.tags,
                policy_bucket="alias_only",
                servable=False,
                scores=scores,
                reason_codes=reason_codes,
            )
            continue
        can_curate = (
            servable
            and scores.pedagogical_value >= curation_thresholds["min_pedagogical_value"]
            and scores.distinctiveness >= curation_thresholds["min_distinctiveness"]
            and scores.answer_richness >= curation_thresholds["min_answer_richness"]
            and scores.groundedness >= curation_thresholds["min_groundedness_for_curation"]
            and scores.query_likelihood >= curation_thresholds["min_query_likelihood_for_curation"]
        )
        if item.get("protected_entry"):
            can_curate = True
        if not servable:
            quarantined_reasons[candidate.candidate_id] = reason_codes + ["quarantined_analysis_only"]
        elif not can_curate:
            quarantined_reasons[candidate.candidate_id] = reason_codes + ["not_distinct_enough_for_curation"]
        valid_cacheable.append(
            {
                **item,
                "curation_eligible": can_curate,
            }
        )

    curated_ids = _select_curated_candidate_ids(
        [item for item in valid_cacheable if item["curation_eligible"]],
        config,
    )

    decisions: list[PolicyDecision] = []
    for item in sorted(valid_cacheable, key=_priority_score, reverse=True):
        candidate = item["candidate"]
        scores = item["scores"]
        family_tags = item["family_tags"]
        canonical_id = item["canonical_id"]
        servable = item["servable"]
        reason_codes = list(item["reason_codes"])
        if candidate.candidate_id in curated_ids:
            reason_codes.append("curation_pass")
            decisions.append(
                PolicyDecision(
                    candidate_id=candidate.candidate_id,
                    canonical_id=canonical_id,
                    family_tags=family_tags.tags,
                    policy_bucket="curated_core",
                    servable=True,
                    scores=scores,
                    reason_codes=reason_codes,
                )
            )
            continue
        if servable:
            reason_codes = quarantined_reasons.get(candidate.candidate_id, reason_codes)
            decisions.append(
                PolicyDecision(
                    candidate_id=candidate.candidate_id,
                    canonical_id=canonical_id,
                    family_tags=family_tags.tags,
                    policy_bucket="cache_servable",
                    servable=True,
                    scores=scores,
                    reason_codes=reason_codes,
                )
            )
        else:
            reason_codes = quarantined_reasons.get(candidate.candidate_id, reason_codes)
            decisions.append(
                PolicyDecision(
                    candidate_id=candidate.candidate_id,
                    canonical_id=canonical_id,
                    family_tags=family_tags.tags,
                    policy_bucket="analysis_only",
                    servable=False,
                    scores=scores,
                    reason_codes=reason_codes,
                )
            )
    decisions.extend(alias_decisions.values())
    decisions.extend(hard_rejects.values())
    return sorted(decisions, key=lambda row: row.candidate_id)
