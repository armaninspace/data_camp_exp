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

The project currently has two semantic tracks:

1. learning-outcome extraction
2. question generation and ledgering

The question-generation track is the more active one and is the basis of the
latest inspection bundles.

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

### Layer 2: Learning-Outcome Extraction

This layer generates cited course-learning claims from normalized course data.

Responsibilities:

- infer likely learning outcomes
- attach citations to source fields
- persist per-course extraction outputs
- support inspection of claim coverage

Main artifacts:

- `learning_outcomes.jsonl`
- `learning_outcomes_yaml/<course_id>.yaml`

Relevant code:

- [learning.py](/code/src/course_pipeline/learning.py)
- [inspect_learning.py](/code/src/course_pipeline/inspect_learning.py)

### Layer 3: Question Generation

This layer generates learner-question candidates from course content.

It currently exists in several generations:

- `question_gen_v2`
- `question_gen_v3`
- `question_gen_v4`
- `question_gen_v4_1`

The currently meaningful path is:

`normalized course -> V3 candidates -> V4/V4.1 policy -> V6 ledger`

Relevant code:

- [question_gen_v3](/code/src/course_pipeline/question_gen_v3)
- [question_gen_v4](/code/src/course_pipeline/question_gen_v4)
- [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)

### Layer 4: Ledger and Inspection

This layer consolidates all generated questions into one normalized ledger.

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

### Layer 5: Human Inspection and Evaluation

This layer is document-first.

It exists to help a human reviewer answer:

- what was generated
- what was kept
- what was hidden
- what failed
- why a foundational learner question is missing or visible

Main artifacts:

- `docs/review_bundle*`
- `docs/inspection_bundle_*`
- implementation reports
- backlog documents

## Current Canonical Question Path

The current canonical path for question generation is:

1. standardize raw course YAML
2. extract V3 topics, edges, pedagogy, and frictions
3. generate V3 raw question candidates
4. filter and score candidates
5. apply V4.1 policy classification
6. enforce foundational-entry coverage
7. build V6 ledger rows
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
- learning outcome runs
- question generation V2/V3/V4/V4.1 runs
- V6 ledger runs
- review bundles
- inspection bundles

Run artifacts live under:

- [data/pipeline_runs](/code/data/pipeline_runs)

## CLI Surface

The project is operated through the Typer CLI in
[cli.py](/code/src/course_pipeline/cli.py).

Important commands:

- `init-db`
- `ingest`
- `export-standardized`
- `run-learning-outcomes`
- `build-question-cache`
- `run-question-gen-v2`
- `run-question-gen-v3`
- `run-question-gen-v4-policy`
- `run-question-gen-v4-1-policy`
- `run-question-ledger-v6`
- bundle-building commands for review and inspection

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
- [pipeline_memo.md](/code/docs/pipeline_memo.md)
- [question_ledger_v6_implementation_report.md](/code/docs/question_ledger_v6_implementation_report.md)

## Definition Of Done For This Project Phase

This phase is successful when:

1. foundational beginner questions are generated and visible for core anchors
2. every generated question is represented in the ledger
3. hidden questions remain inspectable
4. coverage failures are explicit rather than silent
5. bundle docs make diagnosis fast for a human reviewer
