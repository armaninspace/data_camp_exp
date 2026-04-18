# Question Generation V4.1 — Policy Addendum

This addendum modifies the V4 policy layer with a stricter persistence and coverage model.

## Why this exists

The prior design still allowed the following failure mode:
- a correct, grounded question was generated
- later curation, ranking, deduplication, or balancing removed it
- the system no longer exposed any evidence that the question ever existed

That is unacceptable for beginner entry questions and undesirable for all validated-correct questions.

## Policy shift

### Old mental model
`generate -> curate -> keep`

### New mental model
`generate -> validate -> persist -> classify -> surface`

Existence and visibility are now separate decisions.

## New invariants

### 1. Validated-correct candidates are durable
Any candidate passing both:
- correctness threshold
- groundedness threshold

must be persisted to the question ledger.

### 2. Curation is routing, not deletion
Every persisted validated-correct candidate must be assigned one of:
- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`

Only invalid candidates may enter:
- `hard_reject`

### 3. Missing beginner anchors are warnings
If a foundational concept does not have a visible canonical entry question, emit a coverage warning with:
- concept id
- canonical concept label
- whether hidden correct variants exist
- reason visible coverage failed

## Required concept class

### `foundational_vocabulary_anchor`
A concept that is:
- central to understanding the content
- likely unfamiliar to a beginner
- reused later
- named as a core noun phrase, method, metric, signal, or phenomenon

These concepts must receive required entry-question treatment.

## Required question treatment for anchors

For each foundational anchor, generate at least one canonical entry question:
- `What is X?`

Optionally also generate:
- `Why does X matter?`
- `How do I recognize X?`
- `How is X different from Y?`

But only `What is X?` is mandatory.

## Candidate lifecycle policy

### Stage 1 — generation
Generate candidates from:
- anchor pass
- normal template pass
- alias/variant pass

### Stage 2 — validation
Assess:
- correctness
- groundedness
- coherence

### Stage 3 — persistence
If validated-correct, write candidate to durable storage before any later stage.

### Stage 4 — canonicalization
Group semantically equivalent candidates and assign:
- canonical id
- alias relations
- duplicate relations

### Stage 5 — classification
Assign one of:
- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

### Stage 6 — coverage audit
Check whether each foundational anchor has visible canonical entry coverage.

## Non-visible reason policy

Any validated-correct candidate that is not visible must store one or more machine-readable reasons, for example:
- `quota_displacement`
- `canonicalized_under_other_question`
- `kept_for_cache_not_visible`
- `alias_of_canonical`
- `analysis_only_low_distinctiveness`
- `analysis_only_low_serviceability`

## Practical intent

V4.1 makes sure the system can answer all three questions separately:
1. Did we generate a correct question?
2. Did we keep it in the ledger?
3. Did we choose to show it?

Those three answers must never be conflated again.
