from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.questions.candidates.extract_edges import extract_edges
from course_pipeline.questions.candidates.extract_pedagogy import extract_pedagogy
from course_pipeline.semantic_bridge import friction_records_to_friction_points, topic_records_to_topic_nodes
from course_pipeline.semantic_extract_llm import extract_semantics_with_llm
from course_pipeline.semantic_schemas import SemanticExtractionReport, SemanticGuardReport, SemanticStageResult
from course_pipeline.semantic_validate import validate_and_sanitize_semantics
from course_pipeline.utils import ensure_dir, write_jsonl, write_yaml


def run_semantic_stage_for_course(
    *,
    raw_course,
    settings: Settings | None,
    run_dir: Path | None,
) -> SemanticStageResult:
    extracted = extract_semantics_with_llm(
        raw_course=raw_course,
        settings=settings,
        run_dir=run_dir,
    )
    extraction_report = extracted.get("extraction_report")
    if extraction_report is None:
        extraction_mode = str(extracted.get("extraction_mode") or "llm")
        extraction_report = SemanticExtractionReport(
            course_id=raw_course.course_id,
            response_shape="legacy_test_payload",
            normalization_path="llm" if extraction_mode == "llm" else "heuristic_fallback",
            fallback_reason=None if extraction_mode == "llm" else extraction_mode,
            raw_topic_count=len(extracted.get("topic_records", [])),
            raw_anchor_count=len(extracted.get("anchor_candidates", [])),
            normalized_topic_count=len(extracted.get("topic_records", [])),
            normalized_anchor_count=len(extracted.get("anchor_candidates", [])),
        )
    validated = validate_and_sanitize_semantics(
        course_id=raw_course.course_id,
        topic_records=extracted["topic_records"],
        anchor_candidates=extracted["anchor_candidates"],
        alias_groups=extracted["alias_groups"],
        friction_records=extracted["friction_records"],
    )
    topics = topic_records_to_topic_nodes(validated["topic_records"])
    edges = extract_edges(extracted["normalized_document"], topics)
    pedagogy = extract_pedagogy(extracted["normalized_document"], topics, edges)
    frictions = friction_records_to_friction_points(validated["friction_records"])
    document_has_signal = bool(
        extracted["normalized_document"].summary.strip()
        or extracted["normalized_document"].overview.strip()
        or extracted["normalized_document"].sections
    )
    guard_warnings: list[str] = []
    guard_status = "ok"
    if document_has_signal and not topics and not validated["anchor_candidates"]:
        guard_warnings.append("semantic_stage_emitted_no_topics_or_anchors_for_non_empty_course")
        guard_status = "failed"
    elif extracted["extraction_mode"] != "llm":
        guard_status = "fallback"
    elif not topics:
        guard_warnings.append("semantic_stage_emitted_zero_topics_after_validation")
        guard_status = "warning"
    return SemanticStageResult(
        normalized_document=extracted["normalized_document"],
        semantic_payload=extracted["payload"],
        semantic_extraction_mode=extracted["extraction_mode"],
        semantic_extraction_report=extraction_report,
        semantic_guard_report=SemanticGuardReport(
            course_id=raw_course.course_id,
            document_has_semantic_signal=document_has_signal,
            topic_count=len(topics),
            anchor_count=len(validated["anchor_candidates"]),
            status=guard_status,  # type: ignore[arg-type]
            warnings=guard_warnings,
        ),
        semantic_topic_records=extracted["topic_records"],
        semantic_anchor_candidates=extracted["anchor_candidates"],
        semantic_alias_groups=extracted["alias_groups"],
        semantic_friction_records=extracted["friction_records"],
        sanitized_topic_records=validated["topic_records"],
        sanitized_anchor_candidates=validated["anchor_candidates"],
        sanitized_alias_groups=validated["alias_groups"],
        sanitized_friction_records=validated["friction_records"],
        semantic_validation_report=validated["report"],
        topics=topics,
        edges=edges,
        pedagogy=pedagogy,
        frictions=frictions,
    )


def write_semantic_stage_artifacts(
    run_dir: Path,
    course_id: str,
    result: SemanticStageResult | dict,
    *,
    base_dir: Path | None = None,
) -> Path:
    stage_result = _coerce_stage_result(result)
    target_root = ensure_dir(base_dir or (run_dir / "course_artifacts" / course_id))
    write_jsonl(
        target_root / "semantic_topics.jsonl",
        [item.model_dump(mode="json") for item in stage_result.semantic_topic_records],
    )
    write_jsonl(
        target_root / "semantic_anchors.jsonl",
        [item.model_dump(mode="json") for item in stage_result.semantic_anchor_candidates],
    )
    write_jsonl(
        target_root / "semantic_alias_groups.jsonl",
        [item.model_dump(mode="json") for item in stage_result.semantic_alias_groups],
    )
    write_jsonl(
        target_root / "semantic_frictions.jsonl",
        [item.model_dump(mode="json") for item in stage_result.semantic_friction_records],
    )
    (target_root / "semantic_validation_report.json").write_text(
        json.dumps(stage_result.semantic_validation_report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (target_root / "semantic_extraction_report.json").write_text(
        json.dumps(stage_result.semantic_extraction_report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (target_root / "semantic_guard_report.json").write_text(
        json.dumps(stage_result.semantic_guard_report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_jsonl(
        target_root / "topics.jsonl",
        [item.model_dump(mode="json") for item in stage_result.topics],
    )
    write_jsonl(
        target_root / "edges.jsonl",
        [item.model_dump(mode="json") for item in stage_result.edges],
    )
    write_jsonl(
        target_root / "pedagogy.jsonl",
        [item.model_dump(mode="json") for item in stage_result.pedagogy],
    )
    write_jsonl(
        target_root / "friction_points.jsonl",
        [item.model_dump(mode="json") for item in stage_result.frictions],
    )
    return target_root


def write_semantic_course_yaml(
    run_dir: Path,
    course_id: str,
    result: SemanticStageResult | dict,
    *,
    base_dir: Path | None = None,
) -> Path:
    stage_result = _coerce_stage_result(result)
    target_root = ensure_dir(base_dir or (run_dir / "course_artifacts" / course_id))
    yaml_dir = ensure_dir(target_root / "semantic_yaml")
    payload = {
        "course_id": course_id,
        "extraction_mode": stage_result.semantic_extraction_mode,
        "payload": stage_result.semantic_payload,
        "extraction_report": stage_result.semantic_extraction_report.model_dump(mode="json"),
        "guard_report": stage_result.semantic_guard_report.model_dump(mode="json"),
        "sanitized_topics": [item.model_dump(mode="json") for item in stage_result.sanitized_topic_records],
        "sanitized_anchors": [item.model_dump(mode="json") for item in stage_result.sanitized_anchor_candidates],
        "sanitized_alias_groups": [item.model_dump(mode="json") for item in stage_result.sanitized_alias_groups],
        "sanitized_frictions": [item.model_dump(mode="json") for item in stage_result.sanitized_friction_records],
        "validation_report": stage_result.semantic_validation_report.model_dump(mode="json"),
    }
    path = yaml_dir / f"{course_id}.yaml"
    write_yaml(path, payload, width=100)
    return path


def _coerce_stage_result(result: SemanticStageResult | dict) -> SemanticStageResult:
    if isinstance(result, SemanticStageResult):
        return result
    return SemanticStageResult.model_validate(result)
