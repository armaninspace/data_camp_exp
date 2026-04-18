from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from course_pipeline.config import Settings
from course_pipeline.schemas import (
    CandidateQuestionOut,
    GenerationBasisOut,
    LearnerFrictionCandidateOut,
    NormalizedCourse,
    SourceEvidenceOut,
    TopicOut,
)
from course_pipeline.utils import slugify, write_jsonl


QUESTION_GEN_V2_PROMPT_VERSION = "question-gen-v2"


SEMANTIC_SYSTEM_PROMPT = """You extract learner-question-generation structure from course YAML.

Return JSON only.

Rules:
- Use only the supplied course text.
- Prefer chapter-level grounding when available.
- Extract concrete topics, procedures, contrasts, confusions, prerequisites, and learner-friction terms.
- Learner-friction terms are words or phrases likely to trigger natural learner questions.
- Keep labels short and useful.
"""


QUESTION_SYSTEM_PROMPT = """You generate likely learner questions from course structure.

Return JSON only.

Rules:
- Questions must be grounded in the supplied course text.
- Questions must sound like natural learner questions, not analyst paraphrases.
- Prefer beginner-natural wording over syllabus wording.
- Cover multiple question types when evidence supports them.
- Avoid catalog or navigation questions.
- Use the supplied topic labels.
"""


ANSWER_SYSTEM_PROMPT = """You write short grounded answers for review documents.

Return JSON only.

Rules:
- Answer each question directly and briefly.
- Use only the supplied course text and cited context.
- If the course text supports only a limited answer, stay narrow.
- Do not invent implementation details not implied by the course description.
"""


class SemanticTopicDraft(BaseModel):
    label: str
    topic_type: str
    chapter_index: int | None = None
    aliases: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    contrasts: list[str] = Field(default_factory=list)
    confusions: list[str] = Field(default_factory=list)
    evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    importance: float = 0.0


class SemanticFrictionDraft(BaseModel):
    text: str
    candidate_type: str
    chapter_index: int | None = None
    evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    confidence: float = 0.0


class SemanticExtractionDraft(BaseModel):
    topics: list[SemanticTopicDraft] = Field(default_factory=list)
    friction_candidates: list[SemanticFrictionDraft] = Field(default_factory=list)


class CandidateQuestionDraft(BaseModel):
    question_text: str
    chapter_index: int | None = None
    topic_label: str
    mastery_band: str
    question_type: str
    source_evidence: list[SourceEvidenceOut] = Field(default_factory=list)
    generation_basis: GenerationBasisOut
    score: float


class CandidateQuestionDraftList(BaseModel):
    questions: list[CandidateQuestionDraft] = Field(default_factory=list)


class ReviewAnswerDraft(BaseModel):
    question_id: str
    answer_markdown: str


class ReviewAnswerDraftList(BaseModel):
    answers: list[ReviewAnswerDraft] = Field(default_factory=list)


class LLMJsonClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for question generation")
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


def normalize_question_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r"`+", "", normalized)
    normalized = re.sub(r"[_*#>-]+", " ", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def chapter_id_for(course_id: str, chapter_index: int) -> str:
    return f"{course_id}_ch{chapter_index}"


def _course_prompt_payload(course: NormalizedCourse) -> dict:
    return {
        "course_id": course.course_id,
        "title": course.title,
        "summary": course.summary,
        "overview": course.overview,
        "subjects": course.subjects,
        "level": course.level,
        "syllabus": [
            {
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "summary": chapter.summary,
                "source": chapter.source,
            }
            for chapter in course.chapters
        ],
    }


def _chapter_lookup(course: NormalizedCourse) -> dict[int, tuple[str, str]]:
    return {
        chapter.chapter_index: (chapter_id_for(course.course_id, chapter.chapter_index), chapter.title)
        for chapter in course.chapters
    }


def _dedupe_strs(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            ordered.append(cleaned)
    return ordered


class QuestionGenerationV2:
    def __init__(self, settings: Settings) -> None:
        self.client = LLMJsonClient(settings)

    def generate(
        self,
        course: NormalizedCourse,
    ) -> tuple[list[TopicOut], list[LearnerFrictionCandidateOut], list[CandidateQuestionOut]]:
        try:
            semantic = self._extract_semantic_units(course)
        except Exception:
            semantic = self._fallback_semantic_units(course)
        topics = self._finalize_topics(course, semantic.topics)
        frictions = self._finalize_frictions(course, semantic.friction_candidates)
        try:
            questions = self._generate_candidate_questions(course, topics, frictions)
        except Exception:
            questions = self._fallback_candidate_questions(course, topics, frictions)
        return topics, frictions, questions

    def answer_questions_for_review(
        self,
        course: NormalizedCourse,
        questions: list[CandidateQuestionOut],
    ) -> dict[str, str]:
        payload = {
            "course": _course_prompt_payload(course),
            "questions": [
                {
                    "question_id": question.question_id,
                    "question_text": question.question_text,
                    "chapter_title": question.chapter_title,
                    "topic_label": question.topic_label,
                    "question_type": question.question_type,
                    "mastery_band": question.mastery_band,
                    "source_evidence": [e.model_dump(mode="json") for e in question.source_evidence],
                }
                for question in questions
            ],
        }
        content = self.client.invoke_json(ANSWER_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
        parsed = self._parse_review_answer_drafts(content)
        return {item.question_id: item.answer_markdown.strip() for item in parsed.answers if item.answer_markdown.strip()}

    def _extract_semantic_units(self, course: NormalizedCourse) -> SemanticExtractionDraft:
        payload = {
            "course": _course_prompt_payload(course),
            "instructions": [
                "Extract 5 to 14 useful topics if supported.",
                "Extract learner-friction candidates such as jargon, acronyms, methods, tests, process terms, and overloaded terms.",
                "Keep evidence excerpts short and copied from the course text.",
                "Prefer chapter-specific attribution when possible.",
            ],
        }
        content = self.client.invoke_json(SEMANTIC_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
        return SemanticExtractionDraft.model_validate_json(content)

    def _finalize_topics(self, course: NormalizedCourse, drafts: list[SemanticTopicDraft]) -> list[TopicOut]:
        chapter_lookup = _chapter_lookup(course)
        fallback_chapter_index = course.chapters[0].chapter_index if course.chapters else 1
        topics: list[TopicOut] = []
        used_ids: Counter[str] = Counter()
        for draft in drafts:
            chapter_index = draft.chapter_index if draft.chapter_index in chapter_lookup else fallback_chapter_index
            chapter_id, chapter_title = chapter_lookup.get(chapter_index, (chapter_id_for(course.course_id, chapter_index), course.title))
            base_id = f"{course.course_id}_topic_{slugify(draft.label) or 'topic'}"
            used_ids[base_id] += 1
            topic_id = base_id if used_ids[base_id] == 1 else f"{base_id}_{used_ids[base_id]}"
            topic_type = draft.topic_type if draft.topic_type in {
                "concept", "procedure", "tool", "metric_test", "contrast", "confusion", "prerequisite", "advanced"
            } else "concept"
            topics.append(
                TopicOut(
                    topic_id=topic_id,
                    course_id=course.course_id,
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    label=draft.label.strip(),
                    aliases=_dedupe_strs(draft.aliases),
                    topic_type=topic_type,
                    prerequisites=_dedupe_strs(draft.prerequisites),
                    contrasts=_dedupe_strs(draft.contrasts),
                    confusions=_dedupe_strs(draft.confusions),
                    evidence=draft.evidence,
                    importance=max(0.0, min(draft.importance, 1.0)),
                )
            )
        if topics:
            return topics
        # Minimal fallback when semantic extraction under-produces.
        fallback_topics: list[TopicOut] = []
        for chapter in course.chapters:
            label = chapter.title.strip()
            if not label:
                continue
            fallback_topics.append(
                TopicOut(
                    topic_id=f"{course.course_id}_topic_{slugify(label)}",
                    course_id=course.course_id,
                    chapter_id=chapter_id_for(course.course_id, chapter.chapter_index),
                    chapter_title=chapter.title,
                    label=label,
                    aliases=[],
                    topic_type="concept",
                    evidence=[SourceEvidenceOut(field=f"syllabus[{chapter.chapter_index - 1}].title", excerpt=chapter.title)],
                    importance=0.5,
                )
            )
        return fallback_topics

    def _finalize_frictions(self, course: NormalizedCourse, drafts: list[SemanticFrictionDraft]) -> list[LearnerFrictionCandidateOut]:
        chapter_lookup = _chapter_lookup(course)
        fallback_chapter_index = course.chapters[0].chapter_index if course.chapters else 1
        frictions: list[LearnerFrictionCandidateOut] = []
        used_ids: Counter[str] = Counter()
        for draft in drafts:
            chapter_index = draft.chapter_index if draft.chapter_index in chapter_lookup else fallback_chapter_index
            chapter_id, chapter_title = chapter_lookup.get(chapter_index, (chapter_id_for(course.course_id, chapter_index), course.title))
            candidate_type = draft.candidate_type if draft.candidate_type in {
                "term", "acronym", "method", "test", "process", "contrast", "overloaded_term"
            } else "term"
            base_id = f"{course.course_id}_fc_{slugify(draft.text) or 'candidate'}"
            used_ids[base_id] += 1
            candidate_id = base_id if used_ids[base_id] == 1 else f"{base_id}_{used_ids[base_id]}"
            frictions.append(
                LearnerFrictionCandidateOut(
                    candidate_id=candidate_id,
                    course_id=course.course_id,
                    chapter_id=chapter_id,
                    chapter_title=chapter_title,
                    text=draft.text.strip(),
                    candidate_type=candidate_type,
                    evidence=draft.evidence,
                    confidence=max(0.0, min(draft.confidence, 1.0)),
                )
            )
        return frictions

    def _generate_candidate_questions(
        self,
        course: NormalizedCourse,
        topics: list[TopicOut],
        frictions: list[LearnerFrictionCandidateOut],
    ) -> list[CandidateQuestionOut]:
        payload = {
            "course": _course_prompt_payload(course),
            "topics": [topic.model_dump(mode="json") for topic in topics],
            "friction_candidates": [candidate.model_dump(mode="json") for candidate in frictions],
            "instructions": [
                "Generate likely learner questions only.",
                "Use the topic labels already supplied.",
                "Favor natural learner wording.",
                "Cover definition, purpose, intuition, how-to, comparison, misconception, application, limitation, and interpretation when supported.",
                "Return 8 to 24 questions for the course unless the source text is too sparse.",
                "Use mastery bands novice, developing, or proficient.",
            ],
        }
        content = self.client.invoke_json(QUESTION_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False, indent=2))
        parsed = self._parse_candidate_question_drafts(content)
        return self._finalize_questions(course, topics, frictions, parsed.questions)

    def _parse_candidate_question_drafts(self, content: str) -> CandidateQuestionDraftList:
        payload = json.loads(content)
        questions = payload.get("questions") or []
        normalized_questions: list[dict] = []
        for item in questions:
            if not isinstance(item, dict):
                continue
            question_text = item.get("question_text") or item.get("question") or item.get("text")
            topic_label = item.get("topic_label") or item.get("topic") or item.get("topic_name")
            mastery_band = item.get("mastery_band") or item.get("mastery") or item.get("mastery_level")
            question_type = item.get("question_type") or item.get("type") or self._infer_question_type(question_text or "")
            generation_basis = item.get("generation_basis")
            if not generation_basis:
                generation_basis = {
                    "source_kind": "topic",
                    "source_id": slugify(topic_label or "topic"),
                    "rationale": "Generated from the supplied topic label.",
                }
            score = item.get("score")
            if score is None:
                score = item.get("overall_score") or item.get("learner_likelihood") or 0.7
            normalized_questions.append(
                {
                    "question_text": question_text,
                    "chapter_index": item.get("chapter_index"),
                    "topic_label": topic_label,
                    "mastery_band": mastery_band,
                    "question_type": question_type,
                    "source_evidence": item.get("source_evidence") or [],
                    "generation_basis": generation_basis,
                    "score": score,
                }
            )
        return CandidateQuestionDraftList.model_validate({"questions": normalized_questions})

    def _infer_question_type(self, question_text: str) -> str:
        lower = question_text.lower()
        if lower.startswith("why "):
            return "purpose"
        if lower.startswith("how do") or lower.startswith("how can"):
            return "how_to"
        if lower.startswith("when "):
            return "when_to_use"
        if "difference" in lower or "different from" in lower or "compare" in lower:
            return "comparison"
        if "mistake" in lower or "wrong" in lower or "confuse" in lower:
            return "misconception"
        if "mean" in lower or "tell me" in lower or "interpret" in lower:
            return "interpretation"
        return "definition"

    def _parse_review_answer_drafts(self, content: str) -> ReviewAnswerDraftList:
        payload = json.loads(content)
        answers = payload.get("answers") or []
        normalized_answers: list[dict] = []
        for item in answers:
            if not isinstance(item, dict):
                continue
            normalized_answers.append(
                {
                    "question_id": item.get("question_id"),
                    "answer_markdown": item.get("answer_markdown") or item.get("answer") or item.get("response") or "",
                }
            )
        return ReviewAnswerDraftList.model_validate({"answers": normalized_answers})

    def _fallback_semantic_units(self, course: NormalizedCourse) -> SemanticExtractionDraft:
        topics: list[SemanticTopicDraft] = []
        frictions: list[SemanticFrictionDraft] = []
        for chapter in course.chapters:
            field_prefix = f"syllabus[{chapter.chapter_index - 1}]"
            topics.append(
                SemanticTopicDraft(
                    label=chapter.title,
                    topic_type="procedure" if chapter.title.lower().startswith("case study") else "concept",
                    chapter_index=chapter.chapter_index,
                    evidence=[
                        SourceEvidenceOut(field=f"{field_prefix}.title", excerpt=chapter.title),
                        SourceEvidenceOut(field=f"{field_prefix}.summary", excerpt=chapter.summary or ""),
                    ],
                    importance=0.6,
                )
            )
            for token in re.findall(r"\b[A-Z]{2,}(?:-[A-Z]+)?\b", f"{chapter.title} {chapter.summary or ''}"):
                frictions.append(
                    SemanticFrictionDraft(
                        text=token,
                        candidate_type="acronym",
                        chapter_index=chapter.chapter_index,
                        evidence=[SourceEvidenceOut(field=f"{field_prefix}.summary", excerpt=chapter.summary or chapter.title)],
                        confidence=0.7,
                    )
                )
            for phrase in re.findall(r"\b[a-zA-Z]+(?:\s+[a-zA-Z]+){0,2}\b", chapter.title):
                lower = phrase.lower()
                if lower in {"and", "in", "with", "data", "study", "case"}:
                    continue
                if "time series" in lower or "arima" in lower or "smoothing" in lower or "accuracy" in lower or "benchmark" in lower:
                    frictions.append(
                        SemanticFrictionDraft(
                            text=phrase,
                            candidate_type="term",
                            chapter_index=chapter.chapter_index,
                            evidence=[SourceEvidenceOut(field=f"{field_prefix}.title", excerpt=chapter.title)],
                            confidence=0.55,
                        )
                    )
        return SemanticExtractionDraft(topics=topics, friction_candidates=frictions)

    def _fallback_candidate_questions(
        self,
        course: NormalizedCourse,
        topics: list[TopicOut],
        frictions: list[LearnerFrictionCandidateOut],
    ) -> list[CandidateQuestionOut]:
        drafts: list[CandidateQuestionDraft] = []
        for topic in topics:
            label = topic.label.strip()
            basis = GenerationBasisOut(
                source_kind="topic",
                source_id=topic.topic_id,
                rationale="Fallback generation from extracted topic.",
            )
            if topic.topic_type == "procedure" or label.lower().startswith(("exploring", "visualizing", "forecasting", "analyzing")):
                drafts.append(
                    CandidateQuestionDraft(
                        question_text=f"How do I {label[0].lower() + label[1:]}?",
                        topic_label=label,
                        mastery_band="novice",
                        question_type="how_to",
                        source_evidence=topic.evidence,
                        generation_basis=basis,
                        score=0.68,
                    )
                )
            else:
                drafts.append(
                    CandidateQuestionDraft(
                        question_text=f"What is {label[0].lower() + label[1:]}?",
                        topic_label=label,
                        mastery_band="novice",
                        question_type="definition",
                        source_evidence=topic.evidence,
                        generation_basis=basis,
                        score=0.66,
                    )
                )
                drafts.append(
                    CandidateQuestionDraft(
                        question_text=f"Why does {label[0].lower() + label[1:]} matter?",
                        topic_label=label,
                        mastery_band="developing",
                        question_type="purpose",
                        source_evidence=topic.evidence,
                        generation_basis=basis,
                        score=0.58,
                    )
                )
        for friction in frictions:
            source_kind = "friction_candidate"
            basis = GenerationBasisOut(
                source_kind=source_kind,
                source_id=friction.candidate_id,
                rationale="Fallback generation from learner-friction term.",
            )
            if friction.candidate_type == "acronym":
                question_text = f"What does {friction.text} stand for?"
                question_type = "definition"
            elif friction.candidate_type in {"method", "test", "process"}:
                question_text = f"Why do we use {friction.text}?"
                question_type = "purpose"
            else:
                question_text = f"What is {friction.text}?"
                question_type = "definition"
            drafts.append(
                CandidateQuestionDraft(
                    question_text=question_text,
                    chapter_index=None,
                    topic_label=friction.text,
                    mastery_band="novice",
                    question_type=question_type,
                    source_evidence=friction.evidence,
                    generation_basis=basis,
                    score=0.62,
                )
            )
        return self._finalize_questions(course, topics, frictions, drafts)

    def _finalize_questions(
        self,
        course: NormalizedCourse,
        topics: list[TopicOut],
        frictions: list[LearnerFrictionCandidateOut],
        drafts: list[CandidateQuestionDraft],
    ) -> list[CandidateQuestionOut]:
        topic_by_slug = {slugify(topic.label): topic for topic in topics}
        topic_by_id = {topic.topic_id: topic for topic in topics}
        friction_by_id = {candidate.candidate_id: candidate for candidate in frictions}
        friction_by_slug = {slugify(candidate.text): candidate for candidate in frictions}
        chapter_lookup = _chapter_lookup(course)
        question_by_key: dict[str, CandidateQuestionOut] = {}
        id_counts: Counter[str] = Counter()

        for draft in drafts:
            question_text = draft.question_text.strip()
            if not question_text:
                continue
            normalized = normalize_question_text(question_text)
            if not normalized:
                continue
            topic = topic_by_slug.get(slugify(draft.topic_label))
            if topic is None and draft.generation_basis.source_kind == "friction_candidate":
                friction = friction_by_id.get(draft.generation_basis.source_id) or friction_by_slug.get(slugify(draft.topic_label))
                if friction is not None:
                    synthetic_key = f"{course.course_id}_topic_{slugify(friction.text)}"
                    topic = topic_by_id.get(synthetic_key)
                    if topic is None:
                        topic = TopicOut(
                            topic_id=synthetic_key,
                            course_id=course.course_id,
                            chapter_id=friction.chapter_id,
                            chapter_title=friction.chapter_title,
                            label=friction.text,
                            topic_type="concept",
                            evidence=friction.evidence,
                            importance=friction.confidence,
                        )
                        topic_by_id[topic.topic_id] = topic
            if topic is None and topics:
                topic = topics[0]
            if topic is None:
                continue
            chapter_id = topic.chapter_id
            chapter_title = topic.chapter_title
            if draft.chapter_index in chapter_lookup:
                chapter_id, chapter_title = chapter_lookup[draft.chapter_index]
            mastery_band = draft.mastery_band if draft.mastery_band in {"novice", "developing", "proficient"} else "novice"
            question_type = draft.question_type if draft.question_type in {
                "definition",
                "purpose",
                "intuition",
                "how_to",
                "when_to_use",
                "common_error",
                "comparison",
                "misconception",
                "application",
                "limitation",
                "interpretation",
            } else "definition"
            score = max(0.0, min(float(draft.score), 1.0))
            if score < 0.35:
                continue
            key = f"{course.course_id}:{normalized}:{mastery_band}:{question_type}"
            base_id = f"{course.course_id}_{slugify(question_text)[:72] or 'question'}"
            id_counts[base_id] += 1
            question_id = base_id if id_counts[base_id] == 1 else f"{base_id}_{id_counts[base_id]}"
            candidate = CandidateQuestionOut(
                question_id=question_id,
                course_id=course.course_id,
                question_text=question_text,
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                topic_id=topic.topic_id,
                topic_label=topic.label,
                mastery_band=mastery_band,
                question_type=question_type,
                source_evidence=draft.source_evidence,
                generation_basis=draft.generation_basis,
                score=score,
            )
            existing = question_by_key.get(key)
            if existing is None or candidate.score > existing.score:
                question_by_key[key] = candidate

        return sorted(
            question_by_key.values(),
            key=lambda item: (item.chapter_id, item.topic_label.lower(), item.mastery_band, -item.score, item.question_text.lower()),
        )


def write_question_gen_v2_report(
    run_dir: Path,
    questions: list[CandidateQuestionOut],
    topics: list[TopicOut],
    frictions: list[LearnerFrictionCandidateOut],
) -> Path:
    report_path = run_dir / "question_gen_v2_report.md"
    question_counts = Counter(question.course_id for question in questions)
    topic_counts = Counter(topic.course_id for topic in topics)
    friction_counts = Counter(candidate.course_id for candidate in frictions)
    by_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_band: dict[str, Counter[str]] = defaultdict(Counter)
    for question in questions:
        by_type[question.course_id][question.question_type] += 1
        by_band[question.course_id][question.mastery_band] += 1

    lines = ["# Question Generation V2 Report", ""]
    course_ids = sorted(question_counts or topic_counts or friction_counts)
    for course_id in course_ids:
        lines.append(f"## Course `{course_id}`")
        lines.append("")
        lines.append(f"- topics: {topic_counts.get(course_id, 0)}")
        lines.append(f"- learner-friction candidates: {friction_counts.get(course_id, 0)}")
        lines.append(f"- candidate questions: {question_counts.get(course_id, 0)}")
        if by_type.get(course_id):
            lines.append(f"- question types: {json.dumps(dict(sorted(by_type[course_id].items())), ensure_ascii=False)}")
        if by_band.get(course_id):
            lines.append(f"- mastery bands: {json.dumps(dict(sorted(by_band[course_id].items())), ensure_ascii=False)}")
        lines.append("")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def load_question_gen_v2_run(run_dir: Path) -> tuple[list[NormalizedCourse], list[CandidateQuestionOut]]:
    courses = [
        NormalizedCourse.model_validate_json(line)
        for line in (run_dir / "courses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    questions = [
        CandidateQuestionOut.model_validate_json(line)
        for line in (run_dir / "candidate_questions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return courses, questions


def write_review_answers_jsonl(path: Path, rows: list[dict]) -> Path:
    write_jsonl(path, rows)
    return path
