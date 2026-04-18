from __future__ import annotations

import re
from difflib import SequenceMatcher

from course_pipeline.questions.candidates.models import DuplicateCluster, ScoredCandidate


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def dedupe_candidates(
    scored: list[ScoredCandidate],
    config: dict,
) -> tuple[list[ScoredCandidate], list[DuplicateCluster]]:
    threshold = config["thresholds"]["semantic_duplicate_threshold"]
    kept: list[ScoredCandidate] = []
    clusters: list[DuplicateCluster] = []
    for candidate in sorted(scored, key=lambda item: item.score.total, reverse=True):
        duplicate_of = None
        for existing in kept:
            similarity = SequenceMatcher(
                a=_norm(candidate.candidate.question_text),
                b=_norm(existing.candidate.question_text),
            ).ratio()
            if similarity >= threshold:
                duplicate_of = existing
                break
        if duplicate_of is None:
            kept.append(candidate)
        else:
            clusters.append(
                DuplicateCluster(
                    kept_candidate_id=duplicate_of.candidate.candidate_id,
                    duplicate_candidate_ids=[candidate.candidate.candidate_id],
                    rationale="Semantically near-duplicate candidate with lower score.",
                )
            )
    return kept, clusters
