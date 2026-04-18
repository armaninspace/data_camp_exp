from __future__ import annotations

from course_pipeline.question_gen_v3.models import ScoredCandidate
from course_pipeline.question_gen_v4.policy_models import CacheEntry, PolicyDecision
from course_pipeline.utils import slugify


def build_cache_entries(
    candidates_by_id: dict[str, ScoredCandidate],
    decisions: list[PolicyDecision],
    answers_by_candidate_id: dict[str, str],
    alias_ids_by_canonical: dict[str, list[str]],
) -> list[CacheEntry]:
    entries: list[CacheEntry] = []
    for decision in decisions:
        if decision.policy_bucket not in {"curated_core", "cache_servable"}:
            continue
        candidate = candidates_by_id[decision.candidate_id]
        aliases = [
            candidates_by_id[alias_id].candidate.question_text
            for alias_id in alias_ids_by_canonical.get(decision.candidate_id, [])
            if alias_id in candidates_by_id
        ]
        entries.append(
            CacheEntry(
                cache_id=slugify(f"cache-{decision.candidate_id}")[:80],
                canonical_candidate_id=decision.candidate_id,
                canonical_question=candidate.candidate.question_text,
                canonical_answer=answers_by_candidate_id.get(decision.candidate_id, ""),
                alias_questions=aliases,
                source_refs=candidate.candidate.source_support,
                active=True,
            )
        )
    return entries
