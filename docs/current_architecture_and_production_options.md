# Current Architecture And Production Options

## Purpose

This document describes the current architecture of the project as it exists in
the repository today.

It also includes an appendix with technology options that would make the system
more production-grade.

This is a companion to:

- [project_spec.md](/code/docs/project_spec.md)
- [question_generation_algorithm_spec.md](/code/docs/question_generation_algorithm_spec.md)
- [pipeline_memo.md](/code/docs/pipeline_memo.md)

## Current Architecture

The system is currently a file-artifact-heavy pipeline with optional database
persistence and a CLI-first operating model.

The architecture is best understood as seven components:

1. input and normalization
2. semantic extraction
3. question generation
4. policy and coverage enforcement
5. ledger normalization
6. inspection and reporting
7. storage and execution surface

## 1. Input And Normalization

The pipeline starts from raw scraped course YAML.

Input source in practice:

- Class Central / DataCamp YAML files under local data directories

Normalization responsibilities:

- safe parsing
- stable course id recovery
- summary / overview normalization
- syllabus and chapter recovery
- stable `NormalizedCourse` construction

Primary code:

- [normalize.py](/code/src/course_pipeline/normalize.py)
- [schemas.py](/code/src/course_pipeline/schemas.py)
- [pipeline.py](/code/src/course_pipeline/pipeline.py)

Primary artifacts:

- `courses.jsonl`
- `chapters.jsonl`
- standardized course YAML files

## 2. Semantic Extraction

There are two semantic extraction tracks in the repo.

### Learning-outcome extraction

This generates cited learning claims from normalized courses.

Primary code:

- [learning.py](/code/src/course_pipeline/learning.py)
- [inspect_learning.py](/code/src/course_pipeline/inspect_learning.py)

Primary artifacts:

- `learning_outcomes.jsonl`
- `learning_outcomes_yaml/`

### Topic and friction extraction

This is the current substrate for the active question-generation pipeline.

It extracts:

- topics
- edges
- pedagogical profiles
- friction points

Primary code:

- [question_gen_v3/extract_topics.py](/code/src/course_pipeline/question_gen_v3/extract_topics.py)
- [question_gen_v3/extract_edges.py](/code/src/course_pipeline/question_gen_v3/extract_edges.py)
- [question_gen_v3/extract_pedagogy.py](/code/src/course_pipeline/question_gen_v3/extract_pedagogy.py)
- [question_gen_v3/mine_friction.py](/code/src/course_pipeline/question_gen_v3/mine_friction.py)

## 3. Question Generation

The active architecture uses a staged question-generation flow centered on V3.

Core flow:

1. generate raw candidates from topics
2. filter candidates
3. score candidates
4. dedupe candidates
5. pass surviving candidates to policy classification

Primary code:

- [question_gen_v3/generate_candidates.py](/code/src/course_pipeline/question_gen_v3/generate_candidates.py)
- [question_gen_v3/filters.py](/code/src/course_pipeline/question_gen_v3/filters.py)
- [question_gen_v3/score_candidates.py](/code/src/course_pipeline/question_gen_v3/score_candidates.py)
- [question_gen_v3/dedupe.py](/code/src/course_pipeline/question_gen_v3/dedupe.py)
- [question_gen_v3/pipeline.py](/code/src/course_pipeline/question_gen_v3/pipeline.py)

Important current rule:

- foundational beginner-definition questions are generated explicitly via
  [foundational_entry_questions.py](/code/src/course_pipeline/foundational_entry_questions.py)

Examples:

- `What is ARIMA?`
- `What is exponential smoothing?`
- `What is the Ljung-Box test?`

## 4. Policy And Coverage Enforcement

After V3 generation, the repo applies policy classification in V4 / V4.1.

Responsibilities:

- assign delivery buckets
- score serveability
- classify visibility
- detect foundational anchors
- enforce beginner-entry protection
- audit anchor coverage
- fail strict runs when foundational entry coverage is missing

Primary code:

- [question_gen_v4](/code/src/course_pipeline/question_gen_v4)
- [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)

Important logic areas:

- [assign_policy_bucket.py](/code/src/course_pipeline/question_gen_v4/assign_policy_bucket.py)
- [anchors.py](/code/src/course_pipeline/question_gen_v4_1/anchors.py)
- [coverage.py](/code/src/course_pipeline/question_gen_v4_1/coverage.py)
- [run_v4_1_policy.py](/code/src/course_pipeline/question_gen_v4_1/run_v4_1_policy.py)

Key policy outputs:

- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

## 5. Ledger Normalization

The current authoritative architecture is ledger-first.

V6 converts terminal question states into one normalized row per question.

Primary code:

- [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)

Responsibilities:

- represent every generated question in a terminal state
- normalize anchor metadata
- preserve visibility and rejection reasons
- derive inspection views from one source of truth

Primary ledger artifact:

- `all_questions.jsonl`

Derived artifacts:

- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

## 6. Inspection And Reporting

The project is highly document-driven.

Inspection is not incidental. It is a first-class architectural output.

Current inspection surfaces:

- review bundles
- inspection bundles
- per-run reports
- implementation reports
- backlog and requirement docs

Representative directories:

- [docs/review_bundle](/code/docs/review_bundle)
- [docs/review_bundle_v2](/code/docs/review_bundle_v2)
- [docs/inspection_bundle_6](/code/docs/inspection_bundle_6)
- [docs/inspection_bundle_7](/code/docs/inspection_bundle_7)

## 7. Storage And Execution Surface

The project currently uses a hybrid storage model.

### Filesystem artifacts

These are the main operational truth for evaluation runs.

Examples:

- run directories under [data/pipeline_runs](/code/data/pipeline_runs)
- bundle docs under [docs](/code/docs)

### Database persistence

The repo also has a Postgres-backed storage layer for structured persistence.

Primary code:

- [storage.py](/code/src/course_pipeline/storage.py)

The DB is useful for:

- run tracking
- normalized course storage
- learning outcome persistence
- question-cache persistence

### CLI surface

The main operating surface is the Typer CLI:

- [cli.py](/code/src/course_pipeline/cli.py)

This is how runs are created, rebuilt, and inspected.

## Current Architectural Strengths

The current architecture has several strong qualities.

### Traceability

The repo preserves intermediate artifacts well.

A reviewer can inspect:

- inputs
- extracted topics
- generated questions
- hidden reasons
- coverage failures

### Non-destructive visibility

The V6 ledger reduces silent loss of generated questions.

### Strong bounded evaluation workflow

The run-directory model is good for:

- reproducibility
- narrow reruns
- inspection bundles
- debugging policy changes

### Human-review friendliness

The project is unusually strong at producing docs that make failures obvious.

## Current Architectural Weaknesses

The architecture is still not production-grade in several important ways.

### Too artifact-heavy for serving

The current filesystem-centric model is good for analysis but weak for
low-latency application serving.

### Multiple legacy paths remain in repo

The repository still contains several generations of question pipelines.

That is useful historically, but it raises complexity and increases the chance
of confusion about which path is canonical.

### Heuristic-heavy semantics

Topic extraction, foundational-anchor detection, and some policy logic are
heuristic rather than backed by a controlled ontology or robust retrieval
layer.

### Weak service path

`cache_servable` and alias handling remain underdeveloped relative to the
inspection path.

### Limited orchestration model

The system is still closer to a local research pipeline than a resilient
service architecture.

## Current Canonical Runtime Path

For the question-generation side, the current canonical path is:

`raw YAML -> normalized course -> V3 generation -> V4.1 policy -> V6 ledger -> inspection bundle`

This is the path that should be treated as architecturally current.

## Recommended Canonical References

- [project_spec.md](/code/docs/project_spec.md)
- [question_generation_algorithm_spec.md](/code/docs/question_generation_algorithm_spec.md)
- [current_architecture_and_production_options.md](/code/docs/current_architecture_and_production_options.md)

## Appendix: Production-Grade Technology Options

This appendix lists realistic technology options if the project is pushed from
bounded evaluation toward a production system.

These are options, not mandates.

## A. Orchestration And Workflow

### Current state

- local CLI-driven runs
- filesystem artifact chaining

### Production options

- Prefect
- Dagster
- Temporal
- Airflow

### Recommendation

For this project shape, `Prefect` or `Dagster` would be the cleanest upgrade.

Why:

- strong run tracking
- artifact-oriented workflows
- easy local-to-remote migration
- better observability than ad hoc CLI chaining

## B. Storage And Artifact Management

### Current state

- local filesystem for runs
- Postgres for structured persistence

### Production options

- object storage for artifacts: S3, GCS, or R2
- Postgres as the primary metadata database
- optional warehouse layer: BigQuery, Snowflake, or ClickHouse for analytics

### Recommendation

Use:

- Postgres for core metadata and run state
- object storage for run artifacts and inspection exports

This would preserve the repo’s artifact-driven strengths while removing local
filesystem coupling.

## C. API Layer

### Current state

- CLI-first
- minimal web app

### Production options

- FastAPI
- Flask
- Django REST Framework
- Node/Fastify if the serving path moves away from Python

### Recommendation

`FastAPI` is the most natural fit.

Why:

- matches current Python stack
- easy schema integration with Pydantic models
- strong compatibility with async job polling and internal admin tooling

## D. Queueing And Background Execution

### Current state

- synchronous run commands

### Production options

- Celery + Redis
- RQ
- Dramatiq
- Temporal workers
- managed queue systems such as SQS or Pub/Sub

### Recommendation

If keeping a simple Python architecture:

- `Celery + Redis` or `Dramatiq + Redis`

If aiming for stronger workflow guarantees:

- `Temporal`

## E. Search, Retrieval, And Serving

### Current state

- ledger artifacts
- minimal cache-serving path

### Production options

- Postgres full-text and trigram search
- Elasticsearch / OpenSearch
- Meilisearch
- vector DB only if retrieval genuinely requires semantic search

### Recommendation

Start with Postgres:

- trigram similarity
- full-text indexes
- structured filters over ledger rows

Only add a vector store if exact and fuzzy lexical matching proves
insufficient.

## F. Canonical Content Store

### Current state

- question ledger in JSONL files

### Production options

- normalize ledger rows into Postgres tables
- materialized views for visible, hidden, cache-servable, and coverage states
- append-only event table for policy transitions

### Recommendation

Promote the V6 ledger into first-class relational tables.

Suggested core tables:

- `question_ledger`
- `question_anchor`
- `question_delivery_decision`
- `question_source_ref`
- `run_artifact`

This would make the current architecture operationally stronger without
changing its conceptual model.

## G. Validation And Quality Gates

### Current state

- unit tests
- bounded reruns
- inspection bundles

### Production options

- Great Expectations style data-quality checks
- contract tests around schema invariants
- regression fixtures per representative course family
- CI gating on coverage and foundational-entry invariants

### Recommendation

Add CI gates for:

- foundational visible-entry coverage
- ledger completeness
- no hidden required-entry question due solely to low distinctiveness
- stable schema shape for emitted artifacts

## H. Observability

### Current state

- file reports
- implementation notes

### Production options

- structured JSON logging
- OpenTelemetry
- Sentry
- Prometheus / Grafana
- run dashboards in Dagster or Prefect

### Recommendation

At minimum:

- structured run logs
- per-stage metrics
- failure reason aggregation

Ideal production setup:

- OpenTelemetry traces
- Prometheus metrics
- Sentry for exceptions

## I. LLM Integration

### Current state

- direct model calls from Python code
- bounded evaluation usage

### Production options

- explicit model gateway wrapper
- prompt version registry
- response caching
- eval datasets and replay harnesses

### Recommendation

Introduce an internal LLM client abstraction with:

- prompt version ids
- model version ids
- response logging
- retry policy
- timeout policy
- deterministic evaluation mode

## J. Frontend / Review UX

### Current state

- markdown bundles
- lightweight static web app

### Production options

- Next.js review UI
- React admin app
- internal analyst dashboard over Postgres-backed APIs

### Recommendation

If inspection remains central, build a proper review UI over the ledger:

- course view
- anchor view
- question view
- hidden reason filters
- run-to-run comparison

This would be much more valuable than adding a consumer-facing UI early.

## K. Security And Operational Hygiene

### Current state

- local secrets and direct env use

### Production options

- secret manager integration
- role-based DB access
- isolated worker credentials
- artifact bucket IAM policies

### Recommendation

Use:

- secret manager for API keys
- least-privilege DB roles
- separate dev and production storage buckets

## Suggested Production Stack

If the goal is a pragmatic production upgrade while preserving the current
Python architecture, a good stack would be:

- FastAPI
- Postgres
- S3-compatible artifact storage
- Prefect or Dagster
- Redis for short-lived queue/cache needs
- OpenTelemetry + Prometheus + Sentry
- React or Next.js internal review UI

If the goal is stronger workflow durability and multi-stage orchestration:

- FastAPI
- Postgres
- S3-compatible storage
- Temporal
- dedicated workers
- internal review UI over the ledger

## Bottom Line

The current architecture is strong for bounded evaluation and inspection.

To make it production-grade, the most important upgrades are not better prompt
tricks. They are:

- workflow orchestration
- first-class ledger storage
- stronger serving/query infrastructure
- observability
- CI-enforced invariants
- an internal review UI over the ledger
