# Production Refactor Backlog

## Goal

Refactor the source tree so the current question pipeline is production-grade,
elegant, and easier to maintain.

This backlog is specifically intended to remove generational naming such as:

- `question_gen_v3`
- `question_gen_v4`
- `question_gen_v4_1`
- `question_ledger_v6`

and replace it with a coherent domain-driven structure.

The target end state is:

- one canonical pipeline surface
- stable domain names instead of historical version names
- no dead code or stale execution paths
- tests that protect behavior during refactor
- docs that accurately describe the live architecture

## Current Problems

### Naming Drift

The active pipeline is still expressed as historical implementation phases
rather than domain responsibilities.

That makes the code harder to understand because a reader must know project
history to know what each package does.

Examples:

- `question_gen_v3` is really candidate generation
- `question_gen_v4` is really policy classification and serveability
- `question_gen_v4_1` is really anchor coverage and protected-entry policy
- `question_ledger_v6` is really final question ledger assembly

### Split Responsibility

Core responsibilities are spread across too many top-level packages.

The current path is logically:

`normalize -> candidate extraction -> policy -> coverage -> ledger -> inspection`

but the code is organized by version lineage instead of by that flow.

### Stale Documentation

Some docs still describe removed legacy components or outdated CLI commands.

### Incomplete Test Boundaries

There are good targeted tests around ledgering and Prefect flow orchestration,
but the repo still needs better tests for:

- public CLI contract
- end-to-end pipeline behavior
- refactor-safe service boundaries
- dead-code detection at the import surface

## Refactor Principles

1. Preserve behavior before improving internals.
2. Rename by responsibility, not by project history.
3. Keep one canonical pipeline path.
4. Reduce top-level module sprawl.
5. Prefer small adapters over cross-package imports.
6. Move toward explicit domain models and stage contracts.
7. Delete obsolete code promptly once migration is complete.

## Proposed Target Architecture

### Top-Level Shape

Proposed package layout:

```text
src/course_pipeline/
  cli.py
  config.py
  normalize.py
  schemas.py
  storage.py
  utils.py
  pipeline/
    __init__.py
    orchestration.py
    artifacts.py
    inspection.py
  questions/
    __init__.py
    candidates/
      __init__.py
      extraction.py
      pedagogy.py
      friction.py
      generation.py
      filtering.py
      scoring.py
      dedupe.py
      selection.py
      models.py
      config.py
    policy/
      __init__.py
      canonicalize.py
      signals.py
      classification.py
      anchors.py
      coverage.py
      retention.py
      models.py
      config.py
    ledger/
      __init__.py
      build.py
      normalize.py
      models.py
      config.py
    inspection/
      __init__.py
      reports.py
      bundles.py
  orchestration/
    __init__.py
    prefect/
      ...
```

This keeps the current behavior but maps code to responsibilities instead of
historical versions.

## Backlog

### Phase 0: Freeze Current Behavior

Objective:

- establish the current pipeline as the migration baseline

Tasks:

- add a canonical end-to-end fixture for the R time-series sample courses
- snapshot the expected outputs that matter during refactor:
  - visible protected beginner definitions
  - ledger row counts
  - anchor coverage summaries
  - `tracked_topics` behavior
- add a smoke test that exercises the active CLI path without old commands
- add an import-surface test that asserts the live top-level modules import
  cleanly

Acceptance criteria:

- the baseline tests pass before any structural moves
- refactor branches can prove they did not regress core outputs

Recommended tests:

- `tests/test_pipeline_smoke.py`
- `tests/test_cli_contract.py`
- `tests/test_refactor_baseline_outputs.py`

### Phase 1: Define Stable Domain Vocabulary

Objective:

- create the new naming system before moving code

Tasks:

- define canonical internal names for the active stages:
  - candidate extraction
  - candidate generation
  - policy classification
  - anchor coverage
  - question ledger
  - inspection publishing
- add a short naming policy doc
- update the architecture docs to describe the current live system in these
  terms
- explicitly deprecate versioned names in docs

Acceptance criteria:

- every active package has a proposed replacement name
- docs no longer describe removed legacy stages as active

Deliverables:

- `docs/refactor_naming_map.md`
- updated:
  - `docs/project_spec.md`
  - `docs/current_architecture_and_production_options.md`
  - `docs/question_generation_algorithm_spec.md`

### Phase 2: Introduce a Canonical Questions Package

Objective:

- create a new non-versioned home for the active question pipeline

Tasks:

- create `src/course_pipeline/questions/`
- add thin wrapper modules that delegate to current implementation
- define stable public entry points for:
  - candidate generation
  - policy application
  - ledger build
  - inspection bundle generation
- make `pipeline.py` call the new stable package surface instead of importing
  versioned modules directly

Acceptance criteria:

- live runtime flows through stable package imports
- versioned packages are no longer imported by `cli.py`
- tests still pass

Notes:

- this phase should be low-risk because it can start with wrappers
- behavior should remain unchanged

### Phase 3: Move Candidate Logic Out Of `question_gen_v3`

Objective:

- rename and relocate V3 code by responsibility

Tasks:

- move:
  - `extract_topics.py`
  - `extract_edges.py`
  - `extract_pedagogy.py`
  - `mine_friction.py`
  - `generate_candidates.py`
  - `filters.py`
  - `score_candidates.py`
  - `dedupe.py`
  - `select_final.py`
  - `models.py`
  - `config.py`
  into `questions/candidates/`
- rename functions where necessary to reflect domain semantics instead of
  generation numbers
- preserve config compatibility during migration
- delete the old V3 package once all imports are migrated

Acceptance criteria:

- no runtime imports from `question_gen_v3`
- candidate-stage tests pass unchanged

Recommended tests:

- extraction unit tests
- candidate generation unit tests
- dedupe and selection regression tests

### Phase 4: Collapse Policy And Coverage Into One Policy Package

Objective:

- eliminate the awkward split between `question_gen_v4` and
  `question_gen_v4_1`

Tasks:

- move policy logic into `questions/policy/`
- unify:
  - bucket assignment
  - canonicalization
  - serveability
  - anchor detection
  - protected beginner entry enforcement
  - coverage warnings
  - strict coverage failure
- merge config surfaces into one policy config
- replace dual model modules with one stable policy model package

Acceptance criteria:

- no runtime imports from `question_gen_v4` or `question_gen_v4_1`
- one policy entry point exists
- protected-entry behavior is covered by regression tests

Recommended tests:

- `What is ARIMA?` visible and protected
- `What is exponential smoothing?` visible and protected
- `What is the Ljung-Box test?` visible and protected
- trend and seasonality definition coverage
- no required entry hidden solely for low distinctiveness

### Phase 5: Rename Ledger Package By Responsibility

Objective:

- replace `question_ledger_v6` with a stable ledger package

Tasks:

- move ledger code into `questions/ledger/`
- preserve the `all_questions.jsonl` schema contract
- keep `tracked_topics` logic intact
- make ledger build the canonical terminal stage
- remove version references from class names, helpers, reports, and docs

Acceptance criteria:

- no runtime imports from `question_ledger_v6`
- ledger outputs are bitwise stable or intentionally documented when changed

Recommended tests:

- ledger row schema tests
- `tracked_topics` extraction tests
- visible/cache/alias derived-view tests

### Phase 6: Unify Inspection Publishing

Objective:

- move bundle/report generation into one inspection layer

Tasks:

- create `questions/inspection/`
- move report and bundle rendering there
- standardize the inspection bundle contract:
  - course markdown
  - inspection report
  - final deliverables
  - manifest
- ensure inspection docs always show:
  - all questions
  - attributes
  - tracked topics
  - source course content

Acceptance criteria:

- one code path produces the published inspection bundle
- no duplicate bundle builders across old packages

### Phase 7: Simplify Pipeline Entry Points

Objective:

- make the project easier to operate and test

Tasks:

- replace the broad `pipeline.py` grab-bag with explicit orchestration modules
- define one public service per stage
- keep CLI commands thin
- isolate file I/O from pure transformation logic
- ensure Prefect orchestration calls the same service layer as local CLI runs

Acceptance criteria:

- stage logic is testable without filesystem-heavy integration setup
- CLI functions mostly validate args and call services
- Prefect flow reuses the same orchestration functions

### Phase 8: Storage Cleanup

Objective:

- make persistence match the live product instead of historical artifacts

Tasks:

- audit `storage.py` for tables that only exist for deleted legacy flows
- decide whether to:
  - remove obsolete tables entirely
  - keep them but mark them deprecated
- add stable persistence helpers for the current ledger-first model if needed

Acceptance criteria:

- storage layer reflects live architecture
- dead persistence APIs are removed or explicitly deprecated

### Phase 9: Dead-Code Elimination Sweep

Objective:

- remove remaining obsolete modules, configs, and docs after migration

Tasks:

- delete compatibility wrappers once migration is complete
- remove stale config files tied only to versioned packages
- scan for dead imports and orphan helpers
- scan docs for references to removed paths
- remove test files that only target deleted code

Acceptance criteria:

- `rg 'question_gen_v3|question_gen_v4|question_gen_v4_1|question_ledger_v6'`
  only finds migration notes or deprecation docs, not live imports

### Phase 10: Production-Grade Test Matrix

Objective:

- make the refactored pipeline safe to evolve

Tasks:

- add unit tests at the pure-function level
- add stage-level integration tests
- add one end-to-end fixture-based smoke test
- add schema regression tests for:
  - `all_questions.jsonl`
  - inspection bundle structure
  - manifest outputs
- add CLI contract tests for supported commands
- add regression tests for beginner-anchor guarantees
- add coverage thresholds for active packages

Acceptance criteria:

- tests are organized by unit, integration, and smoke layers
- the active pipeline can be refactored without manual inspection-only checks

## Recommended Execution Order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7
9. Phase 8
10. Phase 9
11. Phase 10

## Recommended Done Definition

The refactor should be considered done only when all of the following are true:

- the active code path uses stable domain names rather than historical version
  names
- there is one canonical question pipeline surface
- old versioned packages are gone or fully deprecated and unused
- dead code and stale docs are removed
- the CLI and Prefect flows share the same service layer
- unit, integration, and smoke tests cover the live path
- architecture docs match the actual source tree

## Suggested First Slice

The best first implementation slice is:

1. add baseline smoke and regression tests
2. introduce `src/course_pipeline/questions/` as stable wrappers
3. re-point `pipeline.py` to the stable wrappers

That gives immediate structural improvement without risky behavior changes.
