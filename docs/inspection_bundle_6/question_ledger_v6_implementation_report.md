# Question Ledger V6 Implementation Report

## Scope

This report covers the ledger-first V6 slice defined in
[question_ledger_v6_codex_bundle](/code/docs/question_ledger_v6_codex_bundle).

V6 is not a new scoring layer. It is a consolidation layer that makes one
artifact authoritative:

- `all_questions.jsonl`

All other outputs are derived views over that ledger.

## What changed

### 1. Added an authoritative ledger row model

V6 introduces a normalized ledger row with:

- anchor metadata
- family and type fields
- canonical vs alias fields
- delivery class
- visibility and non-visible reasons
- stable question IDs
- scores and provenance

### 2. Added deterministic derived views

From `all_questions.jsonl`, V6 derives:

- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

This removes the need to treat several parallel artifacts as competing
sources of truth.

### 3. Added anchor summaries and grouped inspection reporting

The V6 report groups by anchor and shows:

- coverage status
- required-entry visibility
- counts by delivery class
- hidden reasons on non-visible questions

That makes the beginner-question problem easier to inspect at the anchor
level.

### 4. Added canonical phrasing normalization hooks

V6 adds a small normalization pass for canonical display text.

Examples:

- `What is repeated cycles?` -> `What are repeated cycles?`
- `What is ljung-box test?` -> `What is the Ljung-Box test?`

This is only a first pass, but it puts the normalization step in the right
place in the pipeline.

## Tests run

Unit tests:

- `tests/test_question_ledger_v6_basics.py`
- `tests/test_question_ledger_v6_views.py`

Executed with:

- `pytest -q tests/test_question_ledger_v6_basics.py tests/test_question_ledger_v6_views.py`

Result:

- `9 passed`

Additional verification:

- `python -m py_compile src/course_pipeline/*.py src/course_pipeline/question_ledger_v6/*.py`

## Bounded run

- V3 source run: `20260417T182414Z`
- V6 run: `20260418T012122Z`
- run dir: [20260418T012122Z](/code/data/pipeline_runs/20260418T012122Z)

## Outcome summary

### Totals

- all questions: `83`
- visible curated: `15`
- cache-servable: `0`
- aliases: `0`
- run errors: `0`

### What improved

The pipeline now has one authoritative question ledger and can reproduce the
visible set, cache set, alias set, and anchor summary from that ledger.

This is a real architectural improvement over V4.1.

### What did not improve yet

The ledger reflects current policy reality:

- almost all hidden correct items are still `analysis_only`
- there are no `cache_servable` or `alias_only` rows in the bounded run

That is not a V6 failure. It means the current upstream policy and
canonicalization layers are still conservative and under-producing those
classes.

## Assessment

V6 is a useful cleanup and should stay.

It does not solve the remaining product issue around missing or hidden
beginner entry questions. What it does do is make that problem easier to
measure and reason about because every question now has one normalized ledger
row and one terminal delivery class.
