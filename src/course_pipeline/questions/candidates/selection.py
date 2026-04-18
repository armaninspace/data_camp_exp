from __future__ import annotations

from collections import Counter

from course_pipeline.questions.candidates.models import ScoredCandidate, SelectionSummary


ADVANCED_TYPES = {"comparison", "diagnostic", "transfer", "misconception", "interpretation"}


def select_final(
    scored: list[ScoredCandidate],
    config: dict,
    target_n: int,
    rejected_count: int = 0,
    duplicate_cluster_count: int = 0,
) -> tuple[list[ScoredCandidate], SelectionSummary]:
    thresholds = config["thresholds"]
    quotas = config["quotas"]
    eligible = [
        candidate
        for candidate in sorted(scored, key=lambda item: item.score.total, reverse=True)
        if candidate.score.groundedness >= thresholds["min_groundedness_for_selection"]
        and candidate.score.total >= thresholds["min_total_score_for_selection"]
    ]
    selected: list[ScoredCandidate] = []
    type_counts: Counter[str] = Counter()
    mastery_counts: Counter[str] = Counter()
    friction_count = 0
    for candidate in eligible:
        if len(selected) >= target_n:
            break
        ctype = candidate.candidate.question_type
        prospective_n = len(selected) + 1
        if ctype == "definition" and (type_counts["definition"] + 1) / prospective_n > quotas["max_definition_share"]:
            continue
        selected.append(candidate)
        type_counts[ctype] += 1
        mastery_counts[candidate.candidate.mastery_band] += 1
        if candidate.candidate.linked_friction_ids:
            friction_count += 1

    # quota repair passes
    def _fill(predicate):
        nonlocal friction_count
        for candidate in eligible:
            if len(selected) >= target_n:
                return
            if candidate in selected:
                continue
            if predicate(candidate):
                selected.append(candidate)
                type_counts[candidate.candidate.question_type] += 1
                mastery_counts[candidate.candidate.mastery_band] += 1
                if candidate.candidate.linked_friction_ids:
                    friction_count += 1

    if selected:
        min_friction = max(1, int(round(target_n * quotas["min_friction_share"])))
        if friction_count < min_friction:
            _fill(lambda item: bool(item.candidate.linked_friction_ids))
        min_advanced = max(1, int(round(target_n * quotas["min_advanced_share"])))
        current_advanced = sum(type_counts[t] for t in ADVANCED_TYPES)
        if current_advanced < min_advanced:
            _fill(lambda item: item.candidate.question_type in ADVANCED_TYPES)
        min_prof = max(1, int(round(target_n * quotas["min_proficient_share"])))
        if mastery_counts["proficient"] < min_prof:
            _fill(lambda item: item.candidate.mastery_band == "proficient")

    selected = selected[:target_n]
    type_counts = Counter(item.candidate.question_type for item in selected)
    mastery_counts = Counter(item.candidate.mastery_band for item in selected)
    friction_rate = (sum(1 for item in selected if item.candidate.linked_friction_ids) / len(selected)) if selected else 0.0
    quotas_met = {
        "max_definition_share": (type_counts["definition"] / len(selected)) <= quotas["max_definition_share"] if selected else True,
        "min_friction_share": friction_rate >= quotas["min_friction_share"] if selected else False,
        "min_advanced_share": (sum(type_counts[t] for t in ADVANCED_TYPES) / len(selected)) >= quotas["min_advanced_share"] if selected else False,
        "min_proficient_share": (mastery_counts["proficient"] / len(selected)) >= quotas["min_proficient_share"] if selected else False,
    }
    summary = SelectionSummary(
        target_n=target_n,
        selected_count=len(selected),
        candidate_count=len(scored),
        rejected_count=rejected_count,
        duplicate_cluster_count=duplicate_cluster_count,
        quotas_requested=quotas,
        quotas_met=quotas_met,
        type_distribution=dict(type_counts),
        mastery_distribution=dict(mastery_counts),
        friction_linked_selection_rate=round(friction_rate, 4),
    )
    return selected, summary
