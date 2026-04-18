# Question Cache Pipeline Review Report

## Purpose

This report summarizes the current state of the question-cache pipeline for an
external reviewer.

It covers:

1. what was implemented
2. what was executed and verified
3. what currently works
4. what is still failing
5. the practical recommendation for next work

## Executive Summary

The question-cache pipeline has been materially improved at the architecture and
auditability level.

The system is no longer a loose one-shot generator. It now has a staged
pipeline with explicit validation and coverage tracking.

The new shape is:

1. claim atomization
2. canonical answer generation
3. variation generation after the answer exists
4. validation
5. coverage audit
6. persistence of only traceable artifacts

This is a real improvement over the earlier cache build.

However, the pipeline is **not yet trustworthy enough for broad runtime use**.
The main blocker is now output quality rather than infrastructure. In bounded
runs, the system still produces too many weak canonical questions and too many
answer-fit failures.

## Scope Of Work Completed

The following changes were implemented.

### 1. Staged cache generation

The cache build was refactored so it no longer performs:

`claim -> groups + variations + answers in one step`

It now performs:

`claim -> atomic groups -> canonical answers -> candidate variations -> validators -> coverage audit`

Primary implementation:
- [src/course_pipeline/question_cache.py](/code/src/course_pipeline/question_cache.py:1)

### 2. Validation-bearing schemas

The artifact schemas were extended to support:

- question-group generation stage
- group validator status
- coverage status
- variation validation decision
- variation acceptance for runtime
- answer-fit status
- grounding status
- answer scope notes
- validation-log rows
- claim coverage audit rows

Primary implementation:
- [src/course_pipeline/schemas.py](/code/src/course_pipeline/schemas.py:1)

### 3. Persistence for validation and audit data

The database layer was extended to persist:

- validated question groups
- validated variations
- canonical answers with answer-fit and grounding state
- validation logs
- claim coverage audits
- runtime match logs
- runtime fallback logs

Primary implementation:
- [src/course_pipeline/storage.py](/code/src/course_pipeline/storage.py:1)

### 4. Export and inspection support

The pipeline now exports:

- `claim_question_groups.jsonl`
- `question_group_variations.jsonl`
- `canonical_answers.jsonl`
- `question_cache_validation_logs.jsonl`
- `claim_coverage_audit.jsonl`
- per-course YAML inspection artifacts

Primary implementation:
- [src/course_pipeline/pipeline.py](/code/src/course_pipeline/pipeline.py:1)

### 5. CLI support

The CLI now supports:

- `build-question-cache`
- `render-question-cache-yaml`
- `inspect-question-cache-run`
- `ask-question-cache`
- `replay-question-cache-eval`
- `validate-question-cache`
- `audit-question-cache-coverage`

Primary implementation:
- [src/course_pipeline/cli.py](/code/src/course_pipeline/cli.py:1)

## Bounded Runs Executed

The following bounded runs were executed during the patch work.

### Learning-outcome substrate

Source learning-outcomes run:
- `20260414T025608Z`

This run provided the claim layer used as the substrate for the question-cache
build.

### Question-cache runs

#### Run `20260414T044133Z`

This was the first staged attempt.

Result:
- structurally valid pipeline
- atomization collapsed all claims to `no_safe_atomic_groups`
- no groups were persisted
- coverage audit still accounted for every claim

Interpretation:
- architecture worked
- atomization strategy was too weak

#### Run `20260414T044343Z`

This run added a deterministic fallback atomizer.

Result:
- groups, answers, and validation logs were produced
- claim coverage was complete
- many question groups still failed answer-fit

Interpretation:
- staged generation became operational
- quality remained weak

#### Run `20260414T044551Z`

This run improved the atomizer to carry shared objects such as `vectors`,
`basic data types`, and similar phrases into the generated intents.

Result:
- full staged artifacts produced
- no pipeline exceptions
- all source claims covered
- answer-fit improved slightly but remained the dominant failure mode

This is the best current run for review.

## Review Artifact For One Course

The best single-course inspection artifact is:

- [7630.yaml](/code/data/pipeline_runs/20260414T044551Z/question_cache_yaml/7630.yaml:1)

That file shows, for course `7630`:

1. source claim text
2. generated question groups
3. candidate variations
4. canonical answers
5. per-group validation state
6. per-answer validation state
7. coverage accounting

Related machine-readable artifacts for the same run:

- [claim_question_groups.jsonl](/code/data/pipeline_runs/20260414T044551Z/claim_question_groups.jsonl:1)
- [question_group_variations.jsonl](/code/data/pipeline_runs/20260414T044551Z/question_group_variations.jsonl:1)
- [canonical_answers.jsonl](/code/data/pipeline_runs/20260414T044551Z/canonical_answers.jsonl:1)
- [question_cache_validation_logs.jsonl](/code/data/pipeline_runs/20260414T044551Z/question_cache_validation_logs.jsonl:1)
- [claim_coverage_audit.jsonl](/code/data/pipeline_runs/20260414T044551Z/claim_coverage_audit.jsonl:1)

## What Works Now

### 1. The pipeline is staged and inspectable

The cache builder is no longer opaque. The output state now reflects which
parts passed, failed, or were only accounted for by audit.

### 2. Every source claim is accounted for

The coverage audit now prevents silent disappearance of source claims.

For run `20260414T044551Z`:
- `claims=8`
- `uncovered=0`

### 3. Runtime gating is structurally possible

The schema now supports serving only:

- validated groups
- accepted variations
- answers that passed answer-fit
- answers that passed grounding

Even where output quality is still weak, the system now has the right control
surfaces to avoid serving bad artifacts accidentally.

### 4. Validation output is reviewable

Validator decisions are no longer implicit. They are exported and queryable.

## What Is Still Failing

### 1. Answer-fit is the main blocker

For run `20260414T044551Z`, validation summary was:

- `answer_fit:PASS=5`
- `answer_fit:FAIL=16`
- `grounding:PASS=18`
- `grounding:FAIL=3`
- `coverage_audit:PASS=8`

This makes the current cache too weak for broader serving.

### 2. Canonical questions are still often poor

Examples visible in the current artifacts include awkward or underspecified
questions such as:

- `How do you recall assignment?`
- `How do you identify basic data types in R?`

These are mechanically traceable, but they are not good learner-facing cache
keys.

### 3. Some canonical answers still do not fit the question

The pipeline now catches many of these via `answer_fit_status = fail`, but this
also demonstrates that the generation layer is still producing unstable output.

### 4. Grounding improved more than fit, but is not fully clean

Most answers pass grounding, but some still fail.

That means the evidence-boundary rule is partially working, but not yet strong
enough to trust without bounded inspection.

## Interpretation

This patch succeeded as a **pipeline correction**.

It did not yet succeed as a **quality completion**.

That distinction matters:

1. The system now has the right architecture for a trustworthy cache.
2. The system does not yet generate high-quality enough artifacts to justify
   broader rollout.

In other words:

- infrastructure: substantially improved
- auditability: substantially improved
- gating safety: substantially improved
- content quality: still insufficient

## Recommendation

Do not broaden runtime use yet.

Recommended next step:

1. keep runs bounded to high-signal fixtures such as `7630`
2. improve claim atomization quality
3. improve canonical answer prompts and/or use more deterministic answer
   templates where possible
4. keep answer-fit as the primary quality metric
5. only expand once answer-fit failures fall materially

## Bottom Line

The question-cache pipeline is now structurally credible but not yet content-safe.

The current implementation is suitable for:

- bounded evaluation
- inspection
- validator development
- regression fixtures

It is not yet suitable for a broader trust-building fast path without more
quality work.
