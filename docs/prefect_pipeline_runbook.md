# Prefect Pipeline Runbook

## Local run

```bash
PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS=120 \
python scripts/run_prefect_pipeline.py \
  --input-root data/classcentral-datacamp-yaml \
  --output-root data/pipeline_runs \
  --run-mode prod \
  --strict-mode true \
  --offset 0 \
  --max-courses 1 \
  --course-id 24491
```

If Prefect's temporary local API server starts slowly in your environment, keep
the `PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS=120` prefix.

## Ref promotion

The pipeline now keeps immutable run outputs under:

- `data/pipeline_runs/<run_id>/`

And promotes successful `prod` runs into:

- `data/ref/current/`
- `data/ref/promotions/<run_id>.json`

Promotion behavior:

- `prod` runs update `data/ref/current/`
- `dev` and `test` runs do not update reference data
- partial runs replace only touched `course_id`s and rebuild aggregates
- `--offset` and `--max-courses` let you process deterministic sequential slices
- `--skip-existing-ref-courses` removes any `course_id` already present in `data/ref/current/by_course/` before slicing

Current reference layout:

- `data/ref/current/by_course/<course_id>/`
- `data/ref/current/aggregate/`
- `data/ref/current/final_deliverables/`
- `data/ref/current/ref_state.json`

## Notes

- the flow writes an immutable run manifest to `run_manifest.json`
- the manifest records `selected_course_ids`, `skipped_existing_course_ids`, and `selection_counts`
- the flow writes a promotion manifest for promoted prod runs
- aggregate reference artifacts are rebuilt from per-course reference state
- live review-answer stages write `llm_metering.jsonl` at the run root

## Future deployment path

- create a Prefect work pool named `process`
- register a deployment
- start a process worker bound to that pool
