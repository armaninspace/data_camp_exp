from __future__ import annotations

import json
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.llm_metering import MeteredLLMJsonClient
from course_pipeline.questions.candidates.config import load_default_config
from course_pipeline.questions.candidates.dedupe import dedupe_candidates
from course_pipeline.questions.candidates.extract_edges import extract_edges
from course_pipeline.questions.candidates.extract_pedagogy import extract_pedagogy
from course_pipeline.questions.candidates.extract_topics import extract_topics
from course_pipeline.questions.candidates.filters import filter_candidates
from course_pipeline.questions.candidates.generate_candidates import generate_candidates
from course_pipeline.questions.candidates.mine_friction import mine_friction
from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    ReviewAnswer,
    ScoredCandidate,
    SelectionSummary,
)
from course_pipeline.questions.candidates.normalize import normalize_document
from course_pipeline.questions.candidates.score_candidates import score_candidates
from course_pipeline.questions.candidates.selection import select_final
from course_pipeline.schemas import NormalizedCourse
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


def run_question_gen_v3_for_course(raw_doc: NormalizedCourse, config: dict | None = None) -> dict:
    cfg = config or load_default_config()
    doc = normalize_document(raw_doc)
    topics = extract_topics(doc)
    edges = extract_edges(doc, topics)
    pedagogy = extract_pedagogy(doc, topics, edges)
    frictions = mine_friction(topics, edges, pedagogy)
    raw_candidates = generate_candidates(doc, topics, edges, pedagogy, frictions, cfg)
    kept_candidates, rejected = filter_candidates(raw_candidates, topics, cfg)
    scored = score_candidates(kept_candidates, topics, edges, frictions, cfg)
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
        "topics": topics,
        "edges": edges,
        "pedagogy": pedagogy,
        "frictions": frictions,
        "raw_candidates": raw_candidates,
        "rejected_candidates": rejected,
        "scored_candidates": scored,
        "duplicate_clusters": duplicate_clusters,
        "final_selected": final_selected,
        "selection_summary": selection_summary,
    }


def write_course_artifacts(run_dir: Path, course_id: str, result: dict) -> None:
    artifact_dir = ensure_dir(run_dir / "course_artifacts" / course_id)
    write_yaml(artifact_dir / "normalized_document.yaml", result["normalized_document"].model_dump(mode="json"), width=100)
    write_jsonl(artifact_dir / "topics.jsonl", [item.model_dump(mode="json") for item in result["topics"]])
    write_jsonl(artifact_dir / "edges.jsonl", [item.model_dump(mode="json") for item in result["edges"]])
    write_jsonl(artifact_dir / "pedagogy.jsonl", [item.model_dump(mode="json") for item in result["pedagogy"]])
    write_jsonl(artifact_dir / "friction_points.jsonl", [item.model_dump(mode="json") for item in result["frictions"]])
    write_jsonl(artifact_dir / "raw_candidates.jsonl", [item.model_dump(mode="json") for item in result["raw_candidates"]])
    write_jsonl(artifact_dir / "rejected_candidates.jsonl", [item.model_dump(mode="json") for item in result["rejected_candidates"]])
    write_jsonl(artifact_dir / "scored_candidates.jsonl", [item.model_dump(mode="json") for item in result["scored_candidates"]])
    write_jsonl(artifact_dir / "duplicate_clusters.jsonl", [item.model_dump(mode="json") for item in result["duplicate_clusters"]])
    write_jsonl(artifact_dir / "final_selected.jsonl", [item.model_dump(mode="json") for item in result["final_selected"]])
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
