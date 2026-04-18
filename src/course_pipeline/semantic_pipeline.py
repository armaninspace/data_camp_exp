from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.questions.candidates.extract_edges import extract_edges
from course_pipeline.questions.candidates.extract_pedagogy import extract_pedagogy
from course_pipeline.semantic_bridge import friction_records_to_friction_points, topic_records_to_topic_nodes
from course_pipeline.semantic_extract_llm import extract_semantics_with_llm
from course_pipeline.semantic_validate import validate_and_sanitize_semantics
from course_pipeline.utils import ensure_dir, write_jsonl, write_yaml


def run_semantic_stage_for_course(
    *,
    raw_course,
    settings: Settings | None,
    run_dir: Path | None,
) -> dict:
    extracted = extract_semantics_with_llm(
        raw_course=raw_course,
        settings=settings,
        run_dir=run_dir,
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
    return {
        "normalized_document": extracted["normalized_document"],
        "semantic_payload": extracted["payload"],
        "semantic_extraction_mode": extracted["extraction_mode"],
        "semantic_topic_records": extracted["topic_records"],
        "semantic_anchor_candidates": extracted["anchor_candidates"],
        "semantic_alias_groups": extracted["alias_groups"],
        "semantic_friction_records": extracted["friction_records"],
        "sanitized_topic_records": validated["topic_records"],
        "sanitized_anchor_candidates": validated["anchor_candidates"],
        "sanitized_alias_groups": validated["alias_groups"],
        "sanitized_friction_records": validated["friction_records"],
        "semantic_validation_report": validated["report"],
        "topics": topics,
        "edges": edges,
        "pedagogy": pedagogy,
        "frictions": frictions,
    }


def write_semantic_stage_artifacts(run_dir: Path, course_id: str, result: dict, *, base_dir: Path | None = None) -> Path:
    target_root = ensure_dir(base_dir or (run_dir / "course_artifacts" / course_id))
    write_jsonl(
        target_root / "semantic_topics.jsonl",
        [item.model_dump(mode="json") for item in result["semantic_topic_records"]],
    )
    write_jsonl(
        target_root / "semantic_anchors.jsonl",
        [item.model_dump(mode="json") for item in result["semantic_anchor_candidates"]],
    )
    write_jsonl(
        target_root / "semantic_alias_groups.jsonl",
        [item.model_dump(mode="json") for item in result["semantic_alias_groups"]],
    )
    write_jsonl(
        target_root / "semantic_frictions.jsonl",
        [item.model_dump(mode="json") for item in result["semantic_friction_records"]],
    )
    (target_root / "semantic_validation_report.json").write_text(
        json.dumps(result["semantic_validation_report"].model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_jsonl(
        target_root / "topics.jsonl",
        [item.model_dump(mode="json") for item in result["topics"]],
    )
    write_jsonl(
        target_root / "edges.jsonl",
        [item.model_dump(mode="json") for item in result["edges"]],
    )
    write_jsonl(
        target_root / "pedagogy.jsonl",
        [item.model_dump(mode="json") for item in result["pedagogy"]],
    )
    write_jsonl(
        target_root / "friction_points.jsonl",
        [item.model_dump(mode="json") for item in result["frictions"]],
    )
    return target_root


def write_semantic_course_yaml(run_dir: Path, course_id: str, result: dict, *, base_dir: Path | None = None) -> Path:
    target_root = ensure_dir(base_dir or (run_dir / "course_artifacts" / course_id))
    yaml_dir = ensure_dir(target_root / "semantic_yaml")
    payload = {
        "course_id": course_id,
        "extraction_mode": result["semantic_extraction_mode"],
        "payload": result["semantic_payload"],
        "sanitized_topics": [item.model_dump(mode="json") for item in result["sanitized_topic_records"]],
        "sanitized_anchors": [item.model_dump(mode="json") for item in result["sanitized_anchor_candidates"]],
        "sanitized_alias_groups": [item.model_dump(mode="json") for item in result["sanitized_alias_groups"]],
        "sanitized_frictions": [item.model_dump(mode="json") for item in result["sanitized_friction_records"]],
        "validation_report": result["semantic_validation_report"].model_dump(mode="json"),
    }
    path = yaml_dir / f"{course_id}.yaml"
    write_yaml(path, payload, width=100)
    return path
