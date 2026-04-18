# Question Generation Algorithm V2

This document consolidates the strongest parts of the two V2 proposals:

- use `question_gen_algo_v2_proposal_2.md` as the base architecture
- add three improvements from `question_gen_algo_v2_proposal.md`
  - explicit learner-friction extraction
  - natural-language preference rules
  - stronger provenance for why a question was generated

The result is a cleaner, implementation-oriented design for generating candidate learner questions from scraped course YAML.

## Objective

Implement a pipeline that generates likely learner questions for a course from scraped course YAML.

The goal is question discovery only.

This document does not include:
- answer generation
- cache IDs
- runtime matching
- serving logic
- personalized learner prediction

Those are downstream concerns.

## Core Design Principle

The generation unit should be:

`(chapter, topic, question_type, mastery_band)`

Do not generate directly from:

`(learning claim -> paraphrases)`

That older pattern tends to produce shallow, syllabus-shaped questions instead of natural learner questions.

## Main Improvement Over V1

The pipeline should generate questions from a richer semantic structure, not just from learning claims.

It should use:
- chapter context
- extracted topics
- prerequisite relationships
- contrasts
- likely confusion points
- learner-friction terms
- question type
- mastery band

This allows the system to produce questions like:
- `What is exponential smoothing?`
- `Why do we use benchmark methods?`
- `What does ARIMA stand for?`
- `How do I visualize a time series in R?`

instead of only claim-shaped prompts like:
- `How do I apply exponential smoothing methods to forecast time series data in R?`

## Inputs

Input is a scraped course YAML-like object with fields such as:
- `title`
- `summary`
- `overview`
- `syllabus`

`syllabus` is preferred when available.
If `syllabus` is missing or sparse, infer chapter structure from `overview`.

## Outputs

Return a list of candidate question objects:

```json
{
  "question_id": "string",
  "question_text": "string",
  "chapter_id": "string",
  "chapter_title": "string",
  "topic_id": "string",
  "topic_label": "string",
  "mastery_band": "novice | developing | proficient",
  "question_type": "definition | purpose | intuition | how_to | when_to_use | common_error | comparison | misconception | application | limitation | interpretation",
  "source_evidence": [
    {
      "field": "summary | overview | syllabus",
      "excerpt": "string"
    }
  ],
  "generation_basis": {
    "source_kind": "topic | friction_candidate | contrast | confusion | prerequisite",
    "source_id": "string",
    "rationale": "string"
  },
  "score": 0.0
}
```

## Non-Goals

Do not implement:
- canonical answers
- paraphrase or variation generation
- cache storage
- runtime semantic matching
- session-aware adaptation

## High-Level Algorithm

### 1. Parse course

Extract:
- title
- summary
- overview
- syllabus

If `syllabus` is missing or empty:
- infer chapter blocks from overview text

### 2. Build chapter records

For each chapter, create:
- `chapter_id`
- `chapter_title`
- `chapter_summary`
- `chapter_order`

### 3. Extract learning units per chapter

For each chapter, extract:
- concepts
- procedures
- tools
- metrics or tests
- contrasts
- prerequisites
- confusions

Examples:
- concept: `exponential smoothing`
- procedure: `visualize a time series`
- metric or test: `forecast accuracy`, `Ljung-Box test`
- contrast: `ARIMA vs exponential smoothing`
- confusion: `benchmark vs benchmark method`

### 4. Extract learner-friction candidates

This is the first major addition to proposal 2.

For each course and chapter, explicitly extract terms and phrases likely to trigger learner questions.

Typical friction candidates include:
- technical terms
- acronyms
- named methods
- tests
- process steps
- statistical language
- overloaded terms
- terms introduced without explanation

Examples from `Forecasting in R (24491)`:
- `ARIMA`
- `exponential smoothing`
- `benchmark methods`
- `forecast accuracy`
- `white noise`
- `Ljung-Box test`
- `trend`
- `seasonality`
- `repeated cycles`

These candidates are not yet questions. They are generation signals.

### 5. Normalize topics

Merge near-duplicate topics across chapters only when they represent the same intent.

Keep:
- canonical `topic_id`
- canonical label
- aliases

Do not merge topics that differ pedagogically even if they are textually similar.

### 6. Create question opportunities

For each topic or friction candidate, generate question slots based on semantic type.

Examples:

- concept
  - definition
  - purpose
  - intuition

- procedure
  - how_to
  - when_to_use
  - common_error

- metric or test
  - definition
  - purpose
  - interpretation

- contrast pair
  - comparison
  - when_to_choose

- confusion pair
  - misconception
  - disambiguation

- advanced topic
  - application
  - limitation

### 7. Expand by mastery band

For each question slot, generate versions for:
- novice
- developing
- proficient

Examples:
- novice: `What is exponential smoothing?`
- developing: `Why do recent observations get more weight in exponential smoothing?`
- proficient: `When is exponential smoothing preferable to ARIMA?`

### 8. Generate candidate questions

For each `(chapter, topic, question_type, mastery_band)` tuple, generate one or more candidate learner questions.

Questions must satisfy these hard constraints:
- answerable from course evidence
- phrased like a natural learner question
- pedagogically useful
- not pure metadata or navigation unless explicitly allowed

### 9. Apply natural-language preference rules

This is the second major addition to proposal 2.

Prefer questions that:
- sound like a real learner would say them
- use short, plain phrasing
- ask about meaning, purpose, use, or comparison
- avoid academic or analyst-style wording

Prefer:
- `What is exponential smoothing?`
- `Why do we use benchmark methods?`
- `How do I visualize a time series in R?`

Avoid:
- `How do I apply exponential smoothing methods to forecast time series data in R?`
- `Explain the implementation of benchmark forecasting methods in applied contexts.`

In general:
- prefer learner wording over syllabus wording
- prefer direct questions over noun-phrase prompts
- prefer one clear concept per question
- prefer terms learners would type into a chat box

### 10. Score questions

Score each question using a weighted combination of:
- `grounding_score`
- `learner_likelihood`
- `pedagogical_value`
- `distinctiveness`
- `answerability`
- `naturalness`

Definitions:
- `grounding_score`: supported by source text
- `learner_likelihood`: plausibly asked by a learner
- `pedagogical_value`: helps learning, not just catalog browsing
- `distinctiveness`: not a duplicate of another question
- `answerability`: can be answered from the course
- `naturalness`: sounds like natural learner language

### 11. Filter

Drop questions that are:
- below score threshold
- duplicates
- metadata-only
- weakly grounded
- awkwardly phrased
- same intent as a better-scoring question

### 12. Canonicalize

Cluster semantically similar candidate questions and keep one canonical question per intent.

Optional:
- attach aliases or paraphrases later
- do not implement that in this stage

### 13. Return final set

Sort by:
1. chapter order
2. topic importance
3. mastery band
4. score descending

## Stronger Provenance

This is the third major addition to proposal 2.

Each generated question should preserve not only source evidence, but also why the system thought this question was worth generating.

This means every candidate should be attributable to one or more of:
- a topic
- a friction candidate
- a contrast pair
- a confusion pair
- a prerequisite link

Recommended provenance fields:
- `source_evidence`
- `generation_basis.source_kind`
- `generation_basis.source_id`
- `generation_basis.rationale`

Example:

```json
{
  "question_text": "What does ARIMA stand for?",
  "generation_basis": {
    "source_kind": "friction_candidate",
    "source_id": "24491_fc_01",
    "rationale": "ARIMA is an acronym introduced in the course text and is likely to trigger a terminology question from a novice learner."
  }
}
```

This improves auditability and makes debugging easier.

## Suggested Internal Data Models

### Chapter

```python
class Chapter:
    chapter_id: str
    chapter_title: str
    chapter_summary: str
    chapter_order: int
```

### Topic

```python
class Topic:
    topic_id: str
    label: str
    aliases: list[str]
    topic_type: str
    chapter_id: str
    prerequisites: list[str]
    contrasts: list[str]
    confusions: list[str]
    evidence: list[dict]
```

### LearnerFrictionCandidate

```python
class LearnerFrictionCandidate:
    candidate_id: str
    text: str
    candidate_type: str
    chapter_id: str | None
    evidence: list[dict]
    confidence: float
```

### CandidateQuestion

```python
class CandidateQuestion:
    question_id: str
    question_text: str
    chapter_id: str
    chapter_title: str
    topic_id: str
    topic_label: str
    mastery_band: str
    question_type: str
    source_evidence: list[dict]
    generation_basis: dict
    score: float
```

## Two-Stage Implementation Guidance

Use a two-stage design.

### Stage A: deterministic structure extraction

- parse YAML
- build chapter records
- collect raw text evidence

### Stage B: semantic extraction and generation

- extract topics
- extract learner-friction candidates
- extract contrasts, confusions, and prerequisites
- generate candidate questions
- score and filter

Keep deterministic parsing separate from LLM-based semantic extraction.

## Example: Forecasting in R (`24491`)

This course should yield candidate questions such as:
- `What is a time series?`
- `How do I visualize a time series in R?`
- `What is trend in a time series?`
- `What is seasonality?`
- `What is white noise?`
- `What is the Ljung-Box test used for?`
- `What is a benchmark method?`
- `Why do we use benchmark methods?`
- `What is forecast accuracy?`
- `What is smoothing?`
- `Why do we use smoothing?`
- `What is exponential smoothing?`
- `How does exponential smoothing work?`
- `What does ARIMA stand for?`
- `What is an ARIMA model?`
- `How is ARIMA different from exponential smoothing?`

These are better candidate questions than direct rewrites of the course claims because they align more closely with likely learner behavior.

## Acceptance Criteria

A good implementation should:
- produce grounded questions from real course content
- generate more than definition questions
- include why, how, compare, misconception, and interpretation questions
- preserve chapter context
- explicitly capture learner-friction signals
- avoid duplicates
- avoid metadata-only questions dominating output
- preserve provenance for why each question was generated
- work when syllabus is missing and chapter structure must be inferred from overview

## Recommended Pipeline Summary

`course YAML -> chapters -> topics + learner-friction candidates -> question opportunities by question_type x mastery_band -> candidate questions -> scoring/filtering -> canonicalized candidate set`
