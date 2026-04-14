# Course Standardization Pipeline

Deterministic ingestion and standardization pipeline for the Class Central
DataCamp YAML corpus in [data/classcentral-datacamp-yaml](/code/data/classcentral-datacamp-yaml).

## What it does

- Parses course YAML safely.
- Normalizes course metadata into a typed schema.
- Recovers chapters from `syllabus` or infers them from `overview`.
- Stores normalized courses and chapters in PostgreSQL.
- Exports standardized course YAML and JSONL artifacts per run.

## What it does not do

- No LLM extraction.
- No topic graph construction.
- No question generation.
- No eval-pack or run-inspection UI.

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
