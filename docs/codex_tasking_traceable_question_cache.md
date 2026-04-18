# Codex Tasking: Build the Traceable Course → Claim → Question Cache Layer

## Objective

Extend the existing extraction pipeline with a new layer that produces a **traceable learner-intent response cache**.

The new layer must preserve lineage from:

`course -> claim -> question_group -> variation -> canonical_answer`

This is **not** the full adaptive tutor runtime. It is the **fast path** for common learner questions:
- low latency
- consistent responses
- strong traceability
- LLM fallback only on misses, low-confidence matches, or follow-ups

The goal is to improve learner trust by returning high-confidence answers quickly for common, repeated intents.

---

## Why this layer exists

The current pipeline already performs:
- deterministic YAML parsing and normalization
- chapter recovery
- structured LLM extraction for topics, edges, pedagogy, and likely student questions
- persistence of extracted artifacts in Postgres and JSONL exports

The current status notes explicitly show persistence for normalized courses, chapters, pedagogical profiles, and predicted questions, along with typed extraction and run artifacts. The pipeline is operational but still has deferred consolidation, broader tracing, and later-stage quality work. The existing flow is therefore a good substrate for the next layer rather than a finished tutor system. fileciteturn16file12 fileciteturn16file9

This next layer should convert the extracted learning claims into a reusable, traceable cache of learner questions and curated answers, while keeping alignment to the earlier design principle that generated questions are **templates / priors** rather than a full learner-aware predictor. The earlier design also stressed that the downstream predictor should eventually use ranking and learner state, not pure generation. fileciteturn16file11 fileciteturn16file14

The `7630.yaml` sample is a good anchor because it already contains claim-level outcomes such as:
- basic R syntax and assignment
- data types
- vectors
- matrices
- factors
- data frames
- lists
- simple real-world analysis

Those are exactly the sort of repeated beginner intents that benefit from a cache-like fast path. fileciteturn16file0 fileciteturn16file1

---

## Product framing

Treat this as a **semantic Q/A cache with LLM fallback**, not as a raw prompt cache.

### Fast path
1. learner asks a question
2. system normalizes and matches it to a known question group
3. if confidence is high, return the canonical answer immediately
4. log the hit with lineage and confidence

### Slow path
1. if match confidence is low, or learner asks a follow-up, or question falls outside the known question groups
2. call the LLM
3. generate a grounded answer
4. log miss / fallback / repair metadata
5. optionally mark the interaction as a candidate for future cache warming

---

## Hard requirements

### 1. End-to-end traceability

Every output row and runtime lookup must preserve lineage:

- `course_id`
- `claim_id`
- `question_group_id`
- `variation_id`
- `canonical_answer_id`

Every question group and answer must be attributable to:
- the originating course
- the originating claim
- source citations from the extracted claim / course YAML evidence
- the generation run that produced it

### 2. Strict equivalence semantics

A `variation` is only a variation if all of the following are identical:
- learner intent
- requested knowledge / skill
- pedagogical move
- ideal answer content

If any of those differ, create a **separate question group**.

This is critical. The system must not group nearby but different questions just because they are semantically similar.

### 3. Cache-first runtime

At runtime, the system must try:
- exact normalized variation match
- semantic match over variation text / canonical question / question group metadata
- only then LLM fallback

### 4. Deterministic lineage-friendly IDs

The implementation must use deterministic IDs where possible:
- `claim_id`: existing claim ID
- `question_group_id`: derived from `course_id + claim_id + intent_slug`
- `variation_id`: derived from `question_group_id + normalized_variation_slug`
- `canonical_answer_id`: derived from `question_group_id + answer_version`

### 5. Preserve provenance

Every generated item must keep:
- citations back to YAML evidence or claim citations
- generation timestamp
- run ID
- model / prompt version
- reviewer status if human review is later added

---

## Deliverables

Codex should produce the following:

### A. Data model changes
Add new persisted entities for:
- `claim_question_groups`
- `question_group_variations`
- `canonical_answers`
- `question_cache_match_logs`
- `question_cache_fallback_logs`

### B. Generation pipeline step
Add a new pipeline stage after claim extraction:
- input: course + claim artifacts
- output: question groups, variations, canonical answers, citations

### C. Runtime matcher
Build a runtime matching layer that:
- normalizes incoming learner questions
- scores matches against variations and canonical questions
- returns a cache hit if confidence exceeds threshold
- routes to fallback otherwise

### D. Evaluation harness
Add offline and runtime evaluation for:
- grouping quality
- match precision
- cache hit rate
- answer usefulness
- miss taxonomy
- fallback frequency

### E. CLI entrypoints
Extend the CLI so this layer can be:
- generated in bounded runs
- inspected
- exported
- replayed against evaluation examples

---

## Proposed schema

## 1. Question group record

```yaml
question_group:
  question_group_id: "7630_LO3_create_vector"
  course_id: "7630"
  claim_id: "LO3"
  intent_slug: "create_vector"
  canonical_question: "How do I create a vector in R?"
  pedagogical_move: "direct_explanation"
  canonical_answer_id: "7630_LO3_create_vector_v1"
  confidence: 0.86
  citations:
    - field: "syllabus[1].title"
      evidence: "Vectors"
    - field: "syllabus[1].summary"
      evidence: "create vectors in R, name them, select elements from them, and compare different vectors"
  source_run_id: "..."
  prompt_version: "..."
```

## 2. Variation record

```yaml
variation:
  variation_id: "7630_LO3_create_vector_var_01"
  question_group_id: "7630_LO3_create_vector"
  text: "Show me how to make a vector in R."
  normalized_text: "show me how to make a vector in r"
  equivalence_notes: "Same intent and same ideal answer as canonical question."
  source: "generated"
```

## 3. Canonical answer record

```yaml
canonical_answer:
  canonical_answer_id: "7630_LO3_create_vector_v1"
  question_group_id: "7630_LO3_create_vector"
  answer_markdown: |
    Use the `c()` function to create a vector in R.

    Example:
    ```r
    scores <- c(10, 20, 30)
    ```

    This creates a vector containing three numeric values.
  answer_style: "short_direct"
  answer_version: 1
  citations:
    - field: "syllabus[1].summary"
      evidence: "create vectors in R"
  reviewer_state: "unreviewed"
```

---

## Proposed relational model

Use the existing relational approach and add the following tables.

### `claim_question_groups`
Columns:
- `question_group_id` TEXT PRIMARY KEY
- `course_id` TEXT NOT NULL
- `claim_id` TEXT NOT NULL
- `intent_slug` TEXT NOT NULL
- `canonical_question` TEXT NOT NULL
- `pedagogical_move` TEXT NOT NULL
- `canonical_answer_id` TEXT NOT NULL
- `confidence` DOUBLE PRECISION
- `source_run_id` TEXT NOT NULL
- `prompt_version` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- `(course_id)`
- `(claim_id)`
- `(course_id, claim_id)`
- unique `(claim_id, intent_slug)`

### `question_group_variations`
Columns:
- `variation_id` TEXT PRIMARY KEY
- `question_group_id` TEXT NOT NULL
- `text` TEXT NOT NULL
- `normalized_text` TEXT NOT NULL
- `source` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- `(question_group_id)`
- unique `(question_group_id, normalized_text)`

### `canonical_answers`
Columns:
- `canonical_answer_id` TEXT PRIMARY KEY
- `question_group_id` TEXT NOT NULL
- `answer_markdown` TEXT NOT NULL
- `answer_style` TEXT NOT NULL
- `answer_version` INTEGER NOT NULL
- `reviewer_state` TEXT NOT NULL
- `source_run_id` TEXT NOT NULL
- `prompt_version` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

Indexes:
- `(question_group_id)`

### `question_cache_match_logs`
Columns:
- `match_log_id` BIGSERIAL PRIMARY KEY
- `course_id` TEXT
- `claim_id` TEXT
- `question_group_id` TEXT
- `variation_id` TEXT
- `canonical_answer_id` TEXT
- `incoming_question` TEXT NOT NULL
- `normalized_question` TEXT NOT NULL
- `match_method` TEXT NOT NULL
- `match_score` DOUBLE PRECISION NOT NULL
- `resolved_as_hit` BOOLEAN NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

### `question_cache_fallback_logs`
Columns:
- `fallback_log_id` BIGSERIAL PRIMARY KEY
- `course_id` TEXT
- `claim_id` TEXT
- `incoming_question` TEXT NOT NULL
- `normalized_question` TEXT NOT NULL
- `fallback_reason` TEXT NOT NULL
- `llm_response_id` TEXT
- `candidate_for_cache_warming` BOOLEAN NOT NULL DEFAULT false
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

### citation linkage
If a normalized citations table already exists, add foreign keys or linkage rows so each question group and canonical answer can point back to the same evidence basis as the source claim.

---

## Generation stage spec

Create a new stage:
`claims_to_question_cache`

### Inputs
- normalized courses
- chapters
- learning claims
- claim citations
- optional pedagogical signals / misconceptions

### Outputs
- question groups
- question variations
- canonical answers
- JSONL exports:
  - `claim_question_groups.jsonl`
  - `question_variations.jsonl`
  - `canonical_answers.jsonl`

### Prompting rules
For each claim:
1. decompose the claim into distinct learner intents
2. create one question group per intent
3. generate only strict paraphrase variations within a group
4. generate one canonical answer per group
5. inherit or attach citations from the underlying claim evidence
6. keep answers concise and optimized for beginner trust-building
7. avoid creating “what / how / why” in the same group unless the ideal answer content is truly identical

### Example decomposition
For claim:
`Create, name, select, and compare vectors in R.`

Expected distinct question groups include:
- `create_vector`
- `name_vector_elements`
- `select_vector_elements`
- `compare_vectors`

Do **not** collapse all of those into one answer.

This preserves the traceable hierarchy:
`course 7630 -> LO3 -> create_vector -> variations -> answer` while keeping the group boundaries tighter and more faithful to actual learner intent. fileciteturn16file0

---

## Runtime matcher spec

Build a matcher with three levels.

### Level 1: deterministic normalization
Normalize:
- lowercase
- trim whitespace
- remove punctuation where appropriate
- normalize code-formatting artifacts
- collapse repeated spaces

### Level 2: symbolic / lexical match
Try:
- exact normalized match to existing variations
- exact match to canonical question
- lightweight token-overlap / BM25-style retrieval if already available

### Level 3: semantic match
Use embeddings or semantic retrieval to score against:
- variation text
- canonical question
- intent metadata
- claim text

Return top-k candidates with scores.

### Resolution logic
- if top score >= high-confidence threshold and margin over #2 is sufficient: return cached answer
- if ambiguous or low-confidence: fallback to LLM
- if user utterance is a clear follow-up, diagnostic report, or repair request: bypass cache and use LLM

---

## LLM fallback spec

Fallback should happen when:
- no acceptable cache match is found
- multiple groups compete closely
- learner asks follow-up / repair / clarification
- learner includes execution result, error text, or context not captured in the cache
- user requests a different explanation style

Fallback response should still try to attach traceability:
- nearest matched course / claim if available
- fallback reason
- generated answer
- candidate cache promotion flag

---

## Evaluation plan

The current broader design has already emphasized that tutoring systems need evaluation for learning behavior, not just extraction success, and that question templates should eventually support retrieval/ranking rather than a pure generative loop. fileciteturn16file13 fileciteturn16file11

For this cache layer, add the following evals.

### Offline generation eval
For a sample of claims:
- question-group boundary correctness
- variation strictness
- answer correctness
- citation adequacy
- redundancy rate

### Offline retrieval eval
For a labeled set of learner utterances:
- top-1 hit precision
- top-3 recall
- false-grouping rate
- fallback rate
- ambiguous-match rate

### Runtime quality eval
Log and monitor:
- median fast-path latency
- hit rate
- fallback rate
- user follow-up rate after cache hit
- user correction rate after cache hit
- answer helpfulness where available

### Cache warming eval
For fallback answers nominated for promotion:
- duplicate rate
- equivalence-boundary review pass rate
- answer reuse rate after promotion

---

## Implementation tasks for Codex

## Task 1: Add schemas and models
Implement Pydantic / ORM models for:
- `ClaimQuestionGroup`
- `QuestionGroupVariation`
- `CanonicalAnswer`
- `QuestionCacheMatchLog`
- `QuestionCacheFallbackLog`

Acceptance criteria:
- models validate deterministically
- IDs are stable
- lineage fields are mandatory
- citations are preserved

## Task 2: Add database migrations
Create migrations for the new tables and indexes.

Acceptance criteria:
- migrations are reversible
- foreign-key or linkage integrity to existing course / claim records is preserved
- unique constraints prevent duplicate variation rows inside a group

## Task 3: Implement claim-to-question-cache generation
Build a pipeline step that consumes claim artifacts and emits:
- distinct question groups
- strict paraphrase variations
- one canonical answer per group

Acceptance criteria:
- outputs can be written to Postgres and JSONL
- generation preserves citations
- grouped variations pass strict-equivalence validation

## Task 4: Implement strict-equivalence validator
Add a validation pass that checks whether each generated variation genuinely belongs to its group.

Possible strategy:
- use an LLM critic or rule-based checker
- compare candidate variation to canonical question and answer
- ensure same learner intent and same ideal answer content

Acceptance criteria:
- invalid variations are rejected or split into new groups
- validator decisions are logged

## Task 5: Implement runtime matcher
Build a lookup component that:
- normalizes incoming learner questions
- tries deterministic match
- tries semantic retrieval
- returns cache hit or miss with confidence

Acceptance criteria:
- matcher returns provenance with every hit
- matcher is testable independently
- matcher supports threshold tuning

## Task 6: Implement LLM fallback path
Build the miss path that:
- explains / answers using LLM
- records miss reason
- records nearest matched course/claim if any
- flags candidates for future warming

Acceptance criteria:
- fallback logs are persisted
- cache miss reasons are categorized
- responses can be reviewed for promotion

## Task 7: Implement export and inspection tooling
Extend CLI with commands such as:
- `build-question-cache`
- `inspect-question-group`
- `export-question-cache`
- `replay-question-cache-eval`

Acceptance criteria:
- bounded runs are supported
- exported artifacts are easy to diff
- outputs support human review

## Task 8: Add evaluation harness
Implement datasets and scripts for:
- generation eval
- retrieval eval
- cache hit / miss analysis

Acceptance criteria:
- reports can run on bounded samples
- metrics are versioned by run
- human-reviewable error cases are exported

---

## Suggested test fixtures

Use `7630.yaml` as an early fixture because it has clear beginner-level claims and multiple obvious sub-intents under claims such as vectors and data frames. The current extracted outcomes show both the claim structure and the limitations of the first-pass claim artifact, which makes it a useful regression fixture. fileciteturn16file0

Create tests such as:

### Positive grouping
Claim `LO3`
- "How do I create a vector in R?"
- "Show me how to make a vector in R."
Expected:
- same `question_group_id`
- same `canonical_answer_id`

### Negative grouping
Claim `LO3`
- "How do I create a vector in R?"
- "What is a vector in R?"
Expected:
- different `question_group_id`

### Runtime hit
Incoming:
- "How can I store several values in one vector?"
Expected:
- high-confidence hit to `create_vector`

### Runtime miss
Incoming:
- "Why does `x(2)` fail on my vector?"
Expected:
- cache miss or diagnostic-specific path
- LLM fallback

---

## Non-goals

Do not build all of the following in this task:
- full learner-state modeling
- mastery estimation
- tutoring policy engine
- multi-turn pedagogical adaptation
- final ranking-based question predictor

Those belong to later layers. This task is specifically about:
- fast-path trust-building
- semantic cache structure
- strict traceability
- clean fallback boundaries

---

## Recommended code organization

Suggested package layout:

```text
src/
  question_cache/
    models.py
    ids.py
    prompts.py
    validators.py
    generator.py
    matcher.py
    fallback.py
    exports.py
    evals.py
    cli.py
```

---

## Recommended prompts for generation

Codex should add prompt templates that instruct the model to:
- split each claim into distinct learner intents
- generate only strict paraphrases within each intent group
- produce exactly one canonical answer per group
- attach source citations inherited from the claim / YAML evidence
- keep answers short, direct, and suitable for beginner trust-building

The prompt should explicitly forbid grouping questions that differ in:
- intent
- pedagogical move
- ideal answer content

---

## Success criteria

This task is successful when:

1. a bounded run can generate traceable question groups and answers from extracted claims
2. the resulting artifacts preserve course -> claim -> question_group -> variation -> answer lineage
3. runtime matching returns fast-path answers for common beginner questions
4. misses cleanly fall back to the LLM
5. inspection and export tooling make grouping errors easy to audit
6. the cache can be warmed over time from fallback traffic

---

## Final instruction to Codex

Implement this as the **next layer on top of the current extraction pipeline**, not as a replacement for it.

The current extraction artifacts remain the source substrate.
This new layer should:
- consume those artifacts
- refine claim-level learning into reusable learner-intent Q/A groups
- preserve provenance and traceability
- accelerate runtime answers
- prepare the ground for later ranking, learner-state, and adaptive tutoring work
