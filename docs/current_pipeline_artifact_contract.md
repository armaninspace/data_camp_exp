# Current Pipeline Artifact Contract

Purpose: describe the artifact layout and stage ownership of the current enhanced pipeline before the early-semantic refactor lands.

This document is the baseline for Slice 0 of the execution backlog.

## Current Stage Ownership

### Deterministic stages

These stages are currently deterministic or primarily deterministic:

- normalization
  - parses YAML
  - recovers `course_id`
  - normalizes course/chapter structure
- candidate semantics extraction
  - heuristic topic extraction
  - heuristic edge extraction
  - heuristic pedagogy extraction
  - deterministic friction mining
- candidate filtering / scoring / dedupe
- policy classification and coverage audit
- V6 ledger generation
- derived view generation
- inspection bundle validation

### LLM-backed stages

These stages are currently LLM-assisted:

- candidate repair
  - `candidate_repair`
- candidate expansion
  - `candidate_expand`
- review-answer generation for inspection bundle pages when `OPENAI_API_KEY` is present
  - `policy_review_answers`
  - older candidate review-answer path still exists but is not the normal Prefect production path

## Current Run Layout

For a Prefect run rooted at `data/pipeline_runs/<run_id>/`:

- `run_manifest.json`
  - run metadata
  - selected course scope
  - metering summary
- `courses.jsonl`
  - normalized courses selected for the run
- `standardized/`
  - normalized course YAML outputs

### `semantics/`

Current meaning:
- not an independent semantic stage yet
- currently stores heuristic semantic outputs produced as part of candidate generation

Artifacts:
- `topics.jsonl`
- `edges.jsonl`
- `pedagogy.jsonl`
- `friction_points.jsonl`
- `course_artifacts/<course_id>/...`

### `candidates/`

Current meaning:
- candidate generation plus LLM refinement artifacts

Artifacts:
- `candidate_repairs.jsonl`
- `candidate_expansions.jsonl`
- `candidate_merge_report.jsonl`
- `merged_candidates.jsonl`
- per-course candidate artifacts under `course_artifacts/<course_id>/`
- per-course:
  - `question_refine.yaml`
  - `question_expand.yaml`

### `policy/`

Current meaning:
- deterministic selection, validation, coverage audit, visibility classification

Artifacts:
- validated-correct question artifacts
- hidden-correct question artifacts
- hard-reject summaries
- `visible_curated.jsonl`
- `coverage_warnings.jsonl`
- `course_artifacts/<course_id>/...`

### `ledger/`

Current meaning:
- authoritative question ledger and coverage summaries

Artifacts:
- `all_questions.jsonl`
- `anchors_summary.json`
- `question_ledger_v6_report.md`
- `course_artifacts/<course_id>/anchors_summary.json`
- per-course inspection report artifacts

### Run root deliverables

Promoted or copied up to the run root:
- `all_questions.jsonl`
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `question_ledger_v6_report.md`

### Review / bundle artifacts

When bundle rendering runs:
- `review_bundle/`
  - per-course markdown pages
- `review_answers.jsonl`
  - LLM-generated answers for visible curated questions when the LLM path runs
- `llm_metering.jsonl`
  - metering rows for LLM-backed stages when invoked

## Current Architectural Constraint

The biggest current gap relative to the refactor target is:

- semantic extraction is still heuristic-first
- LLM work starts at question repair and expansion, not before semantic sanitation

That means downstream deterministic governance is already in place, but the semantic layer can still admit weak anchors before refinement.

## Regression Reference Run

Known enhanced regression reference:
- run id: `20260418T212725Z`

Useful properties:
- enhanced repair / expansion path ran
- metering completed
- bundle artifacts exist
- known coverage failure remains visible:
  - `24370:unemployment`

This run should continue to be usable as a regression reference while the early-semantic refactor is introduced.
