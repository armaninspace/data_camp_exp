# Project Spec

## Purpose

This project builds a traceable pipeline that turns scraped course metadata
into inspectable question-generation artifacts.

The current repository is focused on Class Central DataCamp course YAML, with
bounded evaluation work centered on R time-series courses.

The project exists to answer three operational questions:

1. what a course appears to teach, based on scraped evidence
2. what learner questions are reasonable to generate from that evidence
3. which generated questions are safe to surface, cache, inspect, or reject

## Product Goal

The target product is not a generic chatbot.

The target product is an evidence-bound course-question pipeline that produces:

- normalized course records
- inspectable topic and friction extraction
- generated learner-question candidates
- policy and coverage decisions
- one authoritative question ledger
- inspection bundles for human review

## Non-Goals

The current project does not attempt to:

- infer actual student performance
- generate unrestricted open-domain answers
- claim that every surfaced question is production-ready
- replace source material with a full teaching system
- hide uncertainty when the source evidence is weak

## Primary Input

The main input is raw course YAML scraped from Class Central / DataCamp.

Typical input fields:

- course title
- summary
- overview
- syllabus / chapter list
- provider metadata
- ratings and course details

## Core Output Model

The current product focus is one canonical question pipeline:

`raw course YAML -> normalized course -> candidate questions -> policy decisions -> ledger -> inspection`

Historical learning-outcome and question-cache experiments are no longer part
of the active source tree or CLI surface.

## Canonical Architectural View

The project is best understood as five layers.

### Layer 1: Deterministic Standardization

This layer parses raw YAML into a stable `NormalizedCourse` model.

Responsibilities:

- safe YAML parsing
- stable `course_id` recovery
- chapter normalization
- metadata cleanup
- deterministic export

Main artifacts:

- `courses.jsonl`
- `chapters.jsonl`
- standardized per-course YAML

Relevant code:

- [normalize.py](/code/src/course_pipeline/normalize.py)
- [schemas.py](/code/src/course_pipeline/schemas.py)
- [pipeline.py](/code/src/course_pipeline/pipeline.py)

### Layer 2: Candidate Extraction And Generation

This layer generates learner-question candidates from course content.

Implementation is still split across version-labeled packages, but the live
architectural responsibility is:

`normalized course -> topics / edges / pedagogy / frictions -> candidates`

Relevant code:

- [question_gen_v3](/code/src/course_pipeline/question_gen_v3)
- [questions/candidates.py](/code/src/course_pipeline/questions/candidates.py)

### Layer 3: Policy And Coverage

This layer classifies validated candidates into terminal delivery states and
enforces foundational-entry coverage.

Relevant code:

- [question_gen_v4](/code/src/course_pipeline/question_gen_v4)
- [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)
- [questions/policy.py](/code/src/course_pipeline/questions/policy.py)

### Layer 4: Ledger and Inspection

This layer consolidates all generated questions into one normalized ledger and
derives the inspection surfaces from that ledger.

This is the current authoritative artifact layer.

Responsibilities:

- normalize question rows
- persist one row per question
- derive visible and hidden views
- summarize anchor coverage
- generate inspection reports and bundles

Main artifacts:

- `all_questions.jsonl`
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

Relevant code:

- [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)
- [questions/ledger.py](/code/src/course_pipeline/questions/ledger.py)

### Layer 5: Human Inspection and Evaluation

This layer is document-first.

It exists to help a human reviewer answer:

- what was generated
- what was kept
- what was hidden
- what failed
- why a foundational learner question is missing or visible

Main artifacts:

- `docs/inspection_bundle_7`
- `docs/data_pack`
- implementation reports
- backlog documents

## Current Canonical Question Path

The current canonical path for question generation is:

1. standardize raw course YAML
2. extract topics, edges, pedagogy, and frictions
3. generate raw question candidates
4. filter and score candidates
5. apply policy classification and coverage enforcement
6. enforce foundational-entry coverage
7. build ledger rows
8. derive visible and inspection views
9. publish inspection bundles

## Key Project Invariants

The repo has converged on several important invariants.

### Evidence First

Questions must be grounded in course text.

The pipeline should not invent unsupported techniques, workflows, or course
content beyond what the source text reasonably supports.

### Non-Destructive Inspection

A validated question should not silently disappear.

If it is hidden, that hidden state must be represented in artifacts.

### Foundational Anchor Coverage

For foundational anchors, the system now treats plain beginner definitions as
protected questions.

Examples:

- `What is ARIMA?`
- `What is exponential smoothing?`
- `What is the Ljung-Box test?`
- `What is trend?`
- `What is seasonality?`

### Ledger As Source Of Truth

The V6 ledger is the authoritative artifact for generated questions.

Derived views may change, but they should always be reproducible from the
ledger.

### Strict Coverage Failure

In strict mode, a run fails when a foundational anchor lacks a visible
canonical plain definition question.

## Current Data Products

The main persisted data products are:

- standardized course exports
- question-generation candidate runs
- policy runs
- ledger runs
- inspection bundles
- packaged final deliverables

Run artifacts live under:

- [data/pipeline_runs](/code/data/pipeline_runs)

## CLI Surface

The project is operated through the Typer CLI in
[cli.py](/code/src/course_pipeline/cli.py).

Important commands:

- `init-db`
- `ingest`
- `export-standardized`
- `run-question-gen-v3`
- `run-question-gen-v4-policy`
- `run-question-gen-v4-1-policy`
- `run-question-ledger-v6`
- bundle-building commands for inspection

## Storage Model

The repository uses both file-based artifacts and a Postgres-backed storage
layer.

Operationally:

- file artifacts are the main inspection surface
- database tables support persistence and queryability
- run directories are the main bounded-evaluation unit

## Inspection Bundle Conventions

Inspection bundles are intentionally redundant and human-readable.

They should answer:

- what questions exist for a course
- what attributes each question has
- what course content the questions were derived from
- what the final anchor coverage status is

The latest inspection direction favors:

- all questions with attributes
- visible vs hidden state
- source content in the same file
- explicit coverage outcomes

## Current Status

The project has materially improved from earlier versions.

What is now strong:

- deterministic course normalization
- explicit topic / friction extraction
- ledger-first question inspection
- protected beginner-definition handling for foundational anchors
- strict coverage failure for missing foundational entry questions

What is still weak or incomplete:

- alias grouping is limited
- cache-servable output is still underproduced
- some richer procedural and diagnostic questions remain awkward
- foundational-anchor detection is heuristic, not ontology-backed
- many docs describe intermediate proposals, not only the current state

## Recommended Canonical Docs

For current repo understanding, use these as the primary references:

- [project_spec.md](/code/docs/project_spec.md)
- [question_generation_algorithm_spec.md](/code/docs/question_generation_algorithm_spec.md)
- [refactor_naming_map.md](/code/docs/refactor_naming_map.md)
- [pipeline_memo.md](/code/docs/pipeline_memo.md)
- [current_architecture_and_production_options.md](/code/docs/current_architecture_and_production_options.md)

## Definition Of Done For This Project Phase

This phase is successful when:

1. foundational beginner questions are generated and visible for core anchors
2. every generated question is represented in the ledger
3. hidden questions remain inspectable
4. coverage failures are explicit rather than silent
5. bundle docs make diagnosis fast for a human reviewer
