from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.question_llm_schemas import DerivedCandidateRecord
from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    QuestionCandidate,
    TopicEdge,
    TopicNode,
)


EXPAND_SYSTEM_PROMPT = """You are a bounded pedagogical question generator.

Return JSON only.

Rules:
- Add only grounded learner questions supported by the course text.
- Fill high-value gaps, especially procedural, diagnostic, transfer, misconception, and comparison.
- Avoid near-duplicates and weak paraphrases.
- Do not invent unsupported techniques, workflows, or datasets.
- Do not replace foundational entry questions.
- Mark every returned question as a new derived candidate.
"""


def build_expand_payload(
    course: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    repaired_candidates: list[QuestionCandidate],
    foundational_anchor_labels: list[str],
) -> dict:
    frictions_by_topic: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        frictions_by_topic.setdefault(friction.topic_id, []).append(friction)
    edge_summary: dict[str, list[str]] = {}
    for edge in edges:
        edge_summary.setdefault(edge.source_id, []).append(f"{edge.relation}:{edge.target_id}")
        edge_summary.setdefault(edge.target_id, []).append(f"{edge.relation}:{edge.source_id}")
    pedagogy_map = {item.topic_id: item for item in pedagogy}
    return {
        "course": course.model_dump(mode="json"),
        "foundational_anchor_labels": foundational_anchor_labels,
        "existing_candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "topic_id": candidate.topic_id,
                "question_text": candidate.question_text,
                "question_type": candidate.question_type,
                "mastery_band": candidate.mastery_band,
                "source_support": candidate.source_support,
            }
            for candidate in repaired_candidates
        ],
        "topics": [
            {
                **topic.model_dump(mode="json"),
                "edge_summary": edge_summary.get(topic.topic_id, []),
                "pedagogy": pedagogy_map.get(topic.topic_id).model_dump(mode="json")
                if topic.topic_id in pedagogy_map
                else None,
                "frictions": [item.model_dump(mode="json") for item in frictions_by_topic.get(topic.topic_id, [])],
            }
            for topic in topics
        ],
    }


def _parse_expansions(content: str, course_id: str) -> list[DerivedCandidateRecord]:
    payload = json.loads(content)
    rows = payload.get("derived_candidates") or payload.get("expansions") or []
    parsed: list[DerivedCandidateRecord] = []
    for row in rows:
        try:
            parsed.append(
                DerivedCandidateRecord(
                    course_id=course_id,
                    question_text=row["question_text"],
                    question_family=row["question_family"],
                    question_type=row["question_type"],
                    mastery_band=row["mastery_band"],
                    anchor_label=row["anchor_label"],
                    derivation_reason=row.get("derivation_reason") or "llm_grounded_expansion",
                    grounding_rationale=row.get("grounding_rationale") or "",
                    confidence=float(row.get("confidence") or 0.0),
                    derived_by_llm=True,
                )
            )
        except Exception:
            continue
    return parsed


def expand_candidates_with_llm(
    *,
    settings: Settings | None,
    run_dir: Path | None,
    course: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    repaired_candidates: list[QuestionCandidate],
    foundational_anchor_labels: list[str],
) -> tuple[list[DerivedCandidateRecord], dict]:
    payload = build_expand_payload(course, topics, edges, pedagogy, frictions, repaired_candidates, foundational_anchor_labels)
    if not settings or not settings.openai_api_key or run_dir is None:
        return [], payload

    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="candidate_expand",
        prompt_version="candidate_expand_v1",
    )
    try:
        content = client.invoke_json(
            EXPAND_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, indent=2),
            course_id=course.doc_id,
            entity_ids=[candidate.candidate_id for candidate in repaired_candidates],
        )
    except Exception:
        return [], payload
    return _parse_expansions(content, course.doc_id), payload
