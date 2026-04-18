# Question Generation Algorithm V3

## Purpose

Question Generation V3 changes the system objective from **"generate questions that are grounded in source text"** to **"select the most instructionally useful, source-grounded learner questions"**.

V3 is designed to reduce four recurring failure modes observed in generation-first pipelines:

1. overproduction of generic definition and broad how-to questions
2. underproduction of misconception, diagnostic, and proficient-level questions
3. emission of questions whose answers are technically grounded but thin, vague, or not worth asking
4. weak coverage of likely learner friction, including confusion, method choice, failure modes, and transfer

## Core design shift

Move from:

```text
source text -> generate questions
```

To:

```text
source text
-> parse and normalize
-> extract topic graph and pedagogical signals
-> infer learner friction
-> generate candidates by taxonomy slot
-> filter low-value candidates
-> score and rank
-> select balanced final set
```

## High-level principles

1. **Friction-first**: prioritize questions tied to confusion, choices, tradeoffs, failure modes, and transfer.
2. **Ranker-driven**: treat generation as candidate production, not final selection.
3. **Balanced output**: enforce quotas so the final set cannot collapse into safe but bland question types.
4. **Answerability-aware**: reject questions whose likely answer is thin, tautological, or mostly "not specified".
5. **Subtopic-sensitive**: generate from fine-grained learning units, not just chapter-level themes.
6. **Generalizable**: use generic pedagogical reasoning; do not rely on course-specific hardcoding.

---

## Pipeline

### Stage 0: Parse and normalize

Input: normalized course-like source object containing any available combination of:
- title
- summary
- overview
- syllabus or sections
- metadata such as level, duration, subjects, tool/language

Output:

```python
CanonicalDocument = {
  "doc_id": str,
  "title": str,
  "summary": str,
  "overview": str,
  "level": str | None,
  "tooling": list[str],
  "subjects": list[str],
  "sections": list[Section],
}

Section = {
  "section_index": int,
  "title": str,
  "summary": str,
  "source": "explicit" | "inferred",
}
```

Rules:
- Preserve original ordering.
- If explicit sections are missing, infer pseudo-sections from headings, bullets, or topic transitions.
- Mark inferred structure with lower confidence.

### Stage 1: Fine-grained topic extraction

Run extraction at the **section level**, not only at the whole-document level.

For each section, extract topic units with these allowed types:
- `concept`
- `procedure`
- `tool`
- `metric`
- `diagnostic`
- `comparison_axis`
- `failure_mode`
- `decision_point`
- `prerequisite`

Output:

```python
TopicNode = {
  "topic_id": str,
  "label": str,
  "aliases": list[str],
  "topic_type": str,
  "description": str,
  "source_section_ids": list[int],
  "confidence": float,
}
```

Extraction rules:
- Prefer concrete teachable units over broad chapter labels.
- Split broad themes into subtopics when they imply distinct learner questions.
- Extract explicit and inferred topics.
- Do not extract placeholder topics such as "introduction" or "overview" unless pedagogically meaningful.

### Stage 2: Relationship extraction

Build a local topic graph.

Allowed edge types:
- `prerequisite_of`
- `part_of`
- `contrasts_with`
- `confused_with`
- `evaluated_by`
- `uses`
- `decision_depends_on`
- `failure_revealed_by`

Output:

```python
TopicEdge = {
  "source_id": str,
  "target_id": str,
  "relation": str,
  "rationale": str,
  "confidence": float,
}
```

### Stage 3: Pedagogical signal extraction

For each topic, infer pedagogical properties.

```python
PedagogicalProfile = {
  "topic_id": str,
  "cognitive_modes": list[str],  # conceptual, procedural, comparative, diagnostic, interpretive, transfer
  "abstraction_level": "low" | "medium" | "high",
  "notation_load": "low" | "medium" | "high",
  "procedure_load": "low" | "medium" | "high",
  "likely_misconceptions": list[str],
  "likely_sticking_points": list[str],
  "evidence_of_mastery": list[str],
}
```

This stage exists to support question ranking and mastery assignment.

### Stage 4: Friction mining

This is the key new stage in V3.

For each topic, derive one or more learner-friction records.

```python
FrictionPoint = {
  "friction_id": str,
  "topic_id": str,
  "friction_type": str,  # confusion, choice, failure_mode, prerequisite_gap, transfer_gap, interpretation_gap
  "prompting_signal": str,
  "learner_symptom": str,
  "why_it_matters": str,
  "severity": float,
  "confidence": float,
}
```

Friction inference heuristics:
- create friction points for explicit compare/contrast content
- create friction points when multiple methods, tools, or paths are available
- create friction points for evaluation criteria and diagnostics
- create friction points for topics that rely on unstated prior knowledge
- create friction points for broad-to-specific transitions
- create friction points for any topic containing likely failure modes or tradeoffs

Do **not** require explicit phrases like "common mistake" in the source.

### Stage 5: Candidate generation by slot

Generate a large candidate pool, but in a controlled way.

Each topic should attempt generation into these slots:
- `novice_orientation`
- `novice_definition`
- `developing_procedural`
- `developing_comparison`
- `developing_misconception`
- `proficient_diagnostic`
- `proficient_transfer`

Output:

```python
QuestionCandidate = {
  "candidate_id": str,
  "topic_id": str,
  "slot": str,
  "mastery_band": "novice" | "developing" | "proficient",
  "question_type": str,
  "question_text": str,
  "rationale": str,
  "source_support": list[str],
}
```

Generation rules:
- generate more candidates than needed; final selection happens later
- each candidate must be tied to at least one topic and zero or more friction points
- procedural questions should reference an actual operation or choice
- proficient questions must require diagnosis, transfer, or comparison, not mere recall

### Stage 6: Low-value filtering

Before scoring, reject candidates that match any of the following:

#### 6.1 Low answerability
Reject if the likely answer is primarily:
- tautological
- restating the question using the same wording
- vague summary without discriminative detail
- mostly "not specified"
- mostly "the material mentions this generally"

#### 6.2 Low instructional value
Reject if the candidate is:
- a broad paraphrase of a section heading
- too generic to reveal understanding
- a meta-course question with little learner utility
- a weaker duplicate of a more specific candidate

#### 6.3 Structural issues
Reject if:
- unsupported by source
- malformed
- semantically near-duplicate of an existing candidate
- mastery band and question complexity are misaligned

### Stage 7: Candidate scoring

All surviving candidates receive normalized scores on these dimensions:

```python
CandidateScore = {
  "friction_value": float,
  "specificity": float,
  "answer_richness": float,
  "mastery_fit": float,
  "novelty": float,
  "groundedness": float,
  "total": float,
}
```

Recommended weighted sum:

```text
total =
  0.30 * friction_value +
  0.20 * specificity +
  0.15 * answer_richness +
  0.15 * mastery_fit +
  0.10 * novelty +
  0.10 * groundedness
```

Definitions:
- **friction_value**: whether the question targets confusion, decision-making, failure, tradeoff, interpretation, or transfer
- **specificity**: whether it refers to a real subtopic rather than a broad theme
- **answer_richness**: whether the source can support a meaningful answer with distinguishing detail
- **mastery_fit**: whether the complexity matches the intended mastery band
- **novelty**: whether it is meaningfully different from already retained candidates
- **groundedness**: whether it is well-supported by the source text and extracted structure

### Stage 8: Balanced selection

Final selection should maximize score subject to policy constraints.

Recommended default selection policy:
- at least 25% friction-driven questions
- at least 20% comparison, diagnostic, or transfer questions
- at least 15% proficient questions
- no more than 30% plain definitions
- no more than 2 semantically near-duplicate candidates per topic family
- every selected question must have groundedness above threshold

This stage can be implemented as greedy constrained selection or integer optimization.

---

## Question taxonomy

Use this normalized set:
- `orientation`
- `definition`
- `procedure`
- `comparison`
- `misconception`
- `diagnostic`
- `interpretation`
- `transfer`
- `purpose`
- `when_to_use`

Mapping notes:
- `how_to` should map to `procedure`
- `proficient` questions should mostly come from `diagnostic`, `transfer`, `comparison`, or `interpretation`
- `misconception` requires a real plausible confusion, not merely a negative framing

## Mastery band rules

### Novice
Appropriate signals:
- naming
- orientation
- straightforward concept distinction
- single-step procedure recognition

Inappropriate signals:
- multi-constraint diagnosis
- open transfer without scaffolding
- evaluation of competing methods with implicit assumptions

### Developing
Appropriate signals:
- applying procedure to a case
- comparing two methods or concepts
- interpreting output or choosing a next step
- identifying a plausible error or misconception

### Proficient
Appropriate signals:
- diagnosing why an approach failed
- selecting among alternatives using tradeoffs
- transferring knowledge to a new context
- evaluating adequacy using evidence or diagnostics

Inappropriate signals:
- pure vocabulary recall
- generic "what is" prompts

---

## Scoring heuristics

### Friction value
Increase when candidate:
- resolves a confusion pair
- requires method or tool selection
- targets a common failure mode
- probes interpretation rather than recall
- requires transfer from one context to another

### Specificity
Increase when candidate:
- names a real subtopic
- references a concrete operation, metric, or decision
- could be answered differently from neighboring subtopics

Decrease when candidate:
- paraphrases a broad heading
- could apply equally to almost any section

### Answer richness
Increase when the answer can include:
- distinctions
- examples
- contrasts
- diagnostics
- implications of failure or choice

Decrease when the answer is likely to be:
- one sentence of repetition
- "it depends" without discriminative structure
- unsupported by the source

---

## Deduplication

Deduplicate on semantic intent, not just string similarity.

Two candidates are duplicates if they ask materially the same learner question despite different wording.

Preferred retention policy:
1. keep higher total score
2. if tie, keep more specific candidate
3. if still tied, keep the candidate from the more valuable taxonomy slot

---

## Default thresholds

Recommended initial values:

```yaml
min_topic_confidence: 0.60
min_edge_confidence: 0.55
min_friction_confidence: 0.55
min_groundedness_for_selection: 0.70
min_total_score_for_selection: 0.62
semantic_duplicate_threshold: 0.88
max_definition_share: 0.30
min_friction_share: 0.25
min_advanced_share: 0.20
min_proficient_share: 0.15
```

These should be configurable rather than hardcoded.

---

## Failure modes addressed by V3

V3 is explicitly designed to reduce:
- generic question inflation
- broad heading paraphrase questions
- low-value thin-answer questions
- missing friction detection
- weak proficient representation
- overreliance on direct generation

## Non-goals

V3 does **not** attempt to:
- generate final answers for learners
- estimate learner state from user interaction history
- personalize by user profile
- replace human evaluation of question usefulness

Those can be separate systems.

---

## Evaluation

### Required metrics

Track at least:
- `candidate_count`
- `selected_count`
- `question_type_distribution`
- `mastery_band_distribution`
- `friction_point_count`
- `friction_linked_selection_rate`
- `low_value_rejection_rate`
- `semantic_duplicate_rejection_rate`
- `groundedness_pass_rate`
- `proficient_share`

### Human review rubric

Each selected question should be scored by a reviewer on 1-5 scales for:
- instructional value
- specificity
- answer richness
- mastery fit
- non-duplication
- groundedness

### Success criteria

V3 is considered better than V2 if it achieves most of the following:
- lower share of plain definition questions
- higher share of comparison, diagnostic, misconception, and transfer questions
- higher proficient share
- lower low-value/meta-question rate
- higher average reviewer usefulness score

---

## Implementation notes

- Keep extraction, scoring, and selection as separable steps.
- Prefer structured outputs via Pydantic or JSON schema.
- Store intermediate artifacts for debugging.
- Make weights and quotas configurable.
- Log rejection reasons for every filtered candidate.
- Preserve provenance from candidate to topic, section, and source span.

---

## Summary

V3 should be understood as **Friction-First Ranked Selection**.

Generation remains important, but it is no longer the core decision-maker. The system should win by building better structure, surfacing real learner friction, filtering weak candidates aggressively, and selecting a balanced high-value set.
