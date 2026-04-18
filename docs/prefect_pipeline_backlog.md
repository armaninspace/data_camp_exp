# Prefect Pipeline Backlog

## Goal

Wrap the current question-generation path in a Prefect 3 orchestration layer
without changing the core domain behavior:

`raw YAML -> normalized course -> V3 generation -> V4.1 policy -> V6 ledger -> inspection bundle`

## Slice 1: Scaffolding

- Add Prefect dependency and project entry points.
- Create `src/course_pipeline/prefect_pipeline/`.
- Implement typed models:
  - `RunConfig`
  - `RunContext`
  - `StageSummary`
  - `RunResult`
- Implement run context, manifest, artifact indexing, and filesystem helpers.
- Add top-level flow skeleton and stub task modules.
- Add operator docs:
  - `docs/prefect_pipeline_bundle.md`
  - `docs/prefect_pipeline_runbook.md`

## Slice 2: Pipeline Wiring

- Wire stage A standardization using current normalization code.
- Wire stage C and D using the active V3 per-course pipeline.
- Wire stage E using the current V4.1 policy path.
- Wire stage F and G using the current V6 ledger path.
- Wire stage H inspection bundle rendering using the current review bundle path.
- Emit run manifest and Prefect markdown artifacts.
- Add CLI and script entry points for local execution.

## Slice 3: Tests and Smoke Run

- Add unit tests for config, context, manifest, and artifact index logic.
- Add bounded integration test for successful Prefect flow execution.
- Add strict-mode blocking test using a patched failure fixture.
- Run a smoke test on the real `24491` course.
- Publish the refreshed inspection bundle under `docs/inspection_bundle_7`.

## Definition of Done

- Local developer run works from `scripts/run_prefect_pipeline.py`.
- Prefect flow writes stage-separated outputs and `run_manifest.json`.
- Strict mode blocks on policy failures and records the blocking reason.
- `all_questions.jsonl`, derived views, and inspection bundle are produced.
- Tests pass.
- Smoke run completes and inspection bundle is published.
