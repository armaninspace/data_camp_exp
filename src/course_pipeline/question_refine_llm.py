from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.foundational_entry_questions import plain_definition_question
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.question_llm_schemas import CandidateRepairRecord
from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    QuestionCandidate,
    TopicEdge,
    TopicNode,
)


REPAIR_SYSTEM_PROMPT = """You are a bounded question editor for learner-facing course questions.

Return JSON only.

Rules:
- Keep natural grounded questions unchanged.
- Rewrite awkward or underspecified questions only when wording improves.
- Drop irreparable questions with an explicit reason.
- Do not invent unsupported content.
- Do not remove required foundational entry questions.
- Do not replace plain beginner definitions for foundational anchors with richer variants.
- Every input candidate must end in exactly one state: keep, rewrite, or drop.
"""


def build_repair_payload(
    course: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    candidates: list[QuestionCandidate],
    foundational_anchor_labels: list[str],
) -> dict:
    topic_map = {topic.topic_id: topic for topic in topics}
    pedagogy_map = {item.topic_id: item for item in pedagogy}
    frictions_by_topic: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        frictions_by_topic.setdefault(friction.topic_id, []).append(friction)
    edge_summary: dict[str, list[str]] = {}
    for edge in edges:
        edge_summary.setdefault(edge.source_id, []).append(f"{edge.relation}:{edge.target_id}")
        edge_summary.setdefault(edge.target_id, []).append(f"{edge.relation}:{edge.source_id}")
    return {
        "course": course.model_dump(mode="json"),
        "foundational_anchor_labels": foundational_anchor_labels,
        "candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "topic_id": candidate.topic_id,
                "topic_label": topic_map[candidate.topic_id].label if candidate.topic_id in topic_map else candidate.topic_id,
                "slot": candidate.slot,
                "mastery_band": candidate.mastery_band,
                "question_type": candidate.question_type,
                "question_text": candidate.question_text,
                "source_support": candidate.source_support,
                "linked_frictions": [
                    friction.model_dump(mode="json")
                    for friction in frictions_by_topic.get(candidate.topic_id, [])
                ],
                "pedagogy": pedagogy_map.get(candidate.topic_id).model_dump(mode="json")
                if candidate.topic_id in pedagogy_map
                else None,
                "edge_summary": edge_summary.get(candidate.topic_id, []),
                "protected_plain_definition": (
                    candidate.question_type == "definition"
                    and candidate.question_text
                    == plain_definition_question(topic_map[candidate.topic_id].label)
                    if candidate.topic_id in topic_map
                    else False
                ),
            }
            for candidate in candidates
        ],
    }


def _fallback_repairs(course_id: str, candidates: list[QuestionCandidate], reason: str) -> list[CandidateRepairRecord]:
    return [
        CandidateRepairRecord(
            course_id=course_id,
            source_question_id=candidate.candidate_id,
            action="keep",
            original_question=candidate.question_text,
            repaired_question=candidate.question_text,
            repair_reason=reason,
            grounding_rationale="Original heuristic candidate preserved.",
            confidence=1.0,
            derived_by_llm=False,
        )
        for candidate in candidates
    ]


def _parse_repairs(content: str, course_id: str, candidates: list[QuestionCandidate]) -> list[CandidateRepairRecord]:
    payload = json.loads(content)
    rows = payload.get("repairs") or []
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    parsed: list[CandidateRepairRecord] = []
    for row in rows:
        candidate_id = row.get("source_question_id") or row.get("candidate_id")
        candidate = candidate_by_id.get(str(candidate_id))
        if candidate is None:
            continue
        parsed.append(
            CandidateRepairRecord(
                course_id=course_id,
                source_question_id=candidate.candidate_id,
                action=row.get("action") or "keep",
                original_question=candidate.question_text,
                repaired_question=row.get("repaired_question"),
                repair_reason=row.get("repair_reason") or "llm_repair",
                grounding_rationale=row.get("grounding_rationale") or "",
                confidence=float(row.get("confidence") or 0.0),
                derived_by_llm=False,
            )
        )
    parsed_ids = {row.source_question_id for row in parsed}
    for candidate in candidates:
        if candidate.candidate_id not in parsed_ids:
            parsed.append(
                CandidateRepairRecord(
                    course_id=course_id,
                    source_question_id=candidate.candidate_id,
                    action="keep",
                    original_question=candidate.question_text,
                    repaired_question=candidate.question_text,
                    repair_reason="implicit_keep",
                    grounding_rationale="Candidate omitted from LLM response; kept conservatively.",
                    confidence=0.0,
                    derived_by_llm=False,
                )
            )
    return parsed


def _enforce_protected_entry_repairs(
    repairs: list[CandidateRepairRecord],
    candidates: list[QuestionCandidate],
    topics: list[TopicNode],
) -> list[CandidateRepairRecord]:
    topic_by_id = {topic.topic_id: topic for topic in topics}
    protected_questions = {
        candidate.candidate_id: plain_definition_question(topic_by_id[candidate.topic_id].label)
        for candidate in candidates
        if candidate.topic_id in topic_by_id
        and candidate.question_type == "definition"
        and candidate.question_text == plain_definition_question(topic_by_id[candidate.topic_id].label)
    }
    normalized: list[CandidateRepairRecord] = []
    for repair in repairs:
        protected_question = protected_questions.get(repair.source_question_id)
        if protected_question is None:
            normalized.append(repair)
            continue
        if repair.action == "drop":
            normalized.append(
                repair.model_copy(
                    update={
                        "action": "keep",
                        "repaired_question": protected_question,
                        "repair_reason": "protected_required_entry_kept",
                        "grounding_rationale": "Required plain definition was preserved deterministically.",
                        "confidence": max(repair.confidence, 1.0),
                    }
                )
            )
            continue
        normalized.append(
            repair.model_copy(
                update={
                    "repaired_question": protected_question,
                }
            )
        )
    return normalized


def repair_candidates_with_llm(
    *,
    settings: Settings | None,
    run_dir: Path | None,
    course: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    candidates: list[QuestionCandidate],
    foundational_anchor_labels: list[str],
) -> tuple[list[CandidateRepairRecord], dict]:
    payload = build_repair_payload(course, topics, edges, pedagogy, frictions, candidates, foundational_anchor_labels)
    if not settings or not settings.openai_api_key or run_dir is None:
        return _fallback_repairs(course.doc_id, candidates, "llm_repair_bypassed_no_openai_key"), payload

    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="candidate_repair",
        prompt_version="candidate_repair_v1",
    )
    try:
        content = client.invoke_json(
            REPAIR_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, indent=2),
            course_id=course.doc_id,
            entity_ids=[candidate.candidate_id for candidate in candidates],
        )
    except Exception:
        return _fallback_repairs(course.doc_id, candidates, "llm_repair_failed_fallback"), payload
    repairs = _parse_repairs(content, course.doc_id, candidates)
    return _enforce_protected_entry_repairs(repairs, candidates, topics), payload
