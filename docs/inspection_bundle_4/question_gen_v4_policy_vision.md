# Question Generation V4 — Policy Vision

## Purpose

V4 defines the **policy layer** for question generation, retention, curation, and serving.

It does **not** replace the V3 pipeline. Instead, it governs what happens **after candidates are extracted, generated, filtered, scored, and canonicalized**.

The central shift in V4 is:

> A question candidate is not a binary good/bad object. It is a multi-use asset that may be appropriate for pedagogy, direct serving, alias mapping, analysis, or rejection.

## North star

V4 should optimize for:

**grounded, likely, teachable, and reusable learner questions**

This requires separate decisions for:
- instructional curation
- cache serving
- alias / retrieval mapping
- offline analysis
- hard rejection

## Core principles

### 1) Simple questions are first-class
Short beginner questions are not low quality just because they are basic.

Examples of acceptable entry-question forms:
- What is X?
- How does X work?
- Why do we use X?
- What is the difference between X and Y?

V4 explicitly preserves these as **entry questions**.

### 2) Friction questions are first-class
V4 must also preserve deeper learner questions tied to:
- confusion
- tradeoffs
- failure modes
- choice points
- diagnostics
- transfer

These are **friction questions**.

### 3) The system must balance both lanes
The final visible set must include both:
- entry questions
- friction / diagnostic questions

The policy should prevent collapse into either:
- all safe beginner definitions, or
- all advanced reasoning questions

### 4) Not selected does not mean bad
A candidate may fail to enter the curated instructional set and still be:
- correct
- grounded
- useful for direct Q/A serving
- useful as a retrieval alias
- useful for analysis and threshold tuning

V4 separates those cases.

### 5) Correctness alone is not enough for serving
A candidate must be:
- correct
- grounded
- clear
- serviceable
- not misleadingly partial

before it can be used in a Q/A cache.

### 6) Canonicalize intent
If two candidates express the same learner intent, prefer:
- one canonical question-answer pair
- multiple aliases / paraphrase variants pointing to it

This improves both pedagogy and serving.

---

## Candidate dimensions

V4 decisions must rely on **multiple dimensions**, not one overall score alone.

### Validity dimensions
- `correctness`
- `groundedness`
- `contradiction_risk`
- `coherence`

### Learner-value dimensions
- `query_likelihood`
- `pedagogical_value`
- `answer_richness`
- `mastery_fit`

### Set-quality dimensions
- `distinctiveness`
- `redundancy`
- `canonicality`
- `coverage_contribution`

### Serving dimensions
- `serviceability`
- `clarity`
- `context_dependence`
- `answer_stability`

---

## V4 policy buckets

Every candidate should be placed into exactly one of these policy classes.

### 1) `curated_core`
Best instructional questions. These go into the visible final curated set.

Use when the candidate is:
- valid
- grounded
- pedagogically strong
- distinct
- useful for set balance

### 2) `cache_servable`
Not selected for the curated set, but safe and useful for direct serving.

Use when the candidate is:
- valid
- grounded
- clear
- likely to be asked
- directly answerable
- not superseded by a stronger canonical item

### 3) `alias_only`
Likely user phrasing that should map to a canonical question-answer pair rather than exist as a separate served item.

Use when the candidate is:
- semantically equivalent to a canonical item
- useful for retrieval or intent matching
- too duplicative to surface independently

### 4) `analysis_only`
Retained for threshold tuning, reviewer labeling, debugging, and ranker improvement, but never served directly.

Use when the candidate is:
- interesting but weak
- too vague
- too duplicative
- too narrow for direct use
- low pedagogical value
- borderline in a non-fatal quality dimension

### 5) `hard_reject`
Do not reuse.

Use when the candidate is:
- unsupported
- contradictory
- malformed
- unsafe
- clearly hallucinated

---

## Question families

V4 explicitly recognizes question families.

### Entry family
- What is X?
- How does X work?
- Why do we use X?

### Bridge family
- Is X the same as Y?
- How is X different from Y?
- When would I use X instead of Y?

### Procedural family
- How do I do X?
- What steps do I follow?
- How do I know whether I did X correctly?

### Friction family
- What usually goes wrong with X?
- Why does X fail here?
- What misconception does this reveal?

### Diagnostic family
- What does this signal tell me?
- How do I know whether the method is appropriate?
- What evidence would change my choice?

### Transfer family
- How would I apply this in a new situation?
- When does this break down?
- What changes when the context shifts?

The curated set should span multiple families.

---

## Canonicalization policy

### Canonical item
A canonical item is the preferred pedagogical or serviceable representation of a learner intent.

### Alias item
An alias item is a shorter, colloquial, underspecified, or stylistically different expression of the same intent.

### Canonicalization rules
- One intent should usually map to one canonical served answer.
- Multiple aliases may map to the same canonical item.
- Near-duplicate canonical items should be merged when they do not contribute distinct coverage.
- An alias may be very high query-likelihood without deserving independent curation.

---

## Decision policy

V4 is a staged decision process.

### Stage 1: validity gate
Decide whether the candidate is valid enough to keep at all.

Pass requirements:
- sufficiently correct
- sufficiently grounded
- coherent
- not contradictory

Failure outcome:
- `hard_reject`

### Stage 2: family tagging
Assign one or more family tags:
- entry
- bridge
- procedural
- friction
- diagnostic
- transfer

### Stage 3: canonicalization
Resolve whether the candidate is:
- canonical
- alias
- duplicate

### Stage 4: serviceability decision
Decide whether the candidate is safe and useful for direct Q/A serving.

Pass requirements:
- clear enough to answer directly
- not overly context dependent
- answer is stable and not misleadingly partial

### Stage 5: curation decision
Decide whether the candidate belongs in the curated instructional set.

Pass requirements:
- pedagogically strong
- distinct
- helpful for family / mastery balance
- not superseded by another selected item

### Stage 6: retention assignment
Assign exactly one bucket:
- `curated_core`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

---

## Curation policy

The curated set should satisfy these broad rules:
- include entry questions for major concepts
- include friction and diagnostic questions
- include some compare/contrast coverage
- include some procedural coverage
- include some advanced or transfer coverage when supported
- cap plain definitions so they do not dominate
- suppress near-duplicate beginner variants when one canonical form is enough

The objective is:

**coverage of concept entry points + coverage of real learner friction**

---

## Cache-serving policy

The Q/A cache may draw from:
- `curated_core`
- `cache_servable`

The Q/A cache should not directly serve from:
- `analysis_only`
- `hard_reject`

Aliases should usually route to a canonical cache item rather than being served as standalone entries.

### Cache-serving gate
A candidate may be served from cache only if it is:
- correct
- grounded
- clear
- serviceable
- stable
- not superseded by a better canonical item

---

## Retention policy

### Store full records for:
- `curated_core`
- `cache_servable`
- `alias_only`
- `analysis_only`

### Store minimal audit metadata for:
- `hard_reject`

This enables:
- threshold tuning
- reviewer workflows
- ranker training
- alias expansion
- debugging over-filtering
- drift analysis

---

## Suggested candidate record

```json
{
  "candidate_id": "q_123",
  "question": "What is X?",
  "answer": "...",
  "family_tags": ["entry"],
  "canonical_id": "concept_x_q1",
  "policy_bucket": "cache_servable",
  "scores": {
    "correctness": 0.96,
    "groundedness": 0.94,
    "query_likelihood": 0.91,
    "pedagogical_value": 0.58,
    "answer_richness": 0.72,
    "mastery_fit": 0.89,
    "distinctiveness": 0.80,
    "serviceability": 0.95
  },
  "flags": ["entry_level", "canonical"],
  "reject_reasons": [],
  "source_refs": ["..."],
  "model_version": "v4"
}
```

---

## Telemetry and governance

Track at minimum:
- share of entry questions
- share of friction questions
- share of canonical vs alias items
- duplicate-intent rate
- cache-servable rate
- analysis-only rate
- hard-reject rate
- served-answer satisfaction
- cache-hit usefulness
- family coverage
- mastery-band coverage

V4 should be treated as an observable policy system, not just a prompt.

---

## One-paragraph policy summary

V4 should explicitly preserve simple beginner entry questions, actively mine friction and diagnostic questions, separate pedagogical curation from cache-serving decisions, canonicalize duplicate intents, retain useful non-selected candidates in quarantined buckets, and enforce correctness, groundedness, and serviceability gates before anything is allowed into direct user-facing serving.
