from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.question_seed_generate import generate_seed_candidates
from course_pipeline.question_expand_llm import expand_candidates_with_llm
from course_pipeline.question_llm_merge import merge_llm_candidates
from course_pipeline.question_refine_llm import repair_candidates_with_llm
from course_pipeline.questions.candidates.config import load_default_config
from course_pipeline.questions.candidates.dedupe import dedupe_candidates
from course_pipeline.questions.candidates.filters import filter_candidates
from course_pipeline.questions.candidates.models import (
    ReviewAnswer,
    ScoredCandidate,
    SeedGenerationInvariantReport,
    SelectionSummary,
)
from course_pipeline.questions.candidates.score_candidates import score_candidates
from course_pipeline.questions.candidates.selection import select_final
from course_pipeline.questions.policy.anchors import detect_foundational_anchors
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.semantic_pipeline import run_semantic_stage_for_course
from course_pipeline.semantic_schemas import SemanticStageResult
from course_pipeline.utils import ensure_dir, slugify, write_jsonl, write_yaml


class ReviewAnswerParser:
    @staticmethod
    def parse(content: str) -> list[ReviewAnswer]:
        payload = json.loads(content)
        answers = payload.get("answers") or []
        normalized = []
        for item in answers:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "candidate_id": item.get("candidate_id") or item.get("question_id"),
                    "answer_markdown": item.get("answer_markdown") or item.get("answer") or item.get("response") or "",
                }
            )
        return [ReviewAnswer(**item) for item in normalized if item.get("candidate_id")]


ANSWER_SYSTEM_PROMPT = """You write short grounded answers for selected course questions.

Return JSON only.

Rules:
- Answer directly and briefly.
- Stay within the supplied course description and section text.
- Do not invent implementation detail beyond the source.
- If a question asks for a diagnostic or comparison, answer at that level rather than falling back to a generic definition.
"""


def run_question_gen_v3_for_course(
    raw_doc: NormalizedCourse,
    config: dict | None = None,
    *,
    settings: Settings | None = None,
    run_dir: Path | None = None,
    semantic_result: SemanticStageResult | dict | None = None,
) -> dict:
    cfg = config or load_default_config()
    semantic_stage = semantic_result or run_semantic_stage_for_course(
        raw_course=raw_doc,
        settings=settings,
        run_dir=run_dir,
    )
    if not isinstance(semantic_stage, SemanticStageResult):
        semantic_stage = SemanticStageResult.model_validate(semantic_stage)
    doc = semantic_stage.normalized_document
    topics = semantic_stage.topics
    edges = semantic_stage.edges
    pedagogy = semantic_stage.pedagogy
    frictions = semantic_stage.frictions
    seed_result = generate_seed_candidates(
        doc,
        topics,
        edges,
        pedagogy,
        frictions,
        cfg,
        anchors=semantic_stage.sanitized_anchor_candidates,
    )
    seed_candidates = seed_result["candidates"]
    seed_invariant_report: SeedGenerationInvariantReport = seed_result["invariant_report"]
    foundational_anchors = detect_foundational_anchors(topics)
    foundational_anchor_labels = sorted(
        {
            topic.label
            for topic in foundational_anchors.values()
        }
    )
    candidate_repairs, repair_payload = repair_candidates_with_llm(
        settings=settings,
        run_dir=run_dir,
        course=doc,
        topics=topics,
        edges=edges,
        pedagogy=pedagogy,
        frictions=frictions,
        candidates=seed_candidates,
        foundational_anchor_labels=foundational_anchor_labels,
    )
    repaired_candidates, _repair_merge_report = merge_llm_candidates(
        course_id=raw_doc.course_id,
        raw_candidates=seed_candidates,
        repair_records=candidate_repairs,
        derived_candidates=[],
        topics=topics,
    )
    candidate_expansions, expand_payload = expand_candidates_with_llm(
        settings=settings,
        run_dir=run_dir,
        course=doc,
        topics=topics,
        edges=edges,
        pedagogy=pedagogy,
        frictions=frictions,
        repaired_candidates=repaired_candidates,
        foundational_anchor_labels=foundational_anchor_labels,
    )
    merged_candidates, candidate_merge_report = merge_llm_candidates(
        course_id=raw_doc.course_id,
        raw_candidates=seed_candidates,
        repair_records=candidate_repairs,
        derived_candidates=candidate_expansions,
        topics=topics,
    )
    kept_candidates, rejected = filter_candidates(merged_candidates, topics, cfg)
    scored = score_candidates(
        kept_candidates,
        topics,
        edges,
        frictions,
        cfg,
        anchor_candidates=semantic_stage.sanitized_anchor_candidates,
    )
    deduped, duplicate_clusters = dedupe_candidates(scored, cfg)
    target_n = cfg["generation"]["target_final_per_course"]
    final_selected, selection_summary = select_final(
        deduped,
        cfg,
        target_n=target_n,
        rejected_count=len(rejected),
        duplicate_cluster_count=len(duplicate_clusters),
    )
    return {
        "normalized_document": doc,
        "semantic_payload": semantic_stage.semantic_payload,
        "semantic_extraction_mode": semantic_stage.semantic_extraction_mode,
        "semantic_extraction_report": semantic_stage.semantic_extraction_report,
        "semantic_guard_report": semantic_stage.semantic_guard_report,
        "semantic_topic_records": semantic_stage.semantic_topic_records,
        "semantic_anchor_candidates": semantic_stage.semantic_anchor_candidates,
        "semantic_alias_groups": semantic_stage.semantic_alias_groups,
        "semantic_friction_records": semantic_stage.semantic_friction_records,
        "sanitized_topic_records": semantic_stage.sanitized_topic_records,
        "sanitized_anchor_candidates": semantic_stage.sanitized_anchor_candidates,
        "sanitized_alias_groups": semantic_stage.sanitized_alias_groups,
        "sanitized_friction_records": semantic_stage.sanitized_friction_records,
        "semantic_validation_report": semantic_stage.semantic_validation_report,
        "topics": topics,
        "edges": edges,
        "pedagogy": pedagogy,
        "frictions": frictions,
        "seed_candidates": seed_candidates,
        "seed_invariant_report": seed_invariant_report,
        "raw_candidates": seed_candidates,
        "candidate_repairs": candidate_repairs,
        "candidate_expansions": candidate_expansions,
        "candidate_merge_report": candidate_merge_report,
        "repair_payload": repair_payload,
        "expand_payload": expand_payload,
        "merged_candidates": merged_candidates,
        "rejected_candidates": rejected,
        "scored_candidates": scored,
        "duplicate_clusters": duplicate_clusters,
        "final_selected": final_selected,
        "selection_summary": selection_summary,
    }


def write_course_artifacts(run_dir: Path, course_id: str, result: dict) -> None:
    artifact_dir = ensure_dir(run_dir / "course_artifacts" / course_id)
    write_yaml(artifact_dir / "normalized_document.yaml", result["normalized_document"].model_dump(mode="json"), width=100)
    write_jsonl(artifact_dir / "semantic_topics.jsonl", [item.model_dump(mode="json") for item in result.get("semantic_topic_records", [])])
    write_jsonl(artifact_dir / "semantic_anchors.jsonl", [item.model_dump(mode="json") for item in result.get("semantic_anchor_candidates", [])])
    write_jsonl(artifact_dir / "semantic_alias_groups.jsonl", [item.model_dump(mode="json") for item in result.get("semantic_alias_groups", [])])
    write_jsonl(artifact_dir / "semantic_frictions.jsonl", [item.model_dump(mode="json") for item in result.get("semantic_friction_records", [])])
    (artifact_dir / "semantic_extraction_report.json").write_text(
        json.dumps(result.get("semantic_extraction_report", {}).model_dump(mode="json") if hasattr(result.get("semantic_extraction_report"), "model_dump") else result.get("semantic_extraction_report", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "semantic_guard_report.json").write_text(
        json.dumps(result.get("semantic_guard_report", {}).model_dump(mode="json") if hasattr(result.get("semantic_guard_report"), "model_dump") else result.get("semantic_guard_report", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "semantic_validation_report.json").write_text(
        json.dumps(result.get("semantic_validation_report", {}).model_dump(mode="json") if hasattr(result.get("semantic_validation_report"), "model_dump") else result.get("semantic_validation_report", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_jsonl(artifact_dir / "topics.jsonl", [item.model_dump(mode="json") for item in result["topics"]])
    write_jsonl(artifact_dir / "edges.jsonl", [item.model_dump(mode="json") for item in result["edges"]])
    write_jsonl(artifact_dir / "pedagogy.jsonl", [item.model_dump(mode="json") for item in result["pedagogy"]])
    write_jsonl(artifact_dir / "friction_points.jsonl", [item.model_dump(mode="json") for item in result["frictions"]])
    write_jsonl(artifact_dir / "seed_candidates.jsonl", [item.model_dump(mode="json") for item in result.get("seed_candidates", result["raw_candidates"])])
    (artifact_dir / "seed_invariant_report.json").write_text(
        json.dumps(result.get("seed_invariant_report", {}).model_dump(mode="json") if hasattr(result.get("seed_invariant_report"), "model_dump") else result.get("seed_invariant_report", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_jsonl(artifact_dir / "raw_candidates.jsonl", [item.model_dump(mode="json") for item in result["raw_candidates"]])
    write_jsonl(artifact_dir / "candidate_repairs.jsonl", [item.model_dump(mode="json") for item in result.get("candidate_repairs", [])])
    write_jsonl(artifact_dir / "candidate_expansions.jsonl", [item.model_dump(mode="json") for item in result.get("candidate_expansions", [])])
    write_jsonl(artifact_dir / "candidate_merge_report.jsonl", [item.model_dump(mode="json") for item in result.get("candidate_merge_report", [])])
    write_jsonl(artifact_dir / "merged_candidates.jsonl", [item.model_dump(mode="json") for item in result.get("merged_candidates", [])])
    write_jsonl(artifact_dir / "rejected_candidates.jsonl", [item.model_dump(mode="json") for item in result["rejected_candidates"]])
    write_jsonl(artifact_dir / "scored_candidates.jsonl", [item.model_dump(mode="json") for item in result["scored_candidates"]])
    write_jsonl(artifact_dir / "duplicate_clusters.jsonl", [item.model_dump(mode="json") for item in result["duplicate_clusters"]])
    write_jsonl(artifact_dir / "final_selected.jsonl", [item.model_dump(mode="json") for item in result["final_selected"]])
    write_yaml(artifact_dir / "question_refine.yaml", result.get("repair_payload", {}), width=100)
    write_yaml(artifact_dir / "question_expand.yaml", result.get("expand_payload", {}), width=100)
    (artifact_dir / "selection_summary.json").write_text(
        json.dumps(result["selection_summary"].model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_run_report(run_dir: Path, per_course: dict[str, dict]) -> Path:
    lines = ["# Question Generation V3 Report", ""]
    for course_id, result in per_course.items():
        summary: SelectionSummary = result["selection_summary"]
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- topics: {len(result['topics'])}")
        lines.append(f"- edges: {len(result['edges'])}")
        lines.append(f"- friction points: {len(result['frictions'])}")
        lines.append(f"- raw candidates: {len(result['raw_candidates'])}")
        lines.append(f"- candidate repairs: {len(result.get('candidate_repairs', []))}")
        lines.append(f"- candidate expansions: {len(result.get('candidate_expansions', []))}")
        lines.append(f"- merged candidates: {len(result.get('merged_candidates', []))}")
        lines.append(f"- rejected candidates: {len(result['rejected_candidates'])}")
        lines.append(f"- selected questions: {summary.selected_count}")
        lines.append(f"- type distribution: {json.dumps(summary.type_distribution, ensure_ascii=False)}")
        lines.append(f"- mastery distribution: {json.dumps(summary.mastery_distribution, ensure_ascii=False)}")
        lines.append(f"- friction-linked selection rate: {summary.friction_linked_selection_rate}")
        lines.append(f"- quotas met: {json.dumps(summary.quotas_met, ensure_ascii=False)}")
        lines.append("")
    report_path = run_dir / "question_gen_v3_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def answer_selected_questions(
    settings: Settings,
    run_dir: Path,
    course: NormalizedCourse,
    selected: list[ScoredCandidate],
) -> dict[str, str]:
    client = MeteredLLMJsonClient(
        settings,
        run_id=run_dir.name,
        run_dir=run_dir,
        stage="candidate_review_answers",
        prompt_version="candidate_review_answers_v1",
    )
    payload = {
        "course": {
            "course_id": course.course_id,
            "title": course.title,
            "summary": course.summary,
            "overview": course.overview,
            "sections": [{"title": c.title, "summary": c.summary} for c in course.chapters],
        },
        "questions": [
            {
                "candidate_id": item.candidate.candidate_id,
                "question_text": item.candidate.question_text,
                "question_type": item.candidate.question_type,
                "mastery_band": item.candidate.mastery_band,
                "source_support": item.candidate.source_support,
            }
            for item in selected
        ],
    }
    content = client.invoke_json(
        ANSWER_SYSTEM_PROMPT,
        json.dumps(payload, ensure_ascii=False, indent=2),
        course_id=course.course_id,
        entity_ids=[item.candidate.candidate_id for item in selected],
    )
    answers = ReviewAnswerParser.parse(content)
    return {item.candidate_id: item.answer_markdown.strip() for item in answers}


def build_review_bundle(run_dir: Path, settings: Settings, courses: list[NormalizedCourse], per_course: dict[str, dict]) -> dict[str, Path]:
    bundle_dir = ensure_dir(run_dir / "review_bundle")
    metering_path = run_dir / "llm_metering.jsonl"
    answer_rows: list[dict] = []
    for course in courses:
        result = per_course.get(course.course_id)
        if not result:
            continue
        selected: list[ScoredCandidate] = result["final_selected"]
        answers = answer_selected_questions(settings, run_dir, course, selected)
        lines = [f"# {course.title} (`{course.course_id}`)", "", "## Selected Q/A Pairs", ""]
        for item in selected:
            q = item.candidate.question_text
            a = answers.get(item.candidate.candidate_id, "")
            lines.append(f"Q: {q}  ")
            lines.append(f"A: {a}".rstrip())
            lines.append("")
            answer_rows.append(
                {
                    "course_id": course.course_id,
                    "candidate_id": item.candidate.candidate_id,
                    "question_text": q,
                    "answer_markdown": a,
                    "question_type": item.candidate.question_type,
                    "mastery_band": item.candidate.mastery_band,
                    "score_total": item.score.total,
                }
            )
        lines.extend(["## Scraped Course Description", "", "### Summary", "", course.summary or "", "", "### Overview", "", course.overview or "", "", "### Syllabus", ""])
        for section in course.chapters:
            lines.append(f"{section.chapter_index}. {section.title}  ")
            lines.append((section.summary or "").strip())
            lines.append("")
        (bundle_dir / f"{course.course_id}_{slugify(course.title)}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    answers_path = run_dir / "review_answers.jsonl"
    write_jsonl(answers_path, answer_rows)
    return {"review_bundle": bundle_dir, "review_answers": answers_path, "llm_metering": metering_path}
