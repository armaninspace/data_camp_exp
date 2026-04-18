from __future__ import annotations

import re
from difflib import SequenceMatcher

from course_pipeline.question_gen_v3.models import QuestionCandidate, RejectedCandidate, TopicNode


GENERIC_TERMS = {"introduction", "overview", "data", "methods", "advanced methods"}


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def filter_candidates(
    candidates: list[QuestionCandidate],
    topics: list[TopicNode],
    config: dict,
) -> tuple[list[QuestionCandidate], list[RejectedCandidate]]:
    topic_map = {topic.topic_id: topic for topic in topics}
    kept: list[QuestionCandidate] = []
    rejected: list[RejectedCandidate] = []
    seen_questions: list[QuestionCandidate] = []
    for candidate in candidates:
        reasons: list[str] = []
        topic = topic_map.get(candidate.topic_id)
        if topic is None:
            reasons.append("unsupported")
        else:
            label = topic.label.lower().strip()
            if label in GENERIC_TERMS:
                reasons.append("broad_heading_paraphrase")
            if candidate.question_type == "definition" and topic.topic_type in {"decision_point", "comparison_axis"}:
                reasons.append("thin_answer")
            if candidate.mastery_band == "proficient" and candidate.question_type in {"definition", "orientation", "purpose"}:
                reasons.append("mastery_misaligned")
            if len(candidate.question_text.split()) < 4:
                reasons.append("malformed")
            if not candidate.source_support:
                reasons.append("unsupported")
            # reject weak repeats of already-seen questions
            norm = _normalized(candidate.question_text)
            for existing in seen_questions:
                if SequenceMatcher(a=norm, b=_normalized(existing.question_text)).ratio() > 0.94:
                    reasons.append("duplicate_intent")
                    break
        if reasons:
            rejected.append(RejectedCandidate(candidate=candidate, reasons=sorted(set(reasons))))
        else:
            kept.append(candidate)
            seen_questions.append(candidate)
    return kept, rejected
