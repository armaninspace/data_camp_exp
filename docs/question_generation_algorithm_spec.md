# Question Generation Algorithm Spec

## Scope

This document specifies the current question-generation algorithm as it exists
across the live pipeline stages:

- candidate generation
- policy and coverage classification
- ledger normalization

It describes the actual algorithmic flow that the project should optimize and
audit.

## Goal

Generate learner-question artifacts from course descriptions in a way that is:

- grounded in source text
- inspectable end to end
- non-destructive
- coverage-aware
- biased toward realistic beginner questions for foundational concepts

Implementation note:

The live question pipeline now runs through the stable package surface under
`course_pipeline.questions.*`. The remaining historical implementation label in
the source tree is `question_ledger_v6`, which is treated as a compatibility
name for the ledger stage rather than an architectural stage name.

## High-Level Pipeline

```text
raw course YAML
-> normalized course
-> topic extraction
-> edge extraction
-> pedagogy extraction
-> friction mining
-> candidate generation
-> candidate filtering
-> candidate scoring
-> dedupe
-> policy classification
-> foundational-entry coverage enforcement
-> ledger normalization
-> per-run LLM metering for live review-answer stages
-> derived views and inspection bundle
```

## Metering

Live LLM-backed review-answer stages persist per-run metering as:

- `llm_metering.jsonl`

Each record includes run identity, stage, scoped entity ids, model metadata,
latency, token counts, retry count, cache status, and estimated cost.

Current implementation path:

- [llm_metering.py](/code/src/course_pipeline/llm_metering.py)

## Terminology

### Topic

A topic is a normalized concept, procedure, metric, tool, diagnostic, or other
course element extracted from the course summary, overview, and syllabus.

### Foundational Anchor

A foundational anchor is a topic important enough to warrant explicit beginner
entry coverage.

Examples:

- ARIMA models
- exponential smoothing
- forecast accuracy
- trend
- seasonality
- white noise
- Ljung-Box test

### Candidate Question

A candidate question is a generated learner-question hypothesis prior to policy
classification.

### Required Entry Question

A required entry question is the canonical plain beginner definition question
for a foundational anchor.

Examples:

- `What is ARIMA?`
- `What is seasonality?`

### Delivery Class

Each validated question ends in one delivery class:

- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

### Ledger Row

A ledger row is the normalized V6 representation of one generated question and
its terminal state.

## Stage 1: Course Normalization

Input:

- raw YAML

Output:

- `NormalizedCourse`

Relevant fields:

- `course_id`
- `title`
- `summary`
- `overview`
- `chapters`

Purpose:

- create stable structured input for downstream extraction

## Stage 2: Topic Extraction

The V3 generator extracts topics from:

- chapter titles
- chapter summaries
- course overview

Topic extraction uses:

- phrase patterns
- section title splitting
- heuristic topic typing
- confidence assignment

Representative topic types:

- `concept`
- `procedure`
- `tool`
- `metric`
- `diagnostic`
- `comparison_axis`
- `decision_point`

Important property:

Topic extraction is heuristic and bounded. It is not a full ontology pass.

## Stage 3: Edge Extraction

Edges represent coarse semantic relationships between topics.

Representative relations:

- `contrasts_with`
- `confused_with`
- `evaluated_by`
- `uses`
- `decision_depends_on`

Purpose:

- create question opportunities for comparison, confusion, and method-choice
  prompts

## Stage 4: Pedagogy Extraction

Each topic gets a pedagogical profile that estimates:

- abstraction level
- notation load
- procedure load
- likely misconceptions
- likely sticking points
- evidence of mastery

Purpose:

- guide later candidate generation
- support misconception and diagnostic prompts

## Stage 5: Friction Mining

Friction points are derived from topics, edges, and pedagogy.

Representative friction types:

- `confusion`
- `choice`
- `failure_mode`
- `prerequisite_gap`
- `transfer_gap`
- `interpretation_gap`

Purpose:

- identify where a learner is likely to ask for clarification, comparison, or
  decision help

## Stage 6: Candidate Generation

Candidate generation is performed per topic.

The generator emits questions across a bounded template set:

- orientation
- definition
- procedure
- comparison
- misconception
- diagnostic
- transfer

### Custom Topic Rules

Some topic families have custom generation rules.

Examples:

- benchmark methods
- forecast accuracy
- exponential smoothing
- ARIMA
- white noise
- Ljung-Box test
- univariate / multivariate time series

### Foundational Plain Definition Rule

For foundational anchors, the generator must emit one canonical plain beginner
definition question.

Rule:

- use `What is X?`
- use `What are X?` only when the noun phrase is genuinely plural

Examples:

- `What is ARIMA?`
- `What is exponential smoothing?`
- `What is the Ljung-Box test?`
- `What is trend?`
- `What is seasonality?`
- `What are repeated cycles?`

### Acronym Rule

For acronym anchors:

- the canonical plain question is `What is X?`
- the acronym-expansion form may also be generated

Example:

- canonical: `What is ARIMA?`
- secondary companion: `What does ARIMA stand for?`

The companion must not replace the plain definition.

### Foundational Entry Helper

The repo now centralizes plain-definition wording in:

- [foundational_entry_questions.py](/code/src/course_pipeline/foundational_entry_questions.py)

This helper is responsible for:

- anchor label simplification
- acronym handling
- singular vs plural wording
- article normalization for cases like `the Ljung-Box test`

## Stage 7: Candidate Filtering

The V3 filter removes weak candidates before scoring.

Representative rejection reasons:

- `unsupported`
- `broad_heading_paraphrase`
- `thin_answer`
- `mastery_misaligned`
- `malformed`
- `duplicate_intent`

### Important Current Rule

Plain foundational definitions are protected from earlier over-pruning.

Notable corrections:

- short beginner definitions like `What is ARIMA?` are no longer rejected as
  malformed
- plain definitions for comparison-axis anchors are no longer rejected as
  `thin_answer` by default

## Stage 8: Candidate Scoring

Kept candidates are scored on several dimensions.

Representative V3 score inputs:

- friction value
- specificity
- answer richness
- mastery fit
- novelty
- groundedness

Representative policy score fields:

- correctness
- groundedness
- query likelihood
- pedagogical value
- distinctiveness
- serviceability
- answer stability
- context dependence

Purpose:

- support policy classification
- support visibility selection
- preserve inspection of why one question outranks another

## Stage 9: Dedupe and Canonicalization

The generator dedupes candidates and assigns canonical groupings.

Current canonicalization is similarity-based and still conservative.

Known limitation:

- alias clustering is underpowered
- some semantically related forms remain separate canonical questions

## Stage 10: Foundational Anchor Detection

The policy-and-coverage stage identifies foundational anchors from topics
using:

- topic type
- confidence
- generic-label filtering
- label normalization

Recent correction:

- duplicate labels such as `ARIMA` and `ARIMA models` are normalized toward one
  anchor concept for coverage purposes
- generic headings such as `Advanced methods` are excluded from foundational
  anchor enforcement

## Stage 11: Policy Classification

Validated candidates are classified into delivery buckets.

Main buckets:

- `curated_core` -> mapped to `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

Inputs to policy:

- policy scores
- serveability result
- family tags
- canonicalization result

### Question Families

Family tagging groups questions into:

- `entry`
- `bridge`
- `procedural`
- `friction`
- `diagnostic`
- `transfer`

Purpose:

- balance the visible set
- distinguish beginner entry prompts from richer pedagogical prompts

## Stage 12: Protected Entry Promotion

This is a critical current rule.

If a question is the canonical plain definition for a foundational anchor, then:

- it is marked `required_entry=true`
- it cannot be left hidden purely because of low distinctiveness
- it is promoted to `curated_visible` if otherwise validated

This rule exists specifically to prevent failures like:

- `What is ARIMA?` being absent while richer comparison questions are visible

### Consequence

Richer questions are still allowed and useful, but only after the visible
beginner-definition slot has been satisfied.

## Stage 13: Coverage Audit

Coverage is audited per foundational anchor.

Possible warning types:

- `missing_visible_canonical_entry`
- `only_hidden_correct_entry_exists`
- `only_alias_entry_exists`
- `definition_generation_failed`

### Strict Mode

In strict mode, the run fails if a foundational anchor lacks a visible
canonical plain definition.

This blocks inspection bundles that would otherwise hide a structural failure.

## Stage 14: Ledger Normalization

The ledger stage converts terminal policy records into one authoritative ledger
row per question.

Each row includes:

- stable question id
- question text
- anchor metadata
- family and type
- mastery band
- canonical vs alias state
- required-entry flag
- delivery class
- visibility
- hidden reasons
- reject reasons
- score summary
- source refs
- tracked topics

The ledger is persisted as:

- `all_questions.jsonl`

## Stage 15: Derived Views

From the ledger, the system derives:

- visible curated questions
- cache-servable questions
- aliases
- anchor summaries
- inspection report

Important invariant:

Derived views are not the source of truth.

The ledger is the source of truth.

## Stage 16: Inspection Bundle Rendering

Inspection bundles should show:

- all questions with attributes
- course content
- inspection report
- visibility status
- anchor coverage state

This makes it possible to answer:

- was the question generated?
- was it validated?
- was it visible?
- if hidden, why?
- if missing, where did it fail?

## Current Hard Requirements

The current algorithm should satisfy these requirements.

### Requirement 1: Plain Foundational Definitions

Every foundational anchor must have a plain canonical beginner definition
question.

### Requirement 2: Acronym Preference

For acronym anchors, prefer `What is X?` over `What does X stand for?`

### Requirement 3: No Low-Distinctiveness Hiding

No `required_entry=true` question may be hidden solely because of
`low_distinctiveness`.

### Requirement 4: Strict Failure On Missing Visible Entry

If a foundational anchor lacks a visible canonical plain definition, strict
mode fails the run.

### Requirement 5: Ledger Preservation

Every terminal question state must be represented in the ledger.

## Pseudocode

```text
for each normalized course:
    topics = extract_topics(course)
    edges = extract_edges(course, topics)
    pedagogy = extract_pedagogy(course, topics, edges)
    frictions = mine_friction(topics, edges, pedagogy)

    raw_candidates = []
    for each topic:
        raw_candidates += generate_topic_candidates(topic)
        if topic is foundational:
            raw_candidates += canonical_plain_definition(topic)
            if topic is acronym:
                raw_candidates += acronym_companion_definition(topic)

    kept, rejected = filter_candidates(raw_candidates)
    scored = score_candidates(kept)
    deduped = canonicalize(scored)

    anchors = detect_foundational_anchors(topics)
    policy_decisions = assign_policy_buckets(deduped)
    policy_decisions = promote_protected_required_entries(policy_decisions, anchors)

    validated_records = build_candidate_records(policy_decisions)
    coverage = audit_anchor_coverage(anchors, validated_records)

    if strict_mode and coverage has blocking warning:
        fail run

    ledger_rows = build_ledger_rows(validated_records, rejected)
    derived_views = derive_views(ledger_rows)
    inspection = build_inspection_bundle(ledger_rows, derived_views, course)
```

## Known Weaknesses

The algorithm is materially improved, but still incomplete.

Current weak points:

- some procedural and transfer prompts remain unnatural
- alias grouping is still sparse
- serviceability thresholds may still be too conservative
- foundational anchor detection remains heuristic
- some duplicate topic extraction still leaks through before later cleanup

## Recommended Improvement Directions

1. strengthen alias clustering with intent-aware normalization
2. normalize awkward procedural wording earlier
3. split generic heading topics more aggressively from real concept anchors
4. improve cache-servable criteria after ledger quality stabilizes
5. add more regression fixtures around beginner vocabulary coverage

## Canonical References

- [project_spec.md](/code/docs/project_spec.md)
- [question_generation_algorithm_spec.md](/code/docs/question_generation_algorithm_spec.md)
- [question_ledger_v6_codex_bundle/question_ledger_v6_spec.md](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_spec.md)
- [inspection_bundle_7](/code/docs/inspection_bundle_7)
