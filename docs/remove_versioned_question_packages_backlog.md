# Remove Versioned Question Packages Backlog

## Goal

Remove these legacy implementation packages from the live source tree:

- `src/course_pipeline/question_gen_v3`
- `src/course_pipeline/question_gen_v4`
- `src/course_pipeline/question_gen_v4_1`

Status: completed.

End state reached:

- the active pipeline runs entirely through `course_pipeline.questions.*`
- tests target the stable package names
- no runtime code depends on the removed versioned packages
- the old package names either disappear or remain only as short-lived shims
  during a tightly controlled transition

## Current State

What is already true:

- runtime orchestration now imports through:
  - `course_pipeline.questions.candidates`
  - `course_pipeline.questions.policy`
  - `course_pipeline.questions.ledger`
  - `course_pipeline.questions.inspection`
- active tests now mostly target the stable package surface
- candidate-stage code has been copied into `questions/candidates/`
- policy-stage code has been copied into `questions/policy/`

What is still true:

- the removed package names still appear in some historical docs and reports
- the CLI and some report filenames still retain historical version labels

## Removal Principles

1. Remove runtime dependency first.
2. Preserve behavior until replacement is proven by tests.
3. Delete whole packages only after import scans are clean.
4. Prefer explicit temporary shims over silent breakage.
5. Commit each removal slice independently.

## Executed Slices

### Slice 1: Freeze Deletion Safety

Objective:

- make package deletion testable and low-risk

Tasks:

- add one import-surface regression test that fails if active runtime modules
  import:
  - `course_pipeline.question_gen_v3`
  - `course_pipeline.question_gen_v4`
  - `course_pipeline.question_gen_v4_1`
- add one repo scan test or script for the same rule, scoped to active source
  and active tests
- classify remaining references into:
  - active runtime
  - active tests
  - compatibility shims
  - dead code

Acceptance criteria:

- the repo has an explicit red/green signal for whether deletion is safe

### Slice 2: Remove Remaining Runtime Imports From `question_gen_v3`

Objective:

- make `question_gen_v3` unused by live runtime

Tasks:

- scan all source files for imports from `course_pipeline.question_gen_v3`
- replace remaining imports with:
  - `course_pipeline.questions.candidates.*`
  - or `course_pipeline.questions.inspection`
- especially re-check:
  - `question_ledger_v6/*`
  - any old helper modules
  - any lingering wrapper files

Acceptance criteria:

- no active runtime file imports `course_pipeline.question_gen_v3`

### Slice 3: Remove Remaining Runtime Imports From `question_gen_v4`

Objective:

- make `question_gen_v4` unused by live runtime

Tasks:

- move any remaining live code from V4 into `questions/policy/`
- replace imports of:
  - `policy_models`
  - `build_cache_entries`
  - `canonicalize`
  - `policy_score`
  - `policy_metrics`
  - `tag_families`
  - `serveability_gate`
  with stable package imports

Acceptance criteria:

- no active runtime file imports `course_pipeline.question_gen_v4`

### Slice 4: Remove Remaining Runtime Imports From `question_gen_v4_1`

Objective:

- make `question_gen_v4_1` unused by live runtime

Tasks:

- move any remaining live code from V4.1 into `questions/policy/`
- replace imports of:
  - `anchors`
  - `coverage`
  - `policy_models`
  - `run_v4_1_policy`
  - `config`
  with stable package imports

Acceptance criteria:

- no active runtime file imports `course_pipeline.question_gen_v4_1`

### Slice 5: Move Remaining Legacy Tests To Stable Imports

Objective:

- stop reinforcing the old package names in the test suite

Tasks:

- scan all tests for versioned package imports
- replace those imports with stable package imports where the tests are still
  meant to validate active behavior
- remove tests that only exist to validate deleted package wiring

Acceptance criteria:

- active test suite does not import the versioned packages

### Slice 6: Compatibility Decision

Objective:

- make deletion intentional instead of accidental

Options:

1. short-lived compatibility shims
2. immediate hard removal

Recommended default:

- use short-lived compatibility shims only if you still need to protect
  external imports or transitional docs

Tasks if using shims:

- replace package contents with tiny re-export modules
- add clear deprecation comments
- keep them for one bounded cleanup pass only

Tasks if not using shims:

- delete the packages directly once internal imports are clean

Acceptance criteria:

- there is an explicit repo decision for compatibility behavior

### Slice 7: Delete `question_gen_v3`

Objective:

- remove the package after import cleanup

Tasks:

- delete `src/course_pipeline/question_gen_v3/`
- rerun the active suite
- fix any missed references

Acceptance criteria:

- repo builds and tests pass without `question_gen_v3`

### Slice 8: Delete `question_gen_v4`

Objective:

- remove the package after import cleanup

Tasks:

- delete `src/course_pipeline/question_gen_v4/`
- rerun the active suite
- fix any missed references

Acceptance criteria:

- repo builds and tests pass without `question_gen_v4`

### Slice 9: Delete `question_gen_v4_1`

Objective:

- remove the package after import cleanup

Tasks:

- delete `src/course_pipeline/question_gen_v4_1/`
- rerun the active suite
- fix any missed references

Acceptance criteria:

- repo builds and tests pass without `question_gen_v4_1`

### Slice 10: Clean Docs And Naming Residue

Objective:

- remove architectural references that imply the versioned packages are still
  first-class

Tasks:

- update:
  - `project_spec.md`
  - `current_architecture_and_production_options.md`
  - `question_generation_algorithm_spec.md`
  - `refactor_naming_map.md`
- remove obsolete mentions from implementation reports if they are presented as
  current

Acceptance criteria:

- docs describe only the stable package architecture as current

### Phase 11: Final Dead-Code Sweep

Objective:

- ensure the deletion leaves no orphaned helpers or configs behind

Tasks:

- remove old config files that are no longer referenced
- remove duplicated helper code if stable packages now own it
- scan for dead imports and unused functions
- run compile/import checks

Acceptance criteria:

- no dead package references remain in source or active tests

## Recommended Execution Order

1. Phase 1
2. Phase 2
3. Phase 3
4. Phase 4
5. Phase 5
6. Phase 6
7. Phase 7
8. Phase 8
9. Phase 9
10. Phase 10
11. Phase 11

## Recommended Gate Per Slice

After each slice, run:

```bash
pytest -q tests/test_cli_contract.py tests/test_pipeline_smoke.py tests/test_refactor_baseline_outputs.py tests/test_foundational_entry_questions.py tests/test_prefect_pipeline_flow.py tests/test_prefect_pipeline_models.py tests/test_question_ledger_v6_basics.py tests/test_question_ledger_v6_views.py tests/test_question_ledger_v6_run_helpers.py
```

## Done Definition

This effort is done when all of the following are true:

- `question_gen_v3` is gone
- `question_gen_v4` is gone
- `question_gen_v4_1` is gone
- active runtime imports only stable package names
- active tests import only stable package names
- docs describe the stable package architecture as the current system
