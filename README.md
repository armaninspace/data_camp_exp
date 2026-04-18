# Course Standardization Pipeline

Deterministic ingestion and standardization pipeline for the Class Central
DataCamp YAML corpus in [data/classcentral-datacamp-yaml](/code/data/classcentral-datacamp-yaml).

## What it does

- Parses course YAML safely.
- Normalizes course metadata into a typed schema.
- Recovers chapters from `syllabus` or infers them from `overview`.
- Stores normalized courses and chapters in PostgreSQL.
- Exports standardized course YAML and JSONL artifacts per run.
- Supports a bounded, citation-backed learning-outcome extraction pass.
- Supports a bounded traceable question-cache generation layer on top of
  learning outcomes.
- Supports a bounded learner-centered candidate question generation V2 pass.

## What it does not do

- No topic graph construction.
- No question generation.
- No learner-performance prediction.
- No embedding-based matcher yet.

## Setup

```bash
pip install -e .
```

Environment defaults are read from [data/.env](/code/data/.env).

Important variables:

```bash
DATABASE_URL=postgresql+psycopg://agent@127.0.0.1:55432/course_pipeline
PIPELINE_OUTPUT_ROOT=/code/data/pipeline_runs
```

## Local PostgreSQL

```bash
scripts/start_local_postgres.sh
```

## Run

Initialize the schema:

```bash
course-pipeline init-db
```

Ingest normalized records into PostgreSQL:

```bash
course-pipeline ingest data/classcentral-datacamp-yaml
```

Export standardized artifacts:

```bash
course-pipeline export-standardized data/classcentral-datacamp-yaml
```

Run a bounded cited learning-outcome pass:

```bash
course-pipeline run-learning-outcomes data/classcentral-datacamp-yaml --limit 5
```

Inspect a learning-outcome run:

```bash
course-pipeline inspect-learning-run <run_id>
```

Build a bounded question-cache run from a learning-outcomes run:

```bash
course-pipeline build-question-cache <learning_run_id> --limit 1
```

Run the learner-centered question generation V2 pass:

```bash
course-pipeline run-question-gen-v2 data/classcentral-datacamp-yaml --course-ids 24491,24593,24594
```

Build per-course review docs with grounded Q/A pairs:

```bash
course-pipeline build-question-gen-review-bundle <question_gen_v2_run_id> --course-ids 24491,24593,24594
```

Render question-cache YAML:

```bash
course-pipeline render-question-cache-yaml <question_cache_run_id> --width 80
```

Inspect a question-cache run:

```bash
course-pipeline inspect-question-cache-run <question_cache_run_id>
```

Ask the cache a question:

```bash
course-pipeline ask-question-cache <question_cache_run_id> "How do I create a vector in R?" --course-id 7630
```

Serve the review web app:

```bash
course-pipeline serve-web-app data/classcentral-datacamp-yaml --port 8000
```

## Outputs

Each standardized export is written under:

```text
data/pipeline_runs/<run_id>/
```

Outputs include:

- `courses.jsonl`
- `chapters.jsonl`
- `errors.jsonl`
- `standardized_courses/<course_id>.yaml`

Learning-outcome runs also include:

- `learning_outcomes.jsonl`
- `learning_outcome_errors.jsonl`

Question-cache runs include:

- `claim_question_groups.jsonl`
- `question_group_variations.jsonl`
- `canonical_answers.jsonl`
- `question_cache_errors.jsonl`
- `question_cache_yaml/<course_id>.yaml`

Question-generation V2 runs include:

- `topics.jsonl`
- `learner_friction_candidates.jsonl`
- `candidate_questions.jsonl`
- `question_gen_v2_report.md`
- `review_bundle/<course_id>_<slug>.md` after review-bundle export
