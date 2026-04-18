# Prefect Pipeline Runbook

## Local run

```bash
PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS=120 \
python scripts/run_prefect_pipeline.py \
  --input-root data/classcentral-datacamp-yaml \
  --output-root data/pipeline_runs \
  --strict-mode true \
  --max-courses 1 \
  --course-id 24491
```

If Prefect's temporary local API server starts slowly in your environment, keep
the `PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS=120` prefix.

## Phase 1 notes

- The current implementation creates the run root and manifest.
- Stage wiring for standardization, semantics, policy, ledger, and bundles is
  added in the next slice.

## Future deployment path

- create a Prefect work pool named `process`
- register a deployment
- start a process worker bound to that pool
