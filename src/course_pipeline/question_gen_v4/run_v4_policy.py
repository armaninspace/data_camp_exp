from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.question_gen_v3.models import FrictionPoint, ScoredCandidate
from course_pipeline.question_gen_v4.assign_policy_bucket import assign_policy_decisions
from course_pipeline.question_gen_v4.build_cache_entries import build_cache_entries
from course_pipeline.question_gen_v4.canonicalize import canonicalize
from course_pipeline.question_gen_v4.config import load_default_config
from course_pipeline.question_gen_v4.policy_metrics import compute_policy_metrics
from course_pipeline.question_gen_v4.policy_models import CacheEntry, FamilyTagSet, PolicyDecision
from course_pipeline.question_gen_v4.policy_score import compute_policy_scores
from course_pipeline.question_gen_v4.retention import build_retention_records
from course_pipeline.question_gen_v4.serveability_gate import serveability_gate
from course_pipeline.question_gen_v4.tag_families import tag_families
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.utils import ensure_dir, slugify, write_jsonl


ANSWER_SYSTEM_PROMPT = """You write short grounded answers for policy-selected course questions.

Return JSON only.

Rules:
- Answer directly and briefly.
- Stay within the supplied course description and section text.
- Do not invent unsupported detail.
- Prefer stable answers that can serve as cache entries when appropriate.
"""


class LLMJsonClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for V4 review answers")
        self.settings = settings

    def invoke_json(self, system_prompt: str, user_prompt: str) -> str:
        body = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.openai_timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {error_body}") from exc
        return payload["choices"][0]["message"]["content"]


def _parse_answers(content: str) -> dict[str, str]:
    payload = json.loads(content)
    rows = payload.get("answers") or []
    answers = {}
    for row in rows:
        candidate_id = row.get("candidate_id") or row.get("question_id")
        answer = row.get("answer_markdown") or row.get("answer") or row.get("response") or ""
        if candidate_id:
            answers[candidate_id] = answer.strip()
    return answers


def load_v3_course_artifacts(v3_run_dir: Path, course_id: str) -> dict:
    artifact_dir = v3_run_dir / "course_artifacts" / course_id
    scored = [
        ScoredCandidate.model_validate_json(line)
        for line in (artifact_dir / "scored_candidates.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    frictions = [
        FrictionPoint.model_validate_json(line)
        for line in (artifact_dir / "friction_points.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {"scored_candidates": scored, "frictions": frictions}


def run_question_gen_v4_policy(v3_result: dict, config: dict | None = None) -> dict:
    cfg = config or load_default_config()
    scored_candidates: list[ScoredCandidate] = v3_result["scored_candidates"]
    frictions: list[FrictionPoint] = v3_result["frictions"]
    frictions_by_topic: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        frictions_by_topic.setdefault(friction.topic_id, []).append(friction)
    canonical_groups, canonical_by_candidate, alias_ids_by_canonical = canonicalize(scored_candidates, cfg)
    prepared: list[dict] = []
    for candidate in scored_candidates:
        family_tags = tag_families(candidate, frictions_by_topic)
        scores = compute_policy_scores(candidate, frictions_by_topic)
        servable, serve_reasons = serveability_gate(candidate.candidate, scores, cfg)
        prepared.append(
            {
                "candidate": candidate.candidate,
                "scores": scores,
                "family_tags": family_tags,
                "canonical_id": canonical_by_candidate[candidate.candidate.candidate_id],
                "is_alias": canonical_by_candidate[candidate.candidate.candidate_id] != candidate.candidate.candidate_id,
                "servable": servable,
                "reason_codes": serve_reasons,
            }
        )
    decisions = assign_policy_decisions(prepared, cfg)
    retention_records = build_retention_records(decisions, cfg)
    metrics = compute_policy_metrics(decisions, canonical_groups)
    return {
        "canonical_groups": canonical_groups,
        "policy_decisions": decisions,
        "retention_records": retention_records,
        "metrics": metrics,
        "alias_ids_by_canonical": alias_ids_by_canonical,
    }


def answer_policy_questions(settings: Settings, course: NormalizedCourse, candidate_rows: list[ScoredCandidate]) -> dict[str, str]:
    client = LLMJsonClient(settings)
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
            for item in candidate_rows
        ],
    }
    content = client.invoke_json(ANSWER_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
    return _parse_answers(content)


def write_v4_report(run_dir: Path, per_course: dict[str, dict]) -> Path:
    lines = ["# Question Generation V4 Policy Report", ""]
    for course_id, result in per_course.items():
        metrics = result["metrics"]
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- bucket distribution: {json.dumps(metrics['bucket_distribution'], ensure_ascii=False)}")
        lines.append(f"- family coverage: {json.dumps(metrics['family_coverage'], ensure_ascii=False)}")
        lines.append(f"- curated-core count: {metrics['curated_core_count']}")
        lines.append(f"- canonical count: {metrics['canonical_count']}")
        lines.append(f"- alias count: {metrics['alias_count']}")
        lines.append(f"- cache-servable rate: {metrics['cache_servable_rate']}")
        lines.append(f"- analysis-only rate: {metrics['analysis_only_rate']}")
        lines.append(f"- hard-reject rate: {metrics['hard_reject_rate']}")
        lines.append(f"- top reason codes: {json.dumps(metrics['top_reason_codes'], ensure_ascii=False)}")
        lines.append("")
    path = run_dir / "question_gen_v4_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_v4_review_bundle(
    run_dir: Path,
    settings: Settings,
    courses: list[NormalizedCourse],
    per_course: dict[str, dict],
) -> dict[str, Path]:
    bundle_dir = ensure_dir(run_dir / "review_bundle")
    answer_rows: list[dict] = []
    for course in courses:
        result = per_course[course.course_id]
        scored_by_id = result["scored_by_id"]
        decisions: list[PolicyDecision] = result["policy_decisions"]
        curated_ids = [decision.candidate_id for decision in decisions if decision.policy_bucket == "curated_core"]
        curated = [scored_by_id[candidate_id] for candidate_id in curated_ids if candidate_id in scored_by_id]
        answers = answer_policy_questions(settings, course, curated)
        cache_entries = result["cache_entries"]
        lines = [f"# {course.title} (`{course.course_id}`)", "", "## Curated Core Q/A Pairs", ""]
        for item in curated:
            question = item.candidate.question_text
            answer = answers.get(item.candidate.candidate_id, "")
            lines.append(f"Q: {question}  ")
            lines.append(f"A: {answer}".rstrip())
            lines.append("")
            answer_rows.append(
                {
                    "course_id": course.course_id,
                    "candidate_id": item.candidate.candidate_id,
                    "question_text": question,
                    "answer_markdown": answer,
                    "bucket": "curated_core",
                }
            )
        lines.extend(["## Policy Summary", ""])
        lines.append(f"- bucket distribution: {json.dumps(result['metrics']['bucket_distribution'], ensure_ascii=False)}")
        lines.append(f"- family coverage: {json.dumps(result['metrics']['family_coverage'], ensure_ascii=False)}")
        lines.append(f"- cache entries: {len(cache_entries)}")
        lines.append("")
        if cache_entries:
            lines.append("## Cache Entries")
            lines.append("")
            for entry in cache_entries:
                lines.append(f"- canonical: {entry.canonical_question}")
                if entry.alias_questions:
                    lines.append(f"  aliases: {json.dumps(entry.alias_questions, ensure_ascii=False)}")
            lines.append("")
        lines.extend(["## Scraped Course Description", "", "### Summary", "", course.summary or "", "", "### Overview", "", course.overview or "", "", "### Syllabus", ""])
        for section in course.chapters:
            lines.append(f"{section.chapter_index}. {section.title}  ")
            lines.append((section.summary or "").strip())
            lines.append("")
        (bundle_dir / f"{course.course_id}_{slugify(course.title)}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    answers_path = run_dir / "review_answers.jsonl"
    write_jsonl(answers_path, answer_rows)
    return {"review_bundle": bundle_dir, "review_answers": answers_path}
