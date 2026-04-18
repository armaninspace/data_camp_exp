# Codex Tasking: Fix the Question-Cache Pipeline

## Objective

Patch the current question-cache generation pipeline so that it only produces **strict same-answer variations**.

The new rule is:

> A variation is valid only if the exact same canonical answer is fully correct and sufficient for that variation.

If the answer would need to change in scope, wording, pedagogical move, assumptions, or content, the candidate is **not** a variation. It must become a **separate question group** or be rejected.

This task must preserve full traceability:

`course -> claim -> question_group -> variation -> canonical_answer`

---

## Why this patch is needed

The current cache artifacts are traceable, but they are still inconsistent in ways that make them risky for a production fast-path cache:

- some valid source claims are missing from the generated cache
- some question groups contain overly loose paraphrases
- some canonical answers do not actually answer the canonical question
- some answers overreach the cited source evidence
- confidence values are placeholder-like instead of meaningfully calibrated

This patch is meant to turn the cache generator from a schema-filling system into a constrained, evidence-grounded cache builder.

---

## Root cause diagnosis

The current generation flow is too loose:

`claim -> invent groups + invent variations + invent answers`

That encourages the model to optimize for completeness and formatting rather than truth-preserving decomposition.

The failure modes already visible in the current artifact are:

1. **Broad claims were decomposed too loosely**
   - Example: a claim like "Identify and use basic data types in R" mixes multiple possible intents.
   - Result: a "use-basic-data-types" group also absorbed "How do you create basic data types in R?" which should likely be separate.

2. **Answer fit was not validated**
   - Example: the `name-vector` group answers object assignment, not naming vector elements.

3. **Evidence grounding was not strict enough**
   - Example: some answers introduce actions like importing data that are not clearly supported by the source claim evidence.

4. **Coverage completeness was not enforced**
   - Some source claims did not produce any visible groups and were silently dropped.

5. **Variation generation happened too early**
   - Variations were created before the system had locked down the atomic question intent and the exact reusable answer.

---

## Required design change

Replace the current flow with this:

`claim -> atomic question groups -> canonical answer -> candidate variations -> validators -> persist`

### New generation order

1. **Atomic group extraction**
   - Split each claim into distinct learner question groups.
   - Each group must represent one atomic question intent.

2. **Canonical answer generation**
   - Generate one canonical answer per question group.
   - Keep it short, stable, and evidence-grounded.

3. **Variation generation**
   - Generate only candidate paraphrases of the canonical question.

4. **Validation**
   - Run three validators:
     - same-answer variation validator
     - answer-to-question fit validator
     - evidence-grounding validator

5. **Coverage audit**
   - Verify every source claim either:
     - produced at least one valid question group, or
     - produced an explicit no-groups reason

6. **Persistence**
   - Persist only validated artifacts.

---

## Hard behavioral rules

### Rule 1: Same-answer rule

A candidate variation is valid only if all of the following are identical to the canonical question:

- learner intent
- requested knowledge or skill
- pedagogical move
- ideal answer content

If any of those differ, reject the variation or split it into a new question group.

### Rule 2: Prefer splitting over merging

If there is doubt about whether two learner utterances belong in one group, split them.

False splits are safer than false merges for a trust-building cache.

### Rule 3: Answer first, paraphrase second

Never generate variations before the canonical answer is fixed.

### Rule 4: Every answer sentence must be evidence-supported

Every substantive sentence in `canonical_answer.answer_markdown` must be supported by the cited source evidence.

If not, fail validation.

### Rule 5: No silent claim drops

Every claim from the source artifact must be accounted for.

---

## Updated pipeline stages

## Stage A: Claim atomization

### Input
- extracted course claims
- claim citations
- optional pedagogical metadata

### Output
- atomic question groups only

### Required output fields
- `course_id`
- `claim_id`
- `question_group_id`
- `intent_slug`
- `canonical_question`
- `pedagogical_move`
- `citations`
- `source_run_id`
- `prompt_version`

### Prompt contract

```text
From this claim, create atomic learner question groups.

Rules:
- Each group must represent one distinct learner question intent.
- Each group must be answerable with one short canonical answer.
- If two candidate questions would require different answers, they must be separate groups.
- Prefer splitting over merging.
- Do not generate variations yet.
- Do not generate answers yet.
```

### Example

For a claim like:

`Create, name, select, and compare vectors in R.`

Expected groups include:
- `create_vector`
- `name_vector_elements`
- `select_vector_elements`
- `compare_vectors`

Do not merge these into one group.

---

## Stage B: Canonical answer generation

### Input
- validated atomic question groups
- source claim evidence

### Output
- one canonical answer per question group

### Prompt contract

```text
Write one canonical answer for this question group.

Rules:
- The answer must directly answer the canonical question.
- The answer must stay within cited source evidence.
- Keep it short and stable enough for reuse across paraphrases.
- Do not add unsupported details.
- Do not anticipate follow-up questions unless required by the canonical question.
```

### Constraints
- one group -> one canonical answer
- no branching responses
- no optional sections unless stable across all paraphrases
- no examples unless the canonical question clearly requires or supports them

---

## Stage C: Variation generation

### Input
- canonical question
- canonical answer
- citations

### Output
- candidate variations only

### Prompt contract

```text
Generate paraphrases of the canonical question.

Hard rule:
Generate only paraphrases for which the exact same canonical answer is fully correct and sufficient.

Reject anything that:
- changes scope
- changes pedagogical move
- asks for motivation instead of procedure
- asks for examples when the canonical question does not
- asks for debugging, comparison, definition, or why-explanation if the answer would need to change
- narrows or broadens the request
```

### Additional generation heuristics
- prefer natural learner phrasing
- ban awkward synthetic phrasing such as:
  - "What is the way to..."
  - "What is the process to..."
  - "How would one..."
- generate 2–4 high-quality variations max
- allow zero generated variations if none pass validation

---

## Stage D: Validators

This stage is mandatory.

### Validator 1: Same-answer variation validator

#### Goal
Check whether a candidate variation is a true same-answer paraphrase.

#### Inputs
- canonical question
- canonical answer
- candidate variation

#### Decision outputs
- `ACCEPT`
- `REJECT`
- `SPLIT_NEW_GROUP`

#### Prompt contract

```text
Given:
- canonical question
- canonical answer
- candidate variation

Decide whether the candidate variation is a true paraphrase.

Return ACCEPT only if:
1. learner intent is identical
2. requested knowledge/skill is identical
3. pedagogical move is identical
4. the exact same canonical answer is fully correct and sufficient

If any fail:
- return REJECT, or
- return SPLIT_NEW_GROUP if it should become its own question group
```

#### Persist validator metadata
Store:
- validator decision
- rationale
- model version
- timestamp

### Validator 2: Answer-to-question fit validator

#### Goal
Check whether the canonical answer actually answers the canonical question.

#### Inputs
- canonical question
- canonical answer

#### Decision outputs
- `PASS`
- `FAIL`

#### Prompt contract

```text
Determine whether the canonical answer directly and correctly answers the canonical question.

Fail if:
- the answer responds to a nearby but different question
- the answer omits required information
- the answer changes the intent
- the answer answers a broader or narrower question
```

### Validator 3: Evidence-grounding validator

#### Goal
Ensure that the answer content is supported by the cited source evidence.

#### Inputs
- canonical answer
- citations
- cited evidence text

#### Decision outputs
- `PASS`
- `FAIL`

#### Prompt contract

```text
Check whether every substantive claim in the canonical answer is supported by the cited evidence.

Fail if:
- the answer introduces unsupported operations, concepts, or examples
- the answer relies on outside knowledge not justified by the evidence
- the citations are too weak to support the answer
```

### Validator 4: Coverage audit

#### Goal
Ensure no claims disappear.

#### Inputs
- source claim list
- generated question groups

#### Decision outputs
- `PASS`
- `FAIL`

#### Rule
Every source claim must end in one of two states:
- `produced_question_groups = true`
- `produced_question_groups = false` with explicit `no_groups_reason`

Fail the run if any claim is unaccounted for.

---

## Schema changes

Add these fields to support validation and auditability.

### `claim_question_groups`
New / updated fields:
- `generation_stage` TEXT NOT NULL
- `validator_status` TEXT NOT NULL
- `coverage_status` TEXT NOT NULL DEFAULT 'accounted_for'

### `question_group_variations`
New / updated fields:
- `candidate_source` TEXT NOT NULL
- `validation_decision` TEXT NOT NULL
- `validation_reason` TEXT
- `accepted_for_runtime` BOOLEAN NOT NULL DEFAULT false

### `canonical_answers`
New / updated fields:
- `answer_fit_status` TEXT NOT NULL
- `grounding_status` TEXT NOT NULL
- `grounding_reason` TEXT
- `answer_scope_notes` TEXT

### New table: `question_cache_validation_logs`
Columns:
- `validation_log_id` BIGSERIAL PRIMARY KEY
- `entity_type` TEXT NOT NULL
- `entity_id` TEXT NOT NULL
- `validator_type` TEXT NOT NULL
- `decision` TEXT NOT NULL
- `reason` TEXT
- `model_version` TEXT
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

### New table: `claim_coverage_audit`
Columns:
- `audit_id` BIGSERIAL PRIMARY KEY
- `course_id` TEXT NOT NULL
- `claim_id` TEXT NOT NULL
- `produced_question_groups` BOOLEAN NOT NULL
- `question_group_count` INTEGER NOT NULL DEFAULT 0
- `no_groups_reason` TEXT
- `source_run_id` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

---

## Runtime policy changes

Only serve cache hits from:
- validated question groups
- accepted variations
- canonical answers that passed fit and grounding validation

### Runtime hit logic
1. normalize incoming question
2. exact-match accepted variations
3. semantic-match accepted variations and canonical questions
4. only return cached answer if:
   - variation is accepted
   - question group is validated
   - answer fit passed
   - grounding passed
   - match score exceeds threshold

Otherwise go to fallback.

### Runtime miss reasons
Track:
- `no_match`
- `ambiguous_match`
- `variation_rejected`
- `answer_unvalidated`
- `grounding_failed`
- `follow_up_or_repair`
- `claim_uncovered`

---

## Evaluation updates

### Offline generation evaluation
For a bounded sample:
- group boundary correctness
- answer-fit pass rate
- evidence-grounding pass rate
- coverage completeness
- accepted-variation precision
- rejected-variation false negative rate

### Runtime evaluation
Track:
- hit rate on accepted variations
- false-hit rate
- user correction rate after cache hit
- follow-up rate after cache hit
- fallback rate by reason
- cache usefulness rating where available

### Promotion safety metric
A question group is eligible for production only if:
- all validators pass
- at least one accepted variation exists
- coverage audit passes
- reviewer state is acceptable per policy

---

## Implementation tasks for Codex

### Task 1: Refactor generation order
Replace the old one-shot generator with a staged pipeline:
- claim atomization
- canonical answer generation
- variation generation
- validators
- coverage audit

Acceptance criteria:
- no variations are generated before canonical answers
- outputs are stage-tagged
- failed stages block persistence

### Task 2: Implement validator services
Add validator modules for:
- same-answer variation validation
- answer-to-question fit
- evidence grounding
- coverage audit

Acceptance criteria:
- validators produce machine-readable decisions
- all decisions are logged
- failed validations prevent runtime serving

### Task 3: Update persistence layer
Add new tables / columns for validation outcomes and coverage audit.

Acceptance criteria:
- migrations are reversible
- accepted runtime artifacts are queryable
- audit failures are visible in inspection tooling

### Task 4: Update prompts
Replace current prompts with staged prompts defined in this document.

Acceptance criteria:
- prompts explicitly prioritize splitting over merging
- prompts forbid unsupported detail injection
- prompts do not generate weak synthetic paraphrases

### Task 5: Update CLI
Add or update commands such as:
- `build-question-cache`
- `validate-question-cache`
- `audit-question-cache-coverage`
- `inspect-question-group`
- `export-question-cache`

Acceptance criteria:
- bounded runs supported
- failed validation summarized clearly
- exports distinguish accepted vs rejected variations

### Task 6: Add regression fixtures
Use the existing intro R artifacts as fixtures.

Add tests such as:

#### Positive same-answer group
Canonical question:
- "How do you create a vector in R?"
Variation:
- "How do I make a vector in R?"
Expected:
- `ACCEPT`

#### Negative same-answer group
Canonical question:
- "How do you create a vector in R?"
Variation:
- "What is a vector in R?"
Expected:
- `SPLIT_NEW_GROUP` or `REJECT`

#### Answer-fit failure
Canonical question:
- "How do you name vector elements in R?"
Canonical answer:
- answer about assigning the vector to a variable
Expected:
- `FAIL`

#### Grounding failure
Canonical question:
- question about analyzing real-world datasets
Canonical answer:
- introduces unsupported data import steps not evidenced by source
Expected:
- `FAIL`

#### Coverage audit failure
Source claim present with no generated question groups and no explicit no-groups reason
Expected:
- `FAIL`

### Task 7: Enforce production gate
Only mark artifacts as runtime-eligible if all validators pass.

Acceptance criteria:
- production query path only sees runtime-eligible groups
- rejected groups remain inspectable but not serveable

---

## Suggested code organization

```text
src/
  question_cache/
    generator/
      atomize_claims.py
      generate_answers.py
      generate_variations.py
    validators/
      same_answer.py
      answer_fit.py
      grounding.py
      coverage.py
    persistence/
      models.py
      migrations/
    runtime/
      matcher.py
      serve.py
    evals/
      offline.py
      runtime.py
    cli.py
```

---

## Non-goals

This patch does **not** build:
- learner-state modeling
- mastery estimation
- multi-turn tutor policy
- personalized answer adaptation
- ranking-based next-question prediction

This patch is only about making the **fast-path cache** consistent, grounded, and safe to trust.

---

## Success criteria

This patch is successful when:

1. every source claim is accounted for
2. no question variation is served unless the same canonical answer truly works
3. no canonical answer is served unless it passes answer-fit validation
4. no canonical answer is served unless it passes evidence grounding
5. runtime only serves validated cache entries
6. grouping errors become easy to inspect and fix

---

## Final instruction to Codex

Implement this as a corrective patch to the existing question-cache layer.

Do not replace the extraction pipeline.
Do not broaden scope into full tutoring behavior.

Focus on:
- atomic decomposition
- answer-first generation
- strict same-answer variation acceptance
- hard validation gates
- complete claim coverage
- traceable persistence
