# Question Ledger V6 Backlog

This backlog implements the ledger-first requirements in:

- [question_ledger_v6_bundle_readme.md](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_bundle_readme.md)
- [question_ledger_v6_spec.md](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_spec.md)
- [question_ledger_v6_codex_handoff.md](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_codex_handoff.md)
- [question_ledger_v6_schema.json](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_schema.json)
- [question_ledger_v6_config.yaml](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_config.yaml)
- [question_ledger_v6_tests.md](/code/docs/question_ledger_v6_codex_bundle/question_ledger_v6_tests.md)

## Assessment

The V6 proposal makes sense.

V4.1 fixed auditability, but it still emits several overlapping artifacts with
no single canonical record type. V6 is the right cleanup step:

- one authoritative ledger row per generated question
- derived views for curated, cache, aliases, and anchor summaries
- inspection output derived from the ledger, not parallel ad hoc structures

## Slice 1: Scaffold V6 package, models, config, and baseline tests

- add `src/course_pipeline/question_ledger_v6/`
- add config loader
- add ledger row and anchor summary models
- add question-family and question-type normalization helpers
- add baseline unit tests for config and model normalization

Acceptance criteria:
- V6 package exists
- schema fields are represented in code
- tests pass

## Slice 2: Implement ledger builder and derived views

- build `all_questions.jsonl` rows from V4.1 candidate records
- include hard rejects in the ledger
- derive:
  - `visible_curated.jsonl`
  - `cache_servable.jsonl`
  - `aliases.jsonl`
  - `anchors_summary.json`
  - `inspection_report.md`
- ensure derived views are reproducible from the ledger alone

Acceptance criteria:
- every generated question ends up in exactly one ledger row
- no validated-correct question disappears
- unit tests cover view derivation and anchor summaries

## Slice 3: Wire V6 into pipeline and CLI, then run bounded inspection

- add pipeline entry point and CLI command
- run V6 on the bounded time-series courses:
  - `24491`
  - `24593`
  - `24594`
- publish a new inspection bundle with:
  - ledger outputs
  - report
  - sample course slices
  - implementation note

Acceptance criteria:
- a bounded V6 run completes successfully
- inspection artifacts exist under `docs/inspection_bundle_6`
- regression tests and bounded run checks pass
