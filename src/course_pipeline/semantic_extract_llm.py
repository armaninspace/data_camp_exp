from __future__ import annotations

import json
import re
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.questions.candidates.extract_edges import extract_edges
from course_pipeline.questions.candidates.extract_pedagogy import extract_pedagogy
from course_pipeline.questions.candidates.extract_topics import extract_topics
from course_pipeline.questions.candidates.mine_friction import mine_friction
from course_pipeline.questions.candidates.models import CanonicalDocument, FrictionPoint, TopicNode
from course_pipeline.questions.candidates.normalize import normalize_document
from course_pipeline.questions.policy.anchors import detect_foundational_anchors
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.semantic_schemas import (
    AliasGroupRecord,
    AnchorCandidate,
    EvidenceSpan,
    FrictionRecord,
    TopicRecord,
)
from course_pipeline.utils import slugify


SEMANTIC_EXTRACT_SYSTEM_PROMPT = """You extract structured learner-facing course semantics.

Return JSON only.

Rules:
- Stay grounded in the supplied course fields.
- Do not invent unsupported concepts.
- Every extracted item must cite source_fields and evidence_spans.
- Prefer learner-facing labels over internal or website-like labels.
- Reject placeholders, domains, and raw URL fragments.
"""


def build_semantic_extract_payload(course: CanonicalDocument) -> dict:
    return {
        "course": {
            "course_id": course.doc_id,
            "title": course.title,
            "summary": course.summary,
            "overview": course.overview,
            "level": course.level,
            "subjects": course.subjects,
            "sections": [section.model_dump(mode="json") for section in course.sections],
        }
    }


def extract_semantics_with_llm(
    *,
    raw_course: NormalizedCourse,
    settings: Settings | None,
    run_dir: Path | None,
) -> dict:
    course = normalize_document(raw_course)
    payload = build_semantic_extract_payload(course)
    if not settings or not settings.openai_api_key or run_dir is None:
        return _fallback_semantic_result(raw_course, course, payload, reason="llm_semantic_extract_bypassed_no_openai_key")

    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="semantic_extract",
        prompt_version="semantic_extract_v1",
    )
    try:
        content = client.invoke_json(
            SEMANTIC_EXTRACT_SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False, indent=2),
            course_id=raw_course.course_id,
            entity_ids=[raw_course.course_id],
        )
    except Exception:
        return _fallback_semantic_result(raw_course, course, payload, reason="llm_semantic_extract_failed_fallback")
    try:
        parsed = _parse_semantic_extract_response(content, raw_course.course_id)
    except Exception:
        return _fallback_semantic_result(raw_course, course, payload, reason="llm_semantic_extract_parse_failed_fallback")
    if not parsed["topic_records"] and not parsed["anchor_candidates"]:
        return _fallback_semantic_result(raw_course, course, payload, reason="llm_semantic_extract_empty_fallback")
    return {
        "normalized_document": course,
        "payload": payload,
        "topic_records": parsed["topic_records"],
        "anchor_candidates": parsed["anchor_candidates"],
        "alias_groups": parsed["alias_groups"],
        "friction_records": parsed["friction_records"],
        "extraction_mode": "llm",
    }


def _parse_semantic_extract_response(content: str, course_id: str) -> dict:
    payload = json.loads(content)
    semantic_payload = payload.get("course_semantics")
    if isinstance(semantic_payload, dict):
        payload = semantic_payload
    topic_rows = payload.get("topics", [])
    anchor_rows = payload.get("anchors", [])
    alias_rows = payload.get("alias_groups", [])
    friction_rows = payload.get("frictions", [])

    if topic_rows and not anchor_rows and isinstance(topic_rows[0], dict) and "topic" in topic_rows[0]:
        coerced = _coerce_loose_semantic_payload(payload, course_id)
        topic_rows = coerced["topics"]
        anchor_rows = coerced["anchors"]
        alias_rows = coerced["alias_groups"]
        friction_rows = coerced["frictions"]

    topic_records = [TopicRecord.model_validate(row | {"course_id": course_id}) for row in topic_rows]
    anchor_candidates = [AnchorCandidate.model_validate(row | {"course_id": course_id}) for row in anchor_rows]
    alias_groups = [AliasGroupRecord.model_validate(row | {"course_id": course_id}) for row in alias_rows]
    friction_records = [FrictionRecord.model_validate(row | {"course_id": course_id}) for row in friction_rows]
    return {
        "topic_records": topic_records,
        "anchor_candidates": anchor_candidates,
        "alias_groups": alias_groups,
        "friction_records": friction_records,
    }


def _coerce_loose_semantic_payload(payload: dict, course_id: str) -> dict:
    topics: list[dict] = []
    anchors: list[dict] = []
    alias_groups: list[dict] = []
    frictions: list[dict] = []
    for row in payload.get("topics", []):
        label = str(row.get("topic") or "").strip()
        if not label:
            continue
        topic_id = slugify(label)
        evidence_spans = _coerce_evidence_spans(row.get("source_fields", []), row.get("evidence_spans", []))
        topic_type = _guess_topic_type_from_label(label)
        confidence = float(row.get("confidence") or 0.72)
        topic_payload = {
            "topic_id": topic_id,
            "label": label,
            "aliases": row.get("aliases") or [],
            "topic_type": topic_type,
            "description": _coerce_description(row, label),
            "source_fields": list(row.get("source_fields") or []),
            "evidence_spans": evidence_spans,
            "confidence": confidence,
        }
        topics.append(topic_payload)
        foundational = topic_type in {"concept", "tool", "metric", "diagnostic", "comparison_axis", "decision_point"}
        anchors.append(
            {
                "anchor_id": topic_id,
                "label": label,
                "normalized_label": slugify(label),
                "anchor_type": _anchor_type_for_topic_type(topic_type),
                "foundational_candidate": foundational,
                "learner_facing": True,
                "requires_entry_question": foundational,
                "rationale": "Coerced from loose semantic extraction topic response.",
                "source_fields": list(row.get("source_fields") or []),
                "evidence_spans": evidence_spans,
                "confidence": confidence,
            }
        )
    return {
        "topics": topics,
        "anchors": anchors,
        "alias_groups": alias_groups,
        "frictions": frictions,
    }


def _coerce_evidence_spans(source_fields: list, evidence_spans: list) -> list[dict]:
    if evidence_spans and isinstance(evidence_spans[0], dict):
        return list(evidence_spans)
    fields = [str(field) for field in source_fields] or ["overview"]
    spans = [str(span) for span in evidence_spans if str(span).strip()]
    if not spans:
        spans = [""]
    rows: list[dict] = []
    for index, span in enumerate(spans):
        rows.append({"field": fields[min(index, len(fields) - 1)], "excerpt": span})
    return rows


def _coerce_description(row: dict, label: str) -> str:
    for key in ("description", "summary", "rationale"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    evidence_spans = row.get("evidence_spans") or []
    if evidence_spans:
        first = evidence_spans[0]
        if isinstance(first, dict):
            return str(first.get("excerpt") or label)
        return str(first)
    return label


def _guess_topic_type_from_label(label: str) -> str:
    lower = label.lower()
    if any(term in lower for term in ["compare", "comparison", "different", "difference", "versus", "benchmark"]):
        return "comparison_axis"
    if any(term in lower for term in ["matrix", "vector", "list", "frame", "console", "calculator", "create", "select", "assign", "order"]):
        return "procedure"
    if any(term in lower for term in ["factor", "metric", "accuracy", "rate", "score"]):
        return "metric"
    if any(term in lower for term in ["diagnostic", "test", "check", "validate"]):
        return "diagnostic"
    if re.fullmatch(r"[a-z]\b|r\b", lower):
        return "tool"
    return "concept"


def _anchor_type_for_topic_type(topic_type: str) -> str:
    if topic_type == "concept":
        return "foundational_vocabulary"
    if topic_type in {"procedure", "tool", "metric", "diagnostic", "comparison_axis", "failure_mode", "decision_point"}:
        return topic_type
    return "contextual_topic"


def _fallback_semantic_result(
    raw_course: NormalizedCourse,
    course: CanonicalDocument,
    payload: dict,
    *,
    reason: str,
) -> dict:
    topics = extract_topics(course)
    edges = extract_edges(course, topics)
    pedagogy = extract_pedagogy(course, topics, edges)
    frictions = mine_friction(topics, edges, pedagogy)
    return {
        "normalized_document": course,
        "payload": payload,
        "topic_records": [_topic_record_from_topic(raw_course, topic) for topic in topics],
        "anchor_candidates": _anchor_candidates_from_topics(raw_course, topics),
        "alias_groups": _alias_groups_from_topics(raw_course, topics),
        "friction_records": [_friction_record_from_point(raw_course, point, topics) for point in frictions],
        "extraction_mode": reason,
    }


def _topic_record_from_topic(raw_course: NormalizedCourse, topic: TopicNode) -> TopicRecord:
    evidence = _evidence_spans_for_topic(raw_course, topic)
    return TopicRecord(
        course_id=raw_course.course_id,
        topic_id=topic.topic_id,
        label=topic.label,
        aliases=list(topic.aliases),
        topic_type=topic.topic_type,
        description=topic.description,
        source_fields=sorted({span.field for span in evidence}),
        evidence_spans=evidence,
        confidence=topic.confidence,
    )


def _anchor_candidates_from_topics(raw_course: NormalizedCourse, topics: list[TopicNode]) -> list[AnchorCandidate]:
    foundational = detect_foundational_anchors(topics)
    records: list[AnchorCandidate] = []
    for topic in topics:
        evidence = _evidence_spans_for_topic(raw_course, topic)
        foundational_candidate = topic.topic_id in foundational
        records.append(
            AnchorCandidate(
                course_id=raw_course.course_id,
                anchor_id=topic.topic_id,
                label=topic.label,
                normalized_label=slugify(topic.label),
                anchor_type=_anchor_type_for_topic(topic),
                foundational_candidate=foundational_candidate,
                learner_facing=True,
                requires_entry_question=foundational_candidate,
                rationale="Derived from heuristic semantic extraction fallback.",
                source_fields=sorted({span.field for span in evidence}),
                evidence_spans=evidence,
                confidence=topic.confidence,
            )
        )
    return records


def _alias_groups_from_topics(raw_course: NormalizedCourse, topics: list[TopicNode]) -> list[AliasGroupRecord]:
    groups: list[AliasGroupRecord] = []
    for topic in topics:
        if not topic.aliases:
            continue
        evidence = _evidence_spans_for_topic(raw_course, topic)
        groups.append(
            AliasGroupRecord(
                course_id=raw_course.course_id,
                canonical_label=topic.label,
                aliases=list(topic.aliases),
                rationale="Derived from heuristic semantic extraction fallback.",
                source_fields=sorted({span.field for span in evidence}),
                evidence_spans=evidence,
                confidence=topic.confidence,
            )
        )
    return groups


def _friction_record_from_point(
    raw_course: NormalizedCourse,
    friction: FrictionPoint,
    topics: list[TopicNode],
) -> FrictionRecord:
    topic_map = {topic.topic_id: topic for topic in topics}
    topic = topic_map.get(friction.topic_id)
    evidence = _evidence_spans_for_topic(raw_course, topic) if topic is not None else [EvidenceSpan(field="summary", excerpt=raw_course.summary or raw_course.title)]
    return FrictionRecord(
        course_id=raw_course.course_id,
        anchor_id=friction.topic_id,
        friction_type=friction.friction_type,
        description=friction.learner_symptom,
        rationale=friction.why_it_matters,
        source_fields=sorted({span.field for span in evidence}),
        evidence_spans=evidence,
        confidence=friction.confidence,
    )


def _evidence_spans_for_topic(raw_course: NormalizedCourse, topic: TopicNode | None) -> list[EvidenceSpan]:
    if topic is None:
        return [EvidenceSpan(field="summary", excerpt=raw_course.summary or raw_course.title)]
    evidence: list[EvidenceSpan] = []
    label = topic.label.lower()
    if raw_course.summary and label in raw_course.summary.lower():
        evidence.append(EvidenceSpan(field="summary", excerpt=raw_course.summary))
    if raw_course.overview and label in raw_course.overview.lower():
        evidence.append(EvidenceSpan(field="overview", excerpt=raw_course.overview))
    for chapter in raw_course.chapters:
        title = chapter.title or ""
        summary = chapter.summary or ""
        chapter_text = f"{title}\n{summary}".strip()
        if label in chapter_text.lower():
            evidence.append(EvidenceSpan(field="chapters", excerpt=chapter_text))
    if evidence:
        return evidence[:3]
    fallback_excerpt = topic.description or raw_course.summary or raw_course.title
    return [EvidenceSpan(field="overview", excerpt=fallback_excerpt)]


def _anchor_type_for_topic(topic: TopicNode) -> str:
    if topic.topic_type == "concept":
        return "foundational_vocabulary"
    if topic.topic_type in {"procedure", "tool", "metric", "diagnostic", "comparison_axis", "failure_mode", "decision_point"}:
        return topic.topic_type
    return "contextual_topic"
