from __future__ import annotations

import json
import urllib.error
import urllib.request

from pydantic import ValidationError

from course_pipeline.config import Settings
from course_pipeline.schemas import LearningOutcomeExtractionOut, NormalizedCourse


ALLOWED_CITATION_FIELDS = {
    "title",
    "summary",
    "overview",
    "subjects",
    "details.level",
    "details.duration_workload",
    "details.description",
}


def _allowed_syllabus_field(field: str) -> bool:
    if not field.startswith("syllabus["):
        return False
    return field.endswith("].title") or field.endswith("].summary")


SYSTEM_PROMPT = """You are an expert learning-science analyst.

You are analyzing a course YAML and inferring the likely learning outcomes of a reasonably successful student who completed the course.

You must obey these rules:
- Base every claim only on evidence present in the YAML.
- Do not infer learner mastery beyond what the course content supports.
- When the YAML is sparse, say so explicitly.
- Prefer chapter-level evidence from syllabus; if syllabus is empty, use overview, summary, subjects, and details.
- For every output item, include:
  - a short learning claim
  - a brief rationale
  - explicit citations to YAML fields or chapter titles/summaries

Use these lenses:
1. Revised Bloom's Taxonomy
   - knowledge_type: factual | conceptual | procedural | metacognitive
   - process_level: remember | understand | apply | analyze | evaluate | create
2. Webb DOK
   - dok_level: 1 | 2 | 3 | 4
3. SOLO
   - solo_level: unistructural | multistructural | relational | extended_abstract

Return JSON only.
"""


USER_PROMPT_TEMPLATE = """Analyze the following course YAML and infer what a reasonably successful student would likely learn from the course as described.

Return JSON with this schema:
{{
  "course_id": "",
  "course_title": "",
  "learning_outcomes": [
    {{
      "id": "",
      "claim": "",
      "knowledge_type": "",
      "process_level": "",
      "dok_level": 0,
      "solo_level": "",
      "confidence": 0.0,
      "reasoning": "",
      "citations": [
        {{
          "field": "title|summary|overview|subjects|details.level|details.duration_workload|details.description|syllabus[i].title|syllabus[i].summary",
          "evidence": ""
        }}
      ]
    }}
  ],
  "coverage_notes": {{
    "syllabus_present": true,
    "evidence_strength": "strong|moderate|weak",
    "gaps_or_ambiguities": []
  }}
}}

Course YAML:
{course_yaml}
"""


class LearningOutcomeExtractor:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for learning-outcome extraction")
        self.settings = settings

    def extract(self, course: NormalizedCourse) -> LearningOutcomeExtractionOut:
        course_yaml = self._to_prompt_yaml(course)
        body = {
            "model": self.settings.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(course_yaml=course_yaml)},
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

        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected OpenAI response shape: {payload}") from exc

        try:
            parsed = LearningOutcomeExtractionOut.model_validate_json(content)
        except ValidationError as exc:
            raise RuntimeError(f"Learning-outcome payload failed validation: {exc}") from exc

        return self._validate_and_adjust(parsed, course)

    def _validate_and_adjust(
        self,
        extraction: LearningOutcomeExtractionOut,
        course: NormalizedCourse,
    ) -> LearningOutcomeExtractionOut:
        syllabus_present = any(ch.source == "syllabus" for ch in course.chapters)
        citations_are_chapter_level = True

        for outcome in extraction.learning_outcomes:
            if not outcome.citations:
                raise RuntimeError(f"Outcome {outcome.id} is missing citations")
            for citation in outcome.citations:
                if citation.field not in ALLOWED_CITATION_FIELDS and not _allowed_syllabus_field(citation.field):
                    raise RuntimeError(f"Unsupported citation field: {citation.field}")
                if citation.field.startswith("syllabus[") and not syllabus_present:
                    raise RuntimeError(f"Syllabus citation used for course without syllabus: {citation.field}")
                if not citation.field.startswith("syllabus["):
                    citations_are_chapter_level = False

        if not syllabus_present:
            extraction.coverage_notes.syllabus_present = False
            if extraction.coverage_notes.evidence_strength == "strong":
                extraction.coverage_notes.evidence_strength = "moderate"

        if not citations_are_chapter_level:
            for outcome in extraction.learning_outcomes:
                outcome.confidence = min(outcome.confidence, 0.75)

        return extraction

    def _to_prompt_yaml(self, course: NormalizedCourse) -> str:
        syllabus_entries = [
            {
                "title": chapter.title,
                "summary": chapter.summary,
            }
            for chapter in course.chapters
            if chapter.source == "syllabus"
        ]
        payload = {
            "course_id": course.course_id,
            "title": course.title,
            "summary": course.summary,
            "overview": course.overview,
            "subjects": course.subjects,
            "details": {
                "level": course.level,
                "duration_workload": course.details.get("duration_workload"),
                "description": course.details.get("description"),
            },
            "syllabus": syllabus_entries,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
