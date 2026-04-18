from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from course_pipeline.config import Settings
from course_pipeline.question_gen_v3.models import FrictionPoint, QuestionCandidate, ScoredCandidate, TopicNode
from course_pipeline.question_gen_v4.assign_policy_bucket import assign_policy_decisions
from course_pipeline.question_gen_v4.build_cache_entries import build_cache_entries
from course_pipeline.question_gen_v4.canonicalize import canonicalize
from course_pipeline.question_gen_v4.policy_metrics import compute_policy_metrics
from course_pipeline.question_gen_v4.policy_models import PolicyDecision
from course_pipeline.question_gen_v4.policy_score import compute_policy_scores
from course_pipeline.question_gen_v4.serveability_gate import serveability_gate
from course_pipeline.question_gen_v4.tag_families import tag_families
from course_pipeline.question_gen_v4_1.anchors import detect_foundational_anchors, is_required_entry_candidate
from course_pipeline.question_gen_v4_1.config import load_default_config
from course_pipeline.question_gen_v4_1.coverage import audit_anchor_coverage
from course_pipeline.question_gen_v4_1.policy_models import CandidateRecord
from course_pipeline.schemas import NormalizedCourse
from course_pipeline.utils import ensure_dir, slugify, write_jsonl


def validate_for_v4_1(candidate: QuestionCandidate, scores, config: dict) -> tuple[bool, list[str]]:
    thresholds = config.get("thresholds", {})
    reasons: list[str] = []
    effective_groundedness = scores.groundedness + (0.08 if candidate.source_support else 0.0)
    if scores.correctness < thresholds.get("correctness_threshold", 0.85):
        reasons.append("invalid_low_correctness")
    if effective_groundedness < thresholds.get("groundedness_threshold", 0.85):
        reasons.append("invalid_low_groundedness")
    if scores.coherence < config["validity_thresholds"]["min_coherence"]:
        reasons.append("invalid_low_coherence")
    if scores.contradiction_risk > config["validity_thresholds"]["max_contradiction_risk"]:
        reasons.append("invalid_contradiction_risk")
    return not reasons, reasons


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
    topics = [
        TopicNode.model_validate_json(line)
        for line in (artifact_dir / "topics.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {"scored_candidates": scored, "frictions": frictions, "topics": topics}


def _map_delivery_class(policy_bucket: str) -> str:
    if policy_bucket == "curated_core":
        return "curated_visible"
    return policy_bucket


def _non_visible_reasons(policy_bucket: str, reason_codes: list[str]) -> list[str]:
    if policy_bucket == "curated_core":
        return []
    if policy_bucket == "cache_servable":
        reasons = ["kept_for_cache_not_visible"]
        if "not_distinct_enough_for_curation" in reason_codes:
            reasons.append("quota_displacement")
        return reasons
    if policy_bucket == "alias_only":
        return ["alias_of_canonical", "canonicalized_under_other_question"]
    if policy_bucket == "analysis_only":
        reasons: list[str] = []
        if "servable_fail_low_serviceability" in reason_codes:
            reasons.append("analysis_only_low_serviceability")
        if "not_distinct_enough_for_curation" in reason_codes:
            reasons.append("analysis_only_low_distinctiveness")
        if not reasons:
            reasons.append("analysis_only_low_pedagogical_value")
        if "curation_fail_balance_cap" in reason_codes:
            reasons.append("hidden_due_to_balance_rules")
        return reasons
    return []


def _record_from_candidate(
    candidate: QuestionCandidate,
    scores,
    canonical_id: str | None,
    delivery_class: str,
    visible: bool,
    reason_codes: list[str],
    anchors: dict[str, TopicNode],
) -> CandidateRecord:
    is_anchor = candidate.topic_id in anchors
    return CandidateRecord(
        candidate_id=candidate.candidate_id,
        question=candidate.question_text,
        answer="",
        topic_ids=[candidate.topic_id],
        canonical_id=canonical_id,
        is_correct=True,
        is_grounded=True,
        delivery_class=delivery_class,
        visible=visible,
        non_visible_reasons=[] if visible else _non_visible_reasons(delivery_class if delivery_class != "curated_visible" else "curated_core", reason_codes),
        scores=scores,
        source_refs=candidate.source_support,
        is_foundational_anchor=is_anchor,
        is_required_entry_candidate=is_required_entry_candidate(candidate.topic_id, candidate.question_type, anchors),
        is_canonical=canonical_id == candidate.candidate_id,
        is_alias=canonical_id is not None and canonical_id != candidate.candidate_id,
        question_type=candidate.question_type,
        mastery_band=candidate.mastery_band,
    )


def run_question_gen_v4_1_policy(v3_result: dict, config: dict | None = None) -> dict:
    cfg = config or load_default_config()
    scored_candidates: list[ScoredCandidate] = v3_result["scored_candidates"]
    frictions: list[FrictionPoint] = v3_result["frictions"]
    topics: list[TopicNode] = v3_result["topics"]
    anchors = detect_foundational_anchors(topics)
    frictions_by_topic: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        frictions_by_topic.setdefault(friction.topic_id, []).append(friction)

    # Validate and persist candidates before curation.
    validated_scored: list[ScoredCandidate] = []
    prepared_validated: list[dict] = []
    hard_rejects: list[dict] = []
    validation_rows: list[dict] = []
    score_by_candidate_id: dict[str, object] = {}
    family_tags_by_candidate_id: dict[str, object] = {}

    for scored in scored_candidates:
        family_tags = tag_families(scored, frictions_by_topic)
        scores = compute_policy_scores(scored, frictions_by_topic)
        valid, validity_reasons = validate_for_v4_1(scored.candidate, scores, cfg)
        score_by_candidate_id[scored.candidate.candidate_id] = scores
        family_tags_by_candidate_id[scored.candidate.candidate_id] = family_tags
        validation_rows.append(
            {
                "candidate_id": scored.candidate.candidate_id,
                "is_validated_correct": valid,
                "validity_reasons": validity_reasons,
            }
        )
        if not valid:
            hard_rejects.append(
                {
                    "candidate": scored.candidate,
                    "scores": scores,
                    "family_tags": family_tags,
                    "reason_codes": validity_reasons or ["invalid_unsupported"],
                }
            )
            continue
        validated_scored.append(scored)
        prepared_validated.append(
            {
                "candidate": scored.candidate,
                "scores": scores,
                "family_tags": family_tags,
            }
        )

    canonical_groups, canonical_by_candidate, alias_ids_by_canonical = canonicalize(validated_scored, cfg)
    classified_inputs: list[dict] = []
    for scored in validated_scored:
        candidate = scored.candidate
        scores = score_by_candidate_id[candidate.candidate_id]
        family_tags = family_tags_by_candidate_id[candidate.candidate_id]
        servable, serve_reasons = serveability_gate(candidate, scores, cfg)
        classified_inputs.append(
            {
                "candidate": candidate,
                "scores": scores,
                "family_tags": family_tags,
                "canonical_id": canonical_by_candidate[candidate.candidate_id],
                "is_alias": canonical_by_candidate[candidate.candidate_id] != candidate.candidate_id,
                "servable": servable,
                "reason_codes": serve_reasons,
            }
        )
    policy_decisions = assign_policy_decisions(classified_inputs, cfg)
    cache_threshold = cfg.get("thresholds", {}).get("cache_serviceability_threshold", 0.80)
    adjusted_decisions: list[PolicyDecision] = []
    for decision in policy_decisions:
        if decision.policy_bucket == "cache_servable" and decision.scores.serviceability < cache_threshold:
            adjusted_decisions.append(
                PolicyDecision(
                    candidate_id=decision.candidate_id,
                    canonical_id=decision.canonical_id,
                    family_tags=decision.family_tags,
                    policy_bucket="analysis_only",
                    servable=False,
                    scores=decision.scores,
                    reason_codes=list(decision.reason_codes) + ["analysis_only_low_serviceability"],
                )
            )
            continue
        adjusted_decisions.append(decision)
    policy_decisions = adjusted_decisions
    decisions_by_candidate_id = {row.candidate_id: row for row in policy_decisions}

    validated_correct_all: list[CandidateRecord] = []
    visible_curated: list[CandidateRecord] = []
    hidden_correct: list[CandidateRecord] = []
    for scored in validated_scored:
        candidate = scored.candidate
        decision = decisions_by_candidate_id[candidate.candidate_id]
        delivery_class = _map_delivery_class(decision.policy_bucket)
        visible = delivery_class == "curated_visible"
        record = _record_from_candidate(
            candidate=candidate,
            scores=decision.scores,
            canonical_id=decision.canonical_id,
            delivery_class=delivery_class,
            visible=visible,
            reason_codes=decision.reason_codes,
            anchors=anchors,
        )
        record.family_tags = decision.family_tags
        validated_correct_all.append(record)
        if visible:
            visible_curated.append(record)
        else:
            hidden_correct.append(record)

    hard_reject_records = [
        CandidateRecord(
            candidate_id=row["candidate"].candidate_id,
            question=row["candidate"].question_text,
            answer="",
            topic_ids=[row["candidate"].topic_id],
            canonical_id=None,
            is_correct=False,
            is_grounded=False,
            delivery_class="hard_reject",
            visible=False,
            non_visible_reasons=row["reason_codes"],
            scores=row["scores"],
            source_refs=row["candidate"].source_support,
            is_foundational_anchor=row["candidate"].topic_id in anchors,
            is_required_entry_candidate=is_required_entry_candidate(
                row["candidate"].topic_id,
                row["candidate"].question_type,
                anchors,
            ),
            is_canonical=False,
            is_alias=False,
            question_type=row["candidate"].question_type,
            mastery_band=row["candidate"].mastery_band,
            family_tags=row["family_tags"].tags,
        )
        for row in hard_rejects
    ]

    coverage_warnings = audit_anchor_coverage(anchors, validated_correct_all)
    policy_metrics = compute_policy_metrics(policy_decisions, canonical_groups)
    hard_reject_reason_counts = Counter(
        reason for record in hard_reject_records for reason in record.non_visible_reasons
    )
    hard_reject_audit_summary = {
        "hard_reject_count": len(hard_reject_records),
        "reason_counts": dict(hard_reject_reason_counts),
    }
    return {
        "canonical_groups": canonical_groups,
        "policy_decisions": policy_decisions,
        "validated_correct_all": validated_correct_all,
        "visible_curated": visible_curated,
        "hidden_correct": hidden_correct,
        "hard_reject_records": hard_reject_records,
        "hard_reject_audit_summary": hard_reject_audit_summary,
        "coverage_warnings": coverage_warnings,
        "metrics": policy_metrics,
        "alias_ids_by_canonical": alias_ids_by_canonical,
        "validation_rows": validation_rows,
    }


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


class LLMJsonClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for V4.1 review answers")
        self.settings = settings

    def invoke_json(self, system_prompt: str, user_prompt: str) -> str:
        import urllib.error
        import urllib.request

        body = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Return grounded short answers as JSON only."},
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


def answer_policy_questions(settings: Settings, course: NormalizedCourse, candidate_rows: list[CandidateRecord]) -> dict[str, str]:
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
                "candidate_id": item.candidate_id,
                "question_text": item.question,
                "question_type": item.question_type,
                "mastery_band": item.mastery_band,
                "source_support": item.source_refs,
            }
            for item in candidate_rows
        ],
    }
    content = client.invoke_json("json", json.dumps(payload, ensure_ascii=False, indent=2))
    return _parse_answers(content)


def write_v4_1_report(run_dir: Path, per_course: dict[str, dict]) -> Path:
    lines = ["# Question Generation V4.1 Report", ""]
    for course_id, result in per_course.items():
        metrics = result["metrics"]
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- validated-correct count: {len(result['validated_correct_all'])}")
        lines.append(f"- visible curated count: {len(result['visible_curated'])}")
        lines.append(f"- hidden correct count: {len(result['hidden_correct'])}")
        lines.append(f"- coverage warning count: {len(result['coverage_warnings'])}")
        lines.append(f"- hard reject count: {result['hard_reject_audit_summary']['hard_reject_count']}")
        lines.append(f"- bucket distribution: {json.dumps(metrics['bucket_distribution'], ensure_ascii=False)}")
        lines.append("")
    path = run_dir / "question_gen_v4_1_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_v4_1_review_bundle(
    run_dir: Path,
    settings: Settings,
    courses: list[NormalizedCourse],
    per_course: dict[str, dict],
) -> dict[str, Path]:
    bundle_dir = ensure_dir(run_dir / "review_bundle")
    answer_rows: list[dict] = []
    for course in courses:
        result = per_course[course.course_id]
        visible_curated: list[CandidateRecord] = result["visible_curated"]
        hidden_correct: list[CandidateRecord] = result["hidden_correct"]
        coverage_warnings = result["coverage_warnings"]
        cache_entries = result["cache_entries"]
        answers = answer_policy_questions(settings, course, visible_curated) if visible_curated else {}
        lines = [f"# {course.title} (`{course.course_id}`)", "", "## Visible Curated Q/A Pairs", ""]
        for item in visible_curated:
            answer = answers.get(item.candidate_id, "")
            lines.append(f"Q: {item.question}  ")
            lines.append(f"A: {answer}".rstrip())
            lines.append("")
            answer_rows.append(
                {
                    "course_id": course.course_id,
                    "candidate_id": item.candidate_id,
                    "question_text": item.question,
                    "answer_markdown": answer,
                    "delivery_class": item.delivery_class,
                }
            )
        lines.extend(["## Hidden But Correct", ""])
        if hidden_correct:
            for item in hidden_correct:
                lines.append(f"- {item.question}")
                lines.append(f"  delivery_class: {item.delivery_class}; reasons: {json.dumps(item.non_visible_reasons, ensure_ascii=False)}")
                lines.append(f"  anchor={str(item.is_foundational_anchor).lower()} required_entry={str(item.is_required_entry_candidate).lower()}")
        else:
            lines.append("- none")
        lines.append("")
        lines.extend(["## Coverage Warnings", ""])
        if coverage_warnings:
            for warning in coverage_warnings:
                lines.append(f"- `{warning.warning_type}` for `{warning.concept_label}`: {warning.message}")
        else:
            lines.append("- none")
        lines.append("")
        lines.extend(["## Policy Summary", ""])
        lines.append(f"- validated-correct count: {len(result['validated_correct_all'])}")
        lines.append(f"- visible curated count: {len(visible_curated)}")
        lines.append(f"- hidden correct count: {len(hidden_correct)}")
        lines.append(f"- hard reject count: {result['hard_reject_audit_summary']['hard_reject_count']}")
        lines.append(f"- cache entries: {len(cache_entries)}")
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
