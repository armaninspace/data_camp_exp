from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import BaseModel, Field

from course_pipeline.config import Settings
from course_pipeline.schemas import (
    CanonicalAnswerOut,
    CitationOut,
    ClaimCoverageAuditOut,
    ClaimQuestionGroupOut,
    LearningOutcomeExtractionOut,
    LearningOutcomeOut,
    QuestionCacheGenerationOut,
    QuestionCacheMatchResult,
    QuestionCacheValidationLogOut,
    QuestionGroupVariationOut,
)
from course_pipeline.utils import slugify


QUESTION_CACHE_PROMPT_VERSION = "question-cache-v2"
QUESTION_CACHE_VALIDATOR_VERSION = "question-cache-validator-v1"
FALLBACK_PROMPT_VERSION = "question-cache-fallback-v1"
STOPWORDS = {
    "a", "an", "the", "to", "do", "does", "how", "what", "which", "can", "could", "would",
    "you", "i", "me", "my", "show", "tell", "is", "are", "in", "on", "for", "of", "way",
}


class AtomicGroupDraft(BaseModel):
    intent_slug: str
    canonical_question: str
    pedagogical_move: str
    confidence: float


class AtomicGroupDraftList(BaseModel):
    groups: list[AtomicGroupDraft] = Field(default_factory=list)
    no_groups_reason: str | None = None


class AnswerDraft(BaseModel):
    answer_markdown: str
    answer_scope_notes: str | None = None


class VariationDraftList(BaseModel):
    variations: list[str] = Field(default_factory=list)


class ValidatorDecision(BaseModel):
    decision: str
    reason: str | None = None
    split_intent_slug: str | None = None
    split_canonical_question: str | None = None


def parse_answer_draft(content: str) -> AnswerDraft:
    payload = json.loads(content)
    if "answer_markdown" not in payload:
        payload["answer_markdown"] = payload.get("canonical_answer") or payload.get("answer") or ""
    return AnswerDraft.model_validate(payload)


def parse_validator_decision(content: str) -> ValidatorDecision:
    payload = json.loads(content)
    decision = payload.get("decision") or payload.get("result") or payload.get("status")
    if decision is None:
        decision = "FAIL"
    payload["decision"] = str(decision).upper()
    return ValidatorDecision.model_validate(payload)


def normalize_question_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"`+", "", normalized)
    normalized = re.sub(r"[_*#>-]+", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def token_set(text: str) -> set[str]:
    return {
        token
        for token in normalize_question_text(text).split()
        if token and token not in STOPWORDS
    }


def lexical_score(left: str, right: str) -> float:
    left_norm = normalize_question_text(left)
    right_norm = normalize_question_text(right)
    if not left_norm or not right_norm:
        return 0.0
    ratio = SequenceMatcher(a=left_norm, b=right_norm).ratio()
    left_tokens = token_set(left_norm)
    right_tokens = token_set(right_norm)
    overlap = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    return round((0.55 * ratio) + (0.45 * overlap), 4)


def should_bypass_cache(question: str) -> str | None:
    normalized = normalize_question_text(question)
    bypass_patterns = {
        "follow_up_or_repair": ["traceback", "error", "fails", "failed", "exception", "not working", "doesn t work", "why does", "fix this", "repair", "debug", "my code", "i ran"],
        "style_request": ["another way", "simpler", "in more detail", "step by step"],
    }
    for reason, patterns in bypass_patterns.items():
        if any(pattern in normalized for pattern in patterns):
            return reason
    return None


def make_question_group_id(course_id: str, claim_id: str, intent_slug: str) -> str:
    return f"{course_id}_{claim_id}_{slugify(intent_slug)}"


def make_variation_id(question_group_id: str, text: str) -> str:
    return f"{question_group_id}_{slugify(normalize_question_text(text))[:40] or 'variation'}"


def make_canonical_answer_id(question_group_id: str, version: int = 1) -> str:
    return f"{question_group_id}_v{version}"


def load_learning_outcome_run(run_dir: Path) -> list[LearningOutcomeExtractionOut]:
    path = run_dir / "learning_outcomes.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {path}")
    return [
        LearningOutcomeExtractionOut.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class LLMJsonClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for question-cache generation")
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


class QuestionCacheGenerator:
    def __init__(self, settings: Settings) -> None:
        self.client = LLMJsonClient(settings)

    def generate_for_claim(
        self,
        extraction: LearningOutcomeExtractionOut,
        claim: LearningOutcomeOut,
        source_run_id: str,
    ) -> tuple[QuestionCacheGenerationOut, list[QuestionCacheValidationLogOut], ClaimCoverageAuditOut]:
        citations = [CitationOut.model_validate(c.model_dump(mode="json")) for c in claim.citations]
        validation_logs: list[QuestionCacheValidationLogOut] = []
        groups: list[ClaimQuestionGroupOut] = []
        answers: list[CanonicalAnswerOut] = []
        variations: list[QuestionGroupVariationOut] = []

        atomized = self._atomize_claim(extraction, claim)
        if not atomized.groups:
            audit = ClaimCoverageAuditOut(
                course_id=extraction.course_id,
                claim_id=claim.id,
                produced_question_groups=False,
                question_group_count=0,
                no_groups_reason=atomized.no_groups_reason or "no_safe_atomic_groups",
                source_run_id=source_run_id,
            )
            validation_logs.append(
                QuestionCacheValidationLogOut(
                    entity_type="claim",
                    entity_id=f"{extraction.course_id}:{claim.id}",
                    validator_type="coverage_audit",
                    decision="PASS",
                    reason=audit.no_groups_reason,
                    model_version=QUESTION_CACHE_VALIDATOR_VERSION,
                )
            )
            return (
                QuestionCacheGenerationOut(
                    course_id=extraction.course_id,
                    course_title=extraction.course_title,
                    claim_id=claim.id,
                    claim_text=claim.claim,
                ),
                validation_logs,
                audit,
            )

        for draft in atomized.groups:
            intent_slug = slugify(draft.intent_slug)
            if not intent_slug:
                continue
            question_group_id = make_question_group_id(extraction.course_id, claim.id, intent_slug)
            canonical_answer_id = make_canonical_answer_id(question_group_id, version=1)
            group = ClaimQuestionGroupOut(
                question_group_id=question_group_id,
                course_id=extraction.course_id,
                claim_id=claim.id,
                intent_slug=intent_slug,
                canonical_question=draft.canonical_question.strip(),
                pedagogical_move=slugify(draft.pedagogical_move) or "direct_explanation",
                canonical_answer_id=canonical_answer_id,
                confidence=min(max(draft.confidence, 0.0), claim.confidence),
                citations=citations,
                source_run_id=source_run_id,
                prompt_version=QUESTION_CACHE_PROMPT_VERSION,
                generation_stage="atomized",
                validator_status="pending",
            )

            answer_draft = self._generate_answer(claim, group)
            answer = CanonicalAnswerOut(
                canonical_answer_id=canonical_answer_id,
                question_group_id=question_group_id,
                answer_markdown=answer_draft.answer_markdown.strip(),
                answer_style="short_direct",
                answer_version=1,
                reviewer_state="unreviewed",
                citations=citations,
                source_run_id=source_run_id,
                prompt_version=QUESTION_CACHE_PROMPT_VERSION,
                answer_scope_notes=answer_draft.answer_scope_notes,
            )

            fit = self._validate_answer_fit(group.canonical_question, answer.answer_markdown)
            answer.answer_fit_status = "pass" if fit.decision == "PASS" else "fail"
            validation_logs.append(
                QuestionCacheValidationLogOut(
                    entity_type="canonical_answer",
                    entity_id=answer.canonical_answer_id,
                    validator_type="answer_fit",
                    decision=fit.decision,
                    reason=fit.reason,
                    model_version=QUESTION_CACHE_VALIDATOR_VERSION,
                )
            )

            grounding = self._validate_grounding(answer.answer_markdown, citations)
            answer.grounding_status = "pass" if grounding.decision == "PASS" else "fail"
            answer.grounding_reason = grounding.reason
            validation_logs.append(
                QuestionCacheValidationLogOut(
                    entity_type="canonical_answer",
                    entity_id=answer.canonical_answer_id,
                    validator_type="grounding",
                    decision=grounding.decision,
                    reason=grounding.reason,
                    model_version=QUESTION_CACHE_VALIDATOR_VERSION,
                )
            )

            candidate_variations = self._generate_variations(group.canonical_question, answer.answer_markdown, citations)
            accepted_count = 0
            for index, text in enumerate([group.canonical_question, *candidate_variations.variations]):
                normalized_text = normalize_question_text(text)
                if not normalized_text:
                    continue
                variation = QuestionGroupVariationOut(
                    variation_id=make_variation_id(question_group_id, text),
                    question_group_id=question_group_id,
                    text=text.strip(),
                    normalized_text=normalized_text,
                    equivalence_notes="Pending same-answer validation.",
                    source="canonical" if index == 0 else "generated",
                    candidate_source="canonical_question" if index == 0 else "variation_generation",
                )
                if index == 0:
                    variation.validation_decision = "ACCEPT"
                    variation.validation_reason = "Canonical question anchors the group."
                    variation.accepted_for_runtime = answer.answer_fit_status == "pass" and answer.grounding_status == "pass"
                else:
                    same_answer = self._validate_same_answer(group.canonical_question, answer.answer_markdown, variation.text)
                    variation.validation_decision = same_answer.decision
                    variation.validation_reason = same_answer.reason
                    variation.accepted_for_runtime = (
                        same_answer.decision == "ACCEPT"
                        and answer.answer_fit_status == "pass"
                        and answer.grounding_status == "pass"
                    )
                    validation_logs.append(
                        QuestionCacheValidationLogOut(
                            entity_type="variation",
                            entity_id=variation.variation_id,
                            validator_type="same_answer",
                            decision=same_answer.decision,
                            reason=same_answer.reason,
                            model_version=QUESTION_CACHE_VALIDATOR_VERSION,
                        )
                    )
                if variation.accepted_for_runtime:
                    accepted_count += 1
                variations.append(variation)

            group.generation_stage = "validated"
            group.validator_status = "validated" if (
                answer.answer_fit_status == "pass"
                and answer.grounding_status == "pass"
                and accepted_count > 0
            ) else "rejected"
            groups.append(group)
            answers.append(answer)

        produced = len(groups) > 0
        audit = ClaimCoverageAuditOut(
            course_id=extraction.course_id,
            claim_id=claim.id,
            produced_question_groups=produced,
            question_group_count=len(groups),
            no_groups_reason=None if produced else "all_groups_rejected",
            source_run_id=source_run_id,
        )
        validation_logs.append(
            QuestionCacheValidationLogOut(
                entity_type="claim",
                entity_id=f"{extraction.course_id}:{claim.id}",
                validator_type="coverage_audit",
                decision="PASS" if produced or audit.no_groups_reason else "FAIL",
                reason=audit.no_groups_reason,
                model_version=QUESTION_CACHE_VALIDATOR_VERSION,
            )
        )

        return (
            QuestionCacheGenerationOut(
                course_id=extraction.course_id,
                course_title=extraction.course_title,
                claim_id=claim.id,
                claim_text=claim.claim,
                question_groups=groups,
                variations=variations,
                canonical_answers=answers,
            ),
            validation_logs,
            audit,
        )

    def _atomize_claim(self, extraction: LearningOutcomeExtractionOut, claim: LearningOutcomeOut) -> AtomicGroupDraftList:
        user_prompt = json.dumps(
            {
                "course_id": extraction.course_id,
                "course_title": extraction.course_title,
                "claim_id": claim.id,
                "claim_text": claim.claim,
                "citations": [citation.model_dump(mode="json") for citation in claim.citations],
                "instructions": [
                    "Create atomic learner question groups only.",
                    "Each group must be one distinct learner intent answerable by one short stable answer.",
                    "Do not generate answers or variations.",
                    "Prefer splitting over merging.",
                    "If no safe groups exist, return no_groups_reason.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            content = self.client.invoke_json(
                "Create atomic learner question groups. Return JSON only.",
                user_prompt,
            )
            parsed = AtomicGroupDraftList.model_validate_json(content)
            if parsed.groups:
                return parsed
        except Exception:
            pass
        return self._heuristic_atomize(claim)

    def _heuristic_atomize(self, claim: LearningOutcomeOut) -> AtomicGroupDraftList:
        text = claim.claim.strip().rstrip(".")
        if not text:
            return AtomicGroupDraftList(groups=[], no_groups_reason="empty_claim")
        lower = text.lower()
        subject = ""
        if " in " in lower:
            parts = re.split(r"\bin\b", text, maxsplit=1, flags=re.IGNORECASE)
            action_text = parts[0].strip()
            subject = parts[1].strip()
        else:
            action_text = text

        normalized_actions = re.sub(r"\band\b", ",", action_text, flags=re.IGNORECASE)
        raw_actions = [part.strip(" ,") for part in normalized_actions.split(",") if part.strip(" ,")]
        if not raw_actions:
            raw_actions = [text]

        common_object = self._infer_common_object(raw_actions)

        groups: list[AtomicGroupDraft] = []
        for action in raw_actions:
            action_phrase = self._normalize_action_phrase(action, common_object)
            slug = slugify(action_phrase)
            if not slug:
                continue
            if subject:
                canonical_question = f"How do you {action_phrase.lower()} in {subject}?"
            else:
                canonical_question = f"How do you {action_phrase.lower()}?"
            pedagogical_move = "definition" if any(word in action_phrase.lower() for word in ("identify", "understand", "explain", "what is")) else "worked_example"
            groups.append(
                AtomicGroupDraft(
                    intent_slug=slug,
                    canonical_question=canonical_question[0].upper() + canonical_question[1:],
                    pedagogical_move=pedagogical_move,
                    confidence=min(claim.confidence, 0.65),
                )
            )
        if not groups:
            return AtomicGroupDraftList(groups=[], no_groups_reason="no_safe_atomic_groups")
        return AtomicGroupDraftList(groups=groups)

    def _infer_common_object(self, raw_actions: list[str]) -> str | None:
        if not raw_actions:
            return None
        last = raw_actions[-1].strip()
        tokens = last.split()
        if len(tokens) >= 2:
            return " ".join(tokens[1:]).strip()
        for action in raw_actions[1:]:
            tokens = action.split()
            if len(tokens) >= 2:
                return " ".join(tokens[1:]).strip()
        return None

    def _normalize_action_phrase(self, action: str, common_object: str | None) -> str:
        cleaned = action.strip()
        lower = cleaned.lower()
        if lower == "variable assignment":
            return "assign variables"
        if common_object:
            tokens = cleaned.split()
            if len(tokens) == 1:
                return f"{tokens[0]} {common_object}"
        return cleaned

    def _generate_answer(self, claim: LearningOutcomeOut, group: ClaimQuestionGroupOut) -> AnswerDraft:
        user_prompt = json.dumps(
            {
                "claim_text": claim.claim,
                "canonical_question": group.canonical_question,
                "citations": [citation.model_dump(mode="json") for citation in group.citations],
                "rules": [
                    "Answer the canonical question directly.",
                    "Stay within cited evidence.",
                    "Keep the answer short and stable.",
                    "Do not add unsupported detail or examples unless required.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        content = self.client.invoke_json(
            "Write one short canonical answer for this question group. Return JSON only.",
            user_prompt,
        )
        return parse_answer_draft(content)

    def _generate_variations(
        self,
        canonical_question: str,
        canonical_answer: str,
        citations: list[CitationOut],
    ) -> VariationDraftList:
        user_prompt = json.dumps(
            {
                "canonical_question": canonical_question,
                "canonical_answer": canonical_answer,
                "citations": [citation.model_dump(mode="json") for citation in citations],
                "rules": [
                    "Generate only 2 to 4 strict same-answer paraphrases.",
                    "Reject phrasing that changes scope, pedagogical move, or answer content.",
                    "Avoid synthetic phrasing like 'What is the way to'.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        content = self.client.invoke_json(
            "Generate strict same-answer paraphrases of the canonical question. Return JSON only.",
            user_prompt,
        )
        return VariationDraftList.model_validate_json(content)

    def _validate_same_answer(self, canonical_question: str, canonical_answer: str, variation: str) -> ValidatorDecision:
        content = self.client.invoke_json(
            "Decide whether the candidate variation is a true same-answer paraphrase. Return ACCEPT, REJECT, or SPLIT_NEW_GROUP in JSON.",
            json.dumps(
                {
                    "canonical_question": canonical_question,
                    "canonical_answer": canonical_answer,
                    "candidate_variation": variation,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return parse_validator_decision(content)

    def _validate_answer_fit(self, canonical_question: str, canonical_answer: str) -> ValidatorDecision:
        content = self.client.invoke_json(
            "Determine whether the canonical answer directly and correctly answers the canonical question. Return PASS or FAIL in JSON.",
            json.dumps(
                {
                    "canonical_question": canonical_question,
                    "canonical_answer": canonical_answer,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return parse_validator_decision(content)

    def _validate_grounding(self, canonical_answer: str, citations: list[CitationOut]) -> ValidatorDecision:
        content = self.client.invoke_json(
            "Check whether every substantive claim in the canonical answer is supported by the cited evidence. Return PASS or FAIL in JSON.",
            json.dumps(
                {
                    "canonical_answer": canonical_answer,
                    "citations": [citation.model_dump(mode="json") for citation in citations],
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return parse_validator_decision(content)


@dataclass
class CacheCandidate:
    group: ClaimQuestionGroupOut
    variation: QuestionGroupVariationOut
    answer: CanonicalAnswerOut
    score: float
    method: str


class QuestionCacheIndex:
    def __init__(
        self,
        groups: list[ClaimQuestionGroupOut],
        variations: list[QuestionGroupVariationOut],
        answers: list[CanonicalAnswerOut],
    ) -> None:
        self.groups = {group.question_group_id: group for group in groups}
        self.answers = {answer.canonical_answer_id: answer for answer in answers}
        self.variations = variations

    @classmethod
    def from_run_dir(cls, run_dir: Path) -> QuestionCacheIndex:
        groups = [
            ClaimQuestionGroupOut.model_validate_json(line)
            for line in (run_dir / "claim_question_groups.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        variations = [
            QuestionGroupVariationOut.model_validate_json(line)
            for line in (run_dir / "question_group_variations.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        answers = [
            CanonicalAnswerOut.model_validate_json(line)
            for line in (run_dir / "canonical_answers.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        groups = [group for group in groups if group.validator_status == "validated"]
        group_ids = {group.question_group_id for group in groups}
        answers = [
            answer
            for answer in answers
            if answer.question_group_id in group_ids
            and answer.answer_fit_status == "pass"
            and answer.grounding_status == "pass"
        ]
        answer_ids = {answer.canonical_answer_id for answer in answers}
        groups = [group for group in groups if group.canonical_answer_id in answer_ids]
        group_ids = {group.question_group_id for group in groups}
        variations = [
            variation
            for variation in variations
            if variation.question_group_id in group_ids and variation.accepted_for_runtime
        ]
        return cls(groups, variations, answers)

    def match(self, question: str, course_id: str | None = None) -> QuestionCacheMatchResult:
        normalized_question = normalize_question_text(question)
        bypass_reason = should_bypass_cache(question)
        candidates = self._collect_candidates(question, course_id=course_id)
        if bypass_reason:
            top = candidates[0] if candidates else None
            return QuestionCacheMatchResult(
                course_id=top.group.course_id if top else course_id,
                claim_id=top.group.claim_id if top else None,
                question_group_id=top.group.question_group_id if top else None,
                variation_id=top.variation.variation_id if top else None,
                canonical_answer_id=top.answer.canonical_answer_id if top else None,
                incoming_question=question,
                normalized_question=normalized_question,
                match_method="fallback",
                match_score=top.score if top else 0.0,
                resolved_as_hit=False,
                fallback_reason=bypass_reason,
                candidate_for_cache_warming=True,
            )
        if not candidates:
            return QuestionCacheMatchResult(
                course_id=course_id,
                incoming_question=question,
                normalized_question=normalized_question,
                match_method="fallback",
                match_score=0.0,
                resolved_as_hit=False,
                fallback_reason="no_match",
                candidate_for_cache_warming=True,
            )
        grouped: dict[str, CacheCandidate] = {}
        for candidate in candidates:
            existing = grouped.get(candidate.group.question_group_id)
            if existing is None or candidate.score > existing.score:
                grouped[candidate.group.question_group_id] = candidate
        ranked = sorted(grouped.values(), key=lambda candidate: candidate.score, reverse=True)
        top = ranked[0]
        second = ranked[1] if len(ranked) > 1 else None
        margin = top.score - (second.score if second else 0.0)
        is_hit = top.method.startswith("exact") or (top.score >= 0.84 and margin >= 0.08)
        if not is_hit:
            return QuestionCacheMatchResult(
                course_id=top.group.course_id,
                claim_id=top.group.claim_id,
                question_group_id=top.group.question_group_id,
                variation_id=top.variation.variation_id,
                canonical_answer_id=top.answer.canonical_answer_id,
                incoming_question=question,
                normalized_question=normalized_question,
                match_method="fallback",
                match_score=top.score,
                resolved_as_hit=False,
                fallback_reason="ambiguous_match",
                candidate_for_cache_warming=True,
            )
        return QuestionCacheMatchResult(
            course_id=top.group.course_id,
            claim_id=top.group.claim_id,
            question_group_id=top.group.question_group_id,
            variation_id=top.variation.variation_id,
            canonical_answer_id=top.answer.canonical_answer_id,
            incoming_question=question,
            normalized_question=normalized_question,
            match_method=top.method,  # type: ignore[arg-type]
            match_score=top.score,
            resolved_as_hit=True,
            answer_markdown=top.answer.answer_markdown,
        )

    def _collect_candidates(self, question: str, course_id: str | None = None) -> list[CacheCandidate]:
        normalized_question = normalize_question_text(question)
        candidates: list[CacheCandidate] = []
        for variation in self.variations:
            group = self.groups.get(variation.question_group_id)
            if group is None:
                continue
            if course_id and group.course_id != course_id:
                continue
            answer = self.answers[group.canonical_answer_id]
            if variation.normalized_text == normalized_question:
                method = "exact_variation"
                score = 1.0
            elif normalize_question_text(group.canonical_question) == normalized_question:
                method = "exact_canonical"
                score = 0.99
            else:
                method = "lexical"
                score = lexical_score(question, variation.text)
            candidates.append(CacheCandidate(group, variation, answer, score, method))
        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return candidates[:5]


class QuestionCacheFallback:
    def __init__(self, settings: Settings) -> None:
        self.client = LLMJsonClient(settings)

    def answer(
        self,
        question: str,
        match_result: QuestionCacheMatchResult,
        nearest_group: ClaimQuestionGroupOut | None = None,
        nearest_answer: CanonicalAnswerOut | None = None,
    ) -> str:
        content = self.client.invoke_json(
            "You are a grounded teaching assistant. Answer briefly and return JSON with answer_markdown.",
            json.dumps(
                {
                    "question": question,
                    "fallback_reason": match_result.fallback_reason,
                    "nearest_group": nearest_group.model_dump(mode="json") if nearest_group else None,
                    "nearest_answer": nearest_answer.model_dump(mode="json") if nearest_answer else None,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return json.loads(content)["answer_markdown"]
