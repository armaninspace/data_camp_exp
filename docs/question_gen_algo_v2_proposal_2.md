Here’s a Codex-ready brief. It separates **candidate question generation** from any downstream caching/serving logic, which were mixed together in the earlier repo-style pseudo-algorithm. It also uses a stronger generation unit: **(chapter, topic, question_type, mastery_band)** rather than **(claim -> paraphrase)**.

# Brief for Codex: Course Candidate Question Generation

## Objective

Implement a pipeline that generates **likely learner questions** for a course from scraped course YAML.

The goal is **question discovery only**. Do **not** include answer generation, cache IDs, runtime matching, or serving logic in this implementation.

We want questions that are:

* grounded in course content,
* pedagogically useful,
* phrased like natural learner questions,
* organized by chapter, topic, question type, and mastery band.

## Problem to Solve

The current approach overweights shallow claim-to-question rewriting and mixes generation with cache/runtime concerns.

The new pipeline should generate candidate questions from a richer semantic structure:

* chapter context
* extracted topics
* prerequisite relationships
* contrast pairs
* likely confusion points
* question type
* mastery band

## Inputs

Input is a scraped course YAML-like object with fields such as:

* `title`
* `summary`
* `overview`
* `syllabus`

`syllabus` is preferred when available. If missing or sparse, infer chapter structure from `overview`.

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
  "score": 0.0
}
```

## Non-Goals

Do not implement:

* canonical answers
* paraphrase/variation generation
* cache storage
* runtime semantic matching
* personalized learner prediction
* session-aware adaptation

Those are separate downstream concerns.

## High-Level Algorithm

### 1. Parse course

Extract:

* title
* summary
* overview
* syllabus

If `syllabus` is missing or empty:

* infer chapter blocks from overview text.

### 2. Build chapter records

For each chapter, create:

* `chapter_id`
* `chapter_title`
* `chapter_summary`
* `chapter_order`

### 3. Extract learning units per chapter

For each chapter, extract:

* concepts
* procedures
* tools
* metrics/tests
* contrasts
* prerequisites
* confusions

Examples:

* concept: exponential smoothing
* procedure: visualize a time series
* metric/test: forecast accuracy, Ljung-Box test
* contrast: ARIMA vs exponential smoothing
* confusion: benchmark vs benchmark method

### 4. Normalize topics

Merge near-duplicate topics across chapters only when they represent the same intent.

Keep:

* canonical `topic_id`
* canonical label
* aliases

Do not merge topics that differ pedagogically even if they are textually similar.

### 5. Create question opportunities

For each topic, generate question slots based on topic type:

* **concept**

  * definition
  * purpose
  * intuition

* **procedure**

  * how_to
  * when_to_use
  * common_error

* **metric/test**

  * what_is
  * why_it_matters
  * interpretation

* **contrast pair**

  * comparison
  * when_to_choose_A_vs_B

* **confusion pair**

  * misconception
  * disambiguation

* **advanced topic**

  * application
  * limitation

### 6. Expand by mastery band

For each question slot, generate versions for:

* novice
* developing
* proficient

Examples:

* novice: “What is exponential smoothing?”
* developing: “Why do recent observations get more weight in exponential smoothing?”
* proficient: “When is exponential smoothing preferable to ARIMA?”

### 7. Generate candidate questions

For each `(chapter, topic, question_type, mastery_band)` tuple, generate one or more candidate learner questions.

Hard constraints:

* question must be answerable from course evidence
* question must sound like something a learner would naturally ask
* question must be pedagogically useful
* question must not be pure metadata/navigation unless explicitly allowed

### 8. Score questions

Score each question using a weighted combination of:

* `grounding_score` — supported by source text
* `learner_likelihood` — plausibly asked by a learner
* `pedagogical_value` — helps learning, not just catalog browsing
* `distinctiveness` — not a duplicate
* `answerability` — can be answered from the course

### 9. Filter

Drop questions that are:

* below score threshold
* duplicates
* metadata-only
* weakly grounded
* same intent as a better-scoring question

### 10. Canonicalize

Cluster semantically similar candidate questions and keep one canonical question per intent.

Optional:

* attach aliases/paraphrases later, but do not implement that in this task.

### 11. Return final set

Sort by:

1. chapter order
2. topic importance
3. mastery band
4. score descending

## Key Design Rule

The core generation unit is:

`(chapter, topic, question_type, mastery_band)`

Do **not** generate directly from:

`(learning claim -> paraphrases)`

That approach tends to produce shallow or catalog-like questions.

## Implementation Guidance

Use a two-stage design:

### Stage A: deterministic structure extraction

* parse YAML
* build chapter records
* collect raw text evidence

### Stage B: semantic extraction + generation

* extract learning units
* normalize topics
* generate candidate questions
* score and filter

Keep deterministic parsing separate from LLM-based semantic extraction.

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
    score: float
```

## Acceptance Criteria

A good implementation should:

* produce grounded questions from real course content
* generate more than definition questions
* include why/how/compare/misconception-style questions
* preserve chapter context
* avoid duplicates
* avoid metadata-only questions dominating output
* work even when syllabus is missing and must be inferred from overview

## Minimal MVP

If time is tight, implement this subset first:

1. parse chapters
2. extract topics + contrasts + confusions
3. generate question types:

   * definition
   * purpose
   * how_to
   * comparison
   * misconception
4. score
5. dedupe
6. return ranked list

## Deliverable

Produce:

1. implementation code
2. clear module boundaries
3. example run on one course YAML
4. sample output JSON
5. brief notes on where LLM calls are used vs deterministic logic

Use this brief as the source of truth for the implementation.

