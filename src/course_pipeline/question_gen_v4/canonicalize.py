from __future__ import annotations

import re
from difflib import SequenceMatcher

from course_pipeline.question_gen_v3.models import ScoredCandidate
from course_pipeline.question_gen_v4.policy_models import CanonicalGroup
from course_pipeline.utils import slugify


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def canonicalize(
    candidates: list[ScoredCandidate],
    config: dict,
) -> tuple[list[CanonicalGroup], dict[str, str], dict[str, list[str]]]:
    threshold = config["canonicalization"]["alias_similarity_threshold"]
    groups: list[CanonicalGroup] = []
    canonical_by_candidate: dict[str, str] = {}
    alias_ids_by_canonical: dict[str, list[str]] = {}
    sorted_candidates = sorted(candidates, key=lambda item: item.score.total, reverse=True)
    for candidate in sorted_candidates:
        assigned = False
        for group in groups:
            canonical_candidate = next(item for item in sorted_candidates if item.candidate.candidate_id == group.canonical_candidate_id)
            if candidate.candidate.topic_id != canonical_candidate.candidate.topic_id:
                continue
            similarity = SequenceMatcher(
                a=_norm(candidate.candidate.question_text),
                b=_norm(canonical_candidate.candidate.question_text),
            ).ratio()
            if similarity >= threshold:
                group.member_candidate_ids.append(candidate.candidate.candidate_id)
                if candidate.candidate.candidate_id != group.canonical_candidate_id:
                    group.alias_candidate_ids.append(candidate.candidate.candidate_id)
                    alias_ids_by_canonical.setdefault(group.canonical_candidate_id, []).append(candidate.candidate.candidate_id)
                canonical_by_candidate[candidate.candidate.candidate_id] = group.canonical_candidate_id
                assigned = True
                break
        if not assigned:
            gid = slugify(f"{candidate.candidate.topic_id}-{candidate.candidate.question_text}")[:80]
            groups.append(
                CanonicalGroup(
                    group_id=gid,
                    canonical_candidate_id=candidate.candidate.candidate_id,
                    member_candidate_ids=[candidate.candidate.candidate_id],
                    alias_candidate_ids=[],
                    rationale="Highest-scoring representative for this intent cluster.",
                )
            )
            canonical_by_candidate[candidate.candidate.candidate_id] = candidate.candidate.candidate_id
    return groups, canonical_by_candidate, alias_ids_by_canonical
