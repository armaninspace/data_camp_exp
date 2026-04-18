# Ref Data Promotion Backlog

## Goal

Keep immutable run outputs under `data/pipeline_runs/<run_id>/`, and add an
accumulative promoted reference dataset under `data/ref/current/`.

Key rules:

- only `prod` runs may update `ref/current`
- `dev` and `test` runs must never mutate reference data
- partial runs must merge by `course_id`
- untouched courses must remain in `ref/current`
- aggregate reference artifacts must be rebuilt deterministically

## Recommended Layout

```text
data/
  pipeline_runs/
    <run_id>/
      ...
  ref/
    current/
      by_course/
        <course_id>/
          course.json
          chapters.json
          all_questions.jsonl
          visible_curated.jsonl
          cache_servable.jsonl
          aliases.jsonl
          anchors_summary.json
          inspection_report.md
          inspection_bundle.md
      aggregate/
        courses.jsonl
        chapters.jsonl
        all_questions.jsonl
        visible_curated.jsonl
        cache_servable.jsonl
        aliases.jsonl
        anchors_summary.json
        inspection_bundle/
      final_deliverables/
        all_questions.jsonl
      ref_state.json
    promotions/
      <run_id>.json
```

## Slices

### Slice 1: Backlog And Gating Model

- add a backlog doc
- define `run_mode = dev | test | prod`
- define `ref_root` resolution
- define promotion gating in the Prefect flow

Acceptance:

- design is explicit
- promotion is blocked for non-`prod` runs

### Slice 2: Promotion Models And Context

- add `run_mode`, `promote_ref`, and `ref_root` to Prefect config/context
- include ref-related metadata in the run manifest

Acceptance:

- run manifests show whether a run was eligible for promotion

### Slice 3: Ref Promotion Implementation

- add a promotion module that writes per-course reference files
- replace touched `course_id`s only
- rebuild aggregate reference files from `by_course/`
- write `ref_state.json`
- write `promotions/<run_id>.json`

Acceptance:

- promoting a subset run accumulates into existing reference data

### Slice 4: Prefect Flow Integration

- add a promotion task after successful bundle rendering
- add a stage summary for promotion
- include promoted artifact paths in the run manifest

Acceptance:

- `prod` flow runs update `data/ref/current`
- `dev` and `test` runs skip promotion cleanly

### Slice 5: Tests

- test config/context defaults and gating
- test `prod` promotion creates reference data
- test `dev`/`test` runs do not promote
- test repeated subset promotions accumulate by `course_id`

Acceptance:

- reference promotion behavior is covered by unit/integration tests
