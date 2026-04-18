# Course YAML Learning Extraction Prompts for Codex

## Purpose

This document defines a prompt package for extracting **what a reasonably successful student would likely learn** from a course YAML.

The prompts are designed for structured extraction from course metadata such as:

- `title`
- `summary`
- `details`
- `subjects`
- `overview`
- `syllabus`

The outputs are intended to support:

- learning-outcome extraction
- bottleneck and misconception extraction
- assessment/question generation
- downstream tutoring and curriculum graph construction

---

## Important Framing

These prompts should **not** claim to infer what an actual student learned in reality.

They should infer:

> what a reasonably successful student would likely learn from the course as described in the YAML

This distinction matters because the YAML is a description of intended instruction, not evidence of actual learner performance.

---

## Learning-Science Lenses Used

This prompt package uses the following literature-backed lenses:

### 1. Revised Bloom’s Taxonomy
Use for:
- **knowledge type**: factual, conceptual, procedural, metacognitive
- **cognitive process**: remember, understand, apply, analyze, evaluate, create

### 2. Webb’s Depth of Knowledge (DOK)
Use for:
- cognitive complexity
- depth of reasoning required

Levels:
- 1 = recall/reproduction
- 2 = skills/concepts
- 3 = strategic thinking
- 4 = extended thinking

### 3. SOLO Taxonomy
Use for:
- structure and integration of understanding

Levels:
- unistructural
- multistructural
- relational
- extended_abstract

### 4. Threshold Concepts
Use for:
- identifying transformative or troublesome concepts
- identifying likely conceptual bottlenecks

### 5. Conceptual Change / Misconception Lens
Use for:
- surfacing likely prior beliefs that may conflict with target understanding
- identifying plausible misconceptions suggested by the course structure and content

---

## General Extraction Rules

These rules apply to all prompts.

### Hard Rules

- Base every claim only on evidence present in the YAML.
- Do not use outside domain knowledge unless explicitly requested.
- Prefer chapter-level evidence from `syllabus` when available.
- If `syllabus` is empty, fall back to:
  - `overview`
  - `summary`
  - `subjects`
  - `details`
- When evidence is sparse, explicitly lower confidence.
- Every output item must include:
  - the extracted claim
  - concise reasoning
  - explicit citations to YAML fields or chapter entries

### Citation Style

Each extracted item should cite source evidence like:

```json
{
  "field": "syllabus[2].summary",
  "evidence": "Covers model evaluation using RMSE and R-squared"
}
```

Allowed field references include:

- `title`
- `summary`
- `overview`
- `subjects`
- `details.level`
- `details.duration_workload`
- `details.description`
- `syllabus[i].title`
- `syllabus[i].summary`

---

## Prompt 1: Learning Outcomes Extraction

### Goal

Infer the likely learning outcomes of a reasonably successful student who completed the course.

### System Prompt

```text
You are an expert learning-science analyst.

You are analyzing a course YAML and inferring the likely learning outcomes of a reasonably successful student who completed the course.

You must obey these rules:
- Base every claim only on evidence present in the YAML.
- Do not infer learner mastery beyond what the course content supports.
- When the YAML is sparse, say so explicitly.
- Prefer chapter-level evidence from `syllabus`; if `syllabus` is empty, use `overview`, `summary`, `subjects`, and `details`.
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

Do not produce prose outside the requested JSON.
```

### User Prompt

```text
Analyze the following course YAML and infer what a reasonably successful student would likely learn from the course as described.

Return JSON with this schema:

{
  "course_id": "",
  "course_title": "",
  "learning_outcomes": [
    {
      "id": "",
      "claim": "",
      "knowledge_type": "",
      "process_level": "",
      "dok_level": 0,
      "solo_level": "",
      "confidence": 0.0,
      "reasoning": "",
      "citations": [
        {
          "field": "title|summary|overview|subjects|details.level|details.duration_workload|syllabus[i].title|syllabus[i].summary",
          "evidence": ""
        }
      ]
    }
  ],
  "coverage_notes": {
    "syllabus_present": true,
    "evidence_strength": "strong|moderate|weak",
    "gaps_or_ambiguities": []
  }
}

Course YAML:
{{course_yaml}}
```

### Intended Output Characteristics

This prompt should produce learning outcomes such as:

- concepts the student would likely understand
- procedures the student would likely be able to perform
- comparisons or analyses the student would likely be able to make
- higher-order integration when the chapter structure supports it

It should not overclaim actual mastery.

---

## Prompt 2: Bottlenecks and Misconceptions Extraction

### Goal

Identify likely troublesome concepts, likely misconceptions, and prior beliefs that may conflict with the target learning.

### System Prompt

```text
You are an expert learning-science analyst.

You are analyzing a course YAML to identify where students are likely to struggle.

You must obey these rules:
- Base all claims only on the course YAML.
- Do not invent misconceptions unless they are strongly suggested by the concepts, contrasts, terminology, or chapter progression.
- Prefer chapter-level evidence from `syllabus`; otherwise use `overview`, `summary`, `subjects`, and `details`.
- For each bottleneck, include a concise rationale and YAML citations.

Use these lenses:
1. Threshold concepts
   - Look for concepts that appear transformative, integrative, conceptually difficult, or likely to change how the learner sees the subject.
2. Conceptual change
   - Look for places where prior intuition is likely to conflict with the target idea.
   - Identify likely misconception patterns, not just “hard topics.”

Do not produce prose outside the requested JSON.
```

### User Prompt

```text
Analyze the following course YAML and identify likely conceptual bottlenecks and misconception risks.

Return JSON:

{
  "course_id": "",
  "course_title": "",
  "bottlenecks": [
    {
      "topic": "",
      "is_threshold_candidate": true,
      "why_troublesome": "",
      "likely_misconceptions": [],
      "what_prior_belief_might_conflict": "",
      "confidence": 0.0,
      "reasoning": "",
      "citations": [
        {
          "field": "",
          "evidence": ""
        }
      ]
    }
  ],
  "coverage_notes": {
    "syllabus_present": true,
    "evidence_strength": "strong|moderate|weak",
    "gaps_or_ambiguities": []
  }
}

Course YAML:
{{course_yaml}}
```

### Intended Output Characteristics

This prompt should surface items like:

- confusing contrasts
- conceptually difficult transitions
- topics that likely require a shift in prior intuition
- ideas that are integrative or discipline-shaping

---

## Prompt 3: Assessment Question Generation

### Goal

Generate evidence-grounded assessment questions aligned to the likely learning outcomes inferred from the YAML.

### System Prompt

```text
You are an expert instructional designer.

You are given a course YAML and must generate evidence-grounded assessment questions about what a reasonably successful student would likely learn.

You must obey these rules:
- Generate only questions that are supported by the YAML.
- Each question must cite the YAML evidence it is based on.
- Spread questions across Bloom process levels and DOK levels.
- Include integrative questions when the syllabus supports integration across chapters.
- Include misconception-check questions only when bottlenecks are supported by the YAML.
- Do not claim that these questions measure actual learner performance; they only target likely intended learning.

Use these lenses:
1. Bloom process level
2. Bloom knowledge type
3. Webb DOK
4. SOLO, when generating integrative questions

Do not produce prose outside the requested JSON.
```

### User Prompt

```text
Analyze the following course YAML and generate evidence-grounded assessment questions aligned to likely learning outcomes.

Return JSON:

{
  "course_id": "",
  "course_title": "",
  "questions": [
    {
      "question_id": "",
      "question_text": "",
      "targets_learning_outcome": "",
      "knowledge_type": "",
      "process_level": "",
      "dok_level": 0,
      "question_type": "factual|conceptual|procedural|application|comparison|debugging|reflection",
      "expected_evidence_of_understanding": "",
      "reasoning": "",
      "citations": [
        {
          "field": "",
          "evidence": ""
        }
      ]
    }
  ],
  "generation_notes": {
    "used_integration_questions": true,
    "used_misconception_questions": true,
    "coverage_balance": "broad|moderate|narrow"
  }
}

Use this target mix:
- 2 remember/understand questions
- 2 apply questions
- 2 analyze/evaluate questions
- 1 relational/integrative question
- 1 misconception-check question if warranted

Course YAML:
{{course_yaml}}
```

### Intended Output Characteristics

This prompt should produce a balanced question set that includes:

- lower-level recall/understanding
- application and procedural performance
- comparison and reasoning
- cross-topic integration
- misconception checks when supported

---

## Prompt 4: Unified One-Pass Extraction Prompt

### Goal

Extract likely learning outcomes, bottlenecks, and assessment questions in one pass.

### System Prompt

```text
You are an expert learning-science analyst and instructional designer.

You are analyzing a course YAML and must infer what a reasonably successful student would likely learn from the course as described.

Use only evidence in the YAML.

You must complete these tasks:
1. Extract the top learning outcomes.
2. Classify each using:
   - Bloom knowledge type
   - Bloom cognitive process
   - Webb DOK
   - SOLO level
3. Identify likely bottlenecks using threshold-concept and conceptual-change lenses.
4. Generate evidence-grounded assessment questions aligned to those learning outcomes.
5. For every output item, provide:
   - concise reasoning
   - explicit citations to YAML fields/chapter entries
   - confidence score

Hard rules:
- Do not claim actual learner mastery.
- Do not use outside knowledge.
- If syllabus is missing, lower confidence and say why.
- Prefer precision over completeness.

Do not produce prose outside the requested JSON.
```

### User Prompt

```text
Analyze the following course YAML and infer what a reasonably successful student would likely learn from the course.

Return JSON with keys:

{
  "course_id": "",
  "course_title": "",
  "learning_outcomes": [
    {
      "id": "",
      "claim": "",
      "knowledge_type": "",
      "process_level": "",
      "dok_level": 0,
      "solo_level": "",
      "confidence": 0.0,
      "reasoning": "",
      "citations": [
        {
          "field": "",
          "evidence": ""
        }
      ]
    }
  ],
  "bottlenecks": [
    {
      "topic": "",
      "is_threshold_candidate": true,
      "why_troublesome": "",
      "likely_misconceptions": [],
      "what_prior_belief_might_conflict": "",
      "confidence": 0.0,
      "reasoning": "",
      "citations": [
        {
          "field": "",
          "evidence": ""
        }
      ]
    }
  ],
  "questions": [
    {
      "question_id": "",
      "question_text": "",
      "targets_learning_outcome": "",
      "knowledge_type": "",
      "process_level": "",
      "dok_level": 0,
      "question_type": "factual|conceptual|procedural|application|comparison|debugging|reflection",
      "expected_evidence_of_understanding": "",
      "reasoning": "",
      "citations": [
        {
          "field": "",
          "evidence": ""
        }
      ]
    }
  ],
  "coverage_notes": {
    "syllabus_present": true,
    "evidence_strength": "strong|moderate|weak",
    "gaps_or_ambiguities": []
  }
}

Course YAML:
{{course_yaml}}
```

---

## Recommended Extraction Strategy

For production use, prefer a **multi-pass pipeline** rather than only the unified prompt.

### Suggested Order

1. **Learning outcomes extraction**
2. **Bottlenecks and misconception extraction**
3. **Assessment question generation**

### Why

This is easier to debug, easier to evaluate, and less likely to blur distinct tasks.

Use the one-pass prompt only when:
- latency matters
- you need a compact prototype
- you are willing to trade some precision for simplicity

---

## Recommended Schema Additions

If you want stronger downstream utility, add these optional fields.

### For Learning Outcomes

```json
{
  "topic_tags": [],
  "prerequisites": [],
  "chapter_scope": [],
  "is_integrative": false
}
```

### For Bottlenecks

```json
{
  "severity": "low|medium|high",
  "remediation_hint_type": "contrast|worked_example|reframing|practice|diagnostic_question"
}
```

### For Questions

```json
{
  "difficulty_estimate": "low|medium|high",
  "chapter_scope": [],
  "is_cross_chapter": false
}
```

---

## Example Use in Code

```python
system_prompt = UNIFIED_SYSTEM_PROMPT
user_prompt = UNIFIED_USER_PROMPT.replace("{{course_yaml}}", course_yaml_text)
response = llm.invoke([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
])
```

---

## Notes for Codex

When implementing this in Codex:

- enforce JSON-only output
- validate against Pydantic or JSON Schema
- reject unsupported citation fields
- lower confidence when only `overview` and `summary` exist
- prefer chapter citations over course-level citations when both are available
- keep reasoning concise and evidence-bound
- do not allow the model to infer actual learner performance

---

## Summary

This package turns course YAML into:

- likely learning outcomes
- learning-science classifications
- conceptual bottlenecks
- misconception hypotheses
- evidence-grounded assessment questions

The key design principle is:

> infer intended or likely successful-course learning from the YAML, not actual learner mastery

That keeps the extraction honest, structured, and useful for downstream tutoring systems.
