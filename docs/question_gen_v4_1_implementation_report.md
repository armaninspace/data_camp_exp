# Question Generation V4.1 Implementation Report

## Scope

This report covers the V4.1 persistence-and-coverage slice specified in
[req_bundle_4_1](/code/docs/req_bundle_4_1).

V4.1 does not replace V4 scoring. It changes what happens after candidate
generation so the system can distinguish:

- generated and valid
- hidden but retained
- visible and curated
- invalid and rejected

## What changed

### 1. Validated-correct candidates now persist before curation

The V4.1 stage validates candidates first and builds a durable ledger of all
validated-correct candidates before visible selection is applied.

New persisted artifacts include:

- `validated_correct_all.jsonl`
- `visible_curated.jsonl`
- `hidden_correct.jsonl`
- `coverage_warnings.jsonl`
- `hard_reject_records.jsonl`

### 2. Visibility is now separate from delivery class

Validated-correct candidates are stored with:

- `delivery_class`
- `visible`
- `non_visible_reasons`
- foundational-anchor flags
- canonical linkage

That means a question can now exist in storage even if it is not shown in
the visible set.

### 3. Foundational anchor coverage is now audited

V4.1 detects `foundational_vocabulary_anchor` topics and checks whether a
visible canonical definition question exists for each one.

If not, it emits machine-readable warnings such as:

- `definition_generation_failed`
- `only_hidden_correct_entry_exists`

This is the main fix for the silent-missing-beginner-question problem.

### 4. Inspection output now exposes hidden-but-correct questions

Review docs now include:

- visible curated questions
- hidden but correct questions with non-visible reasons
- coverage warnings

That makes failures like missing `What is seasonality?` inspectable rather
than implicit.

## Final bounded run

- V3 source run: `20260417T182414Z`
- V4.1 run: `20260417T235527Z`
- run dir: [20260417T235527Z](/code/data/pipeline_runs/20260417T235527Z)

## Result summary

### `24491`

- validated-correct: `35`
- visible curated: `8`
- hidden correct: `27`
- coverage warnings: `11`

Most important audit outcome:

- `What is exponential smoothing?` is now preserved as hidden-but-correct.
- `What is seasonality?` is now surfaced as a `definition_generation_failed`
  warning because no definition candidate was generated at all.

### `24593`

- validated-correct: `12`
- visible curated: `3`
- hidden correct: `9`
- coverage warnings: `5`

Main outcome:

- `What is a univariate time series?` is retained and visible as hidden
  rather than disappearing.

### `24594`

- validated-correct: `36`
- visible curated: `4`
- hidden correct: `32`
- coverage warnings: `7`

Main outcome:

- hidden definition questions for `flight data`, `xts`, `zoo`, `weather data`,
  and `economic data` are preserved and explicitly flagged as not visible.

## Regression checks run

I ran:

- `python -m py_compile src/course_pipeline/*.py src/course_pipeline/question_gen_v4_1/*.py`
- bounded dry-runs on `24491`, `24593`, and `24594`
- full V4.1 pipeline run and review-bundle build

The bounded checks confirmed:

- validated-correct candidates are persisted
- hidden candidates remain inspectable
- coverage warnings are emitted for missing visible anchor coverage

## Residual gaps

### 1. V4.1 audits the missing beginner-question problem; it does not fully solve generation

If a definition question was never generated, V4.1 now emits a warning, but
it does not fabricate a new candidate by itself.

So for `24491`:

- `What is seasonality?` is still absent from the candidate set
- but the system now reports that absence explicitly

### 2. Anchor heuristics are still broad

Some warnings still attach to coarse topics that may not be ideal anchors.
This is acceptable for V4.1 because the goal here is auditability, but the
anchor detector can still be refined.

## Assessment

V4.1 is complete for the stated slice.

The important change is not better question quality by itself. The important
change is that correct beginner questions can no longer disappear silently,
and missing visible beginner coverage is now machine-detectable.
