# Question Ledger V6 Bundle

This bundle specifies a **ledger-first** end state for the question generation pipeline.

## Goal

At the end of the pipeline, preserve **all generated questions** in a single authoritative ledger.
Downstream outputs such as visible curated questions, cache-servable questions, alias maps, and inspection reports are derived **views**, not destructive filters.

## Core invariant

If a question is generated, it must end in exactly one of these terminal classes:

- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

Questions that are validated-correct must be preserved in the ledger even if they are not visible.

## Bundle contents

- `question_ledger_v6_spec.md` — product and pipeline spec
- `question_ledger_v6_codex_handoff.md` — implementation handoff for Codex
- `question_ledger_v6_schema.json` — ledger record schema
- `question_ledger_v6_config.yaml` — config knobs and policy defaults
- `question_ledger_v6_sample_all_questions.jsonl` — example ledger rows
- `question_ledger_v6_sample_inspection_report.md` — example human-readable report
- `question_ledger_v6_tests.md` — acceptance criteria and regression tests
- `question_ledger_v6_diagram.md` — Mermaid diagrams

## Deliverables Codex should produce

1. `all_questions.jsonl`
2. `visible_curated.jsonl`
3. `cache_servable.jsonl`
4. `aliases.jsonl`
5. `anchors_summary.json`
6. `inspection_report.md`

The source of truth is always `all_questions.jsonl`.
