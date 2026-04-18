# Prefect Pipeline Implementation Bundle for Codex

## 1. Mission

Implement a new Prefect-based orchestration layer for the current question-generation pipeline without changing the project’s core domain invariants.

The new pipeline must preserve the current canonical runtime path:

`raw YAML -> normalized course -> V3 generation -> V4.1 policy -> V6 ledger -> inspection bundle`

The orchestration rewrite should improve:

- run tracking
- reproducibility
- stage isolation
- resumability / rerun ergonomics
- artifact publication
- observability
- readiness for local-to-remote execution

It should **not** rewrite the domain logic on day one. The first goal is to wrap and regularize the current pipeline, not reinvent question generation.

---

## 2. Product and domain constraints

These are non-negotiable and must be preserved by the new Prefect pipeline.

### Core invariants

1. **Evidence first**
   - questions must remain grounded in source course text
   - no unsupported content generation should be introduced by orchestration changes

2. **Ledger as source of truth**
   - every terminal question state must still be represented in the ledger
   - derived outputs are projections of the ledger, not replacements for it

3. **Non-destructive inspection**
   - hidden questions must remain inspectable
   - coverage failures must remain explicit

4. **Foundational entry protection**
   - canonical beginner definition questions for foundational anchors must remain protected
   - no `required_entry=true` question may become hidden solely due to orchestration or batching behavior

5. **Strict coverage failure**
   - strict mode must still fail if a foundational anchor lacks a visible canonical plain definition

### Canonical outputs to preserve

At minimum, the new pipeline must preserve or regenerate these artifacts:

- `courses.jsonl`
- `chapters.jsonl`
- `all_questions.jsonl`
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`
- existing inspection/review bundle outputs

### Scope boundary

The current repo has multiple semantic tracks and legacy generations. The new Prefect pipeline should treat the **question-generation side** as architecturally current.

Do not make learning-outcome extraction the main orchestration spine unless explicitly asked in a later phase.

---

## 3. What to build

Build a new orchestration package that makes the current pipeline runnable as Prefect flows and tasks.

### Primary deliverable

A new package:

```text
src/course_pipeline/prefect_pipeline/
```

This package should provide:

- a clear top-level Prefect flow for the canonical question pipeline
- subflows or tasks for each major stage
- a typed run configuration model
- artifact publishing helpers
- run manifest generation
- retry / timeout policies for stage boundaries
- local filesystem artifact writing for phase 1
- optional hooks for future Postgres / object storage persistence

### Non-goals for first implementation

Do **not** do these unless necessary for the wiring to work:

- large-scale rewrite of V3/V4.1/V6 logic
- full migration from JSONL to relational tables
- full FastAPI service implementation
- full cloud deployment automation
- vector DB adoption
- queue system adoption

---

## 4. Architecture target

### 4.1 New orchestration stance

Use Prefect as the orchestration layer only.

The pipeline should be expressed as:

- **flow** = one logically meaningful orchestration boundary
- **task** = one concrete stage or external side effect
- **artifact** = human-readable progress and summary output in the Prefect UI
- **deployment** = remotely triggerable run definition
- **work pool** = execution environment selector
- **worker** = process that polls a work pool and executes runs when using hybrid execution

### 4.2 Canonical flow graph

Implement this flow graph.

```text
question_generation_pipeline_flow
  -> prepare_run_context_task
  -> standardize_courses_subflow
  -> extract_semantics_subflow
  -> generate_candidates_subflow
  -> apply_policy_subflow
  -> build_ledger_subflow
  -> derive_views_subflow
  -> render_inspection_bundle_subflow
  -> finalize_run_manifest_task
```

### 4.3 Stage boundaries

#### Stage A: Prepare run context

Responsibilities:
- allocate `run_id`
- resolve input source paths
- resolve output root
- load run config
- create run directories
- emit initial manifest

Inputs:
- run config

Outputs:
- `RunContext`

#### Stage B: Standardize courses

Responsibilities:
- parse YAML inputs
- normalize metadata
- recover chapters
- persist normalized course artifacts

Outputs:
- normalized course collection
- `courses.jsonl`
- `chapters.jsonl`
- per-course normalized exports

#### Stage C: Extract semantics

Responsibilities:
- extract topics
- extract edges
- extract pedagogy
- mine friction

Outputs:
- per-course semantic intermediates
- semantic stage manifest / summary

#### Stage D: Generate candidates

Responsibilities:
- generate raw question candidates
- apply candidate filters
- apply scoring
- perform dedupe / canonicalization prep

Outputs:
- raw / filtered / scored candidate artifacts
- candidate summary metrics

#### Stage E: Apply policy

Responsibilities:
- detect foundational anchors
- assign delivery buckets
- enforce protected entry promotion
- run coverage audit
- fail strict runs when necessary

Outputs:
- policy decision artifacts
- coverage warnings
- failure status if strict mode blocks run

#### Stage F: Build ledger

Responsibilities:
- build terminal ledger rows
- preserve hidden/rejected states
- normalize output rows

Outputs:
- `all_questions.jsonl`
- ledger stage metrics

#### Stage G: Derive views

Responsibilities:
- derive visible curated output
- derive cache-servable output
- derive aliases
- derive anchor summary
- derive inspection report source material

Outputs:
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

#### Stage H: Render inspection bundle

Responsibilities:
- materialize human-readable bundle files
- ensure bundle answers the inspection questions already expected by the repo

Outputs:
- bundle directory
- bundle index / summary

#### Stage I: Finalize run manifest

Responsibilities:
- collect artifact paths
- stage durations
- row counts
- warning counts
- final status

Outputs:
- `run_manifest.json`
- final Prefect markdown artifact

---

## 5. File layout to implement

Create this structure.

```text
src/course_pipeline/prefect_pipeline/
  __init__.py
  config.py
  context.py
  artifacts.py
  logging.py
  manifests.py
  states.py
  flows.py
  deployments.py
  tasks/
    __init__.py
    prepare.py
    standardize.py
    semantics.py
    candidates.py
    policy.py
    ledger.py
    views.py
    bundles.py
    finalize.py
  adapters/
    __init__.py
    filesystem.py
    db.py
    llm.py
  models/
    __init__.py
    run_config.py
    run_context.py
    run_result.py
    stage_summary.py
```

Also add these top-level project files if missing:

```text
prefect.yaml                # optional if Codex prefers deployment yaml
prefect.toml                # project-level Prefect config if useful
scripts/
  run_prefect_pipeline.py
  register_prefect_deployments.py
```

And add documentation:

```text
docs/
  prefect_pipeline_bundle.md
  prefect_pipeline_runbook.md
```

---

## 6. Required models

Implement typed config and context models with Pydantic.

### 6.1 RunConfig

```python
class RunConfig(BaseModel):
    run_label: str | None = None
    input_root: Path
    output_root: Path
    standardized_output_subdir: str = "standardized"
    semantic_output_subdir: str = "semantics"
    candidate_output_subdir: str = "candidates"
    policy_output_subdir: str = "policy"
    ledger_output_subdir: str = "ledger"
    bundle_output_subdir: str = "inspection_bundle"
    strict_mode: bool = True
    max_courses: int | None = None
    course_ids: list[str] | None = None
    overwrite_existing: bool = False
    persist_to_db: bool = False
    publish_prefect_artifacts: bool = True
    fail_fast: bool = False
    log_level: str = "INFO"
    model_profile: str = "default"
    tags: list[str] = Field(default_factory=list)
```

### 6.2 RunContext

```python
class RunContext(BaseModel):
    run_id: str
    started_at: datetime
    input_root: Path
    output_root: Path
    run_root: Path
    standardized_dir: Path
    semantics_dir: Path
    candidates_dir: Path
    policy_dir: Path
    ledger_dir: Path
    bundle_dir: Path
    manifest_path: Path
    strict_mode: bool
    persist_to_db: bool
    model_profile: str
    tags: list[str]
```

### 6.3 StageSummary

```python
class StageSummary(BaseModel):
    stage_name: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    input_count: int | None = None
    output_count: int | None = None
    warnings: list[str] = Field(default_factory=list)
    artifact_paths: list[str] = Field(default_factory=list)
    metrics: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
```

### 6.4 RunResult

```python
class RunResult(BaseModel):
    run_id: str
    status: Literal["completed", "failed"]
    manifest_path: Path
    stage_summaries: list[StageSummary]
    artifact_paths: list[str]
    warning_count: int
    blocking_failure: str | None = None
```

---

## 7. Core implementation rules

### Rule 1: Wrap existing logic before rewriting it

Where the repo already has working code for:

- normalization
- topic extraction
- edge extraction
- pedagogy extraction
- friction mining
- candidate generation
- filtering
- scoring
- dedupe
- V4.1 policy
- V6 ledger
- bundle rendering

call that logic from Prefect tasks or thin adapters first.

Do not fork behavior unless the current interfaces make wrapping impossible.

### Rule 2: One task per meaningful failure boundary

Tasks should be coarse enough to give useful retries and logs, but not so coarse that one failure reruns the whole world.

Good task boundaries:
- standardize a batch of courses
- extract semantics for one course
- generate candidates for one course
- apply policy for one course
- build ledger for one course or run
- derive run-level views

### Rule 3: Preserve existing artifacts

Phase 1 success means users can still inspect familiar artifacts on disk.

Even if Prefect artifacts are added, the filesystem artifacts remain required.

### Rule 4: Make stage outputs explicit

Every stage should return a typed result or a typed reference to on-disk artifacts.

Avoid implicit coupling through globals or environment state.

### Rule 5: Strict mode must be enforced by orchestration

If coverage audit yields a blocking failure in strict mode, the flow should enter a failed state with a clear error message.

### Rule 6: Prefer idempotent writes where possible

If a run is retried, task outputs should either:
- reuse the same deterministic file path and overwrite safely, or
- write atomically to temp files then move into place

---

## 8. Prefect-specific implementation guidance

### 8.1 Use current Prefect concepts

Use current Prefect 3 terminology and APIs.

Implement flows as `@flow` decorated Python functions.
Implement stage logic as `@task` decorated functions where it adds retry, timeout, caching, or observability value.

### 8.2 Work pool assumption

Assume the initial deployment target is a **hybrid process work pool** for local or VM-based execution.

Phase 1 expectation:
- local development can run flows directly as Python
- deployments can be registered to a Prefect work pool
- a process worker can execute them in a dev environment

Do not assume Kubernetes or ECS in phase 1.

### 8.3 Blocks

Use Prefect blocks for reusable typed configuration only where they add real value, especially:
- database credentials
- object storage credentials in future phases
- optional model provider configuration

Do not over-block everything.

Use ordinary flow parameters and Pydantic config for per-run settings that vary often.

### 8.4 Prefect artifacts

Emit Prefect markdown or table artifacts for:
- run summary
- per-stage summary
- coverage audit summary
- final artifact index

But do not rely on Prefect artifacts as the only review surface.

### 8.5 Results

Do not overuse Prefect result persistence for large domain payloads.

Preferred approach:
- write large structured outputs to the run directory on disk
- return small typed references / summaries from tasks
- optionally add Prefect result storage later if remote execution requires it

---

## 9. Recommended flow and task signatures

These are recommendations, not exact required signatures.

### Top-level flow

```python
@flow(name="question-generation-pipeline", log_prints=True)
def question_generation_pipeline_flow(config: RunConfig) -> RunResult:
    ...
```

### Prepare

```python
@task(retries=0)
def prepare_run_context(config: RunConfig) -> RunContext:
    ...
```

### Standardization

```python
@flow(name="standardize-courses")
def standardize_courses_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Semantics

```python
@flow(name="extract-semantics")
def extract_semantics_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Candidate generation

```python
@flow(name="generate-candidates")
def generate_candidates_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Policy

```python
@flow(name="apply-policy")
def apply_policy_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Ledger

```python
@flow(name="build-ledger")
def build_ledger_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Views

```python
@flow(name="derive-ledger-views")
def derive_views_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Bundle rendering

```python
@flow(name="render-inspection-bundle")
def render_inspection_bundle_flow(context: RunContext, config: RunConfig) -> StageSummary:
    ...
```

### Finalize

```python
@task
def finalize_run_manifest(context: RunContext, stage_summaries: list[StageSummary]) -> RunResult:
    ...
```

---

## 10. Execution model

### 10.1 Phase 1 execution

Support two execution modes.

#### Mode A: local direct execution

Used by developers.

```bash
python scripts/run_prefect_pipeline.py --input-root ... --output-root ...
```

#### Mode B: Prefect deployment execution

Used for scheduled or remotely triggered runs.

Example outcome:
- deployment registered in Prefect
- assigned to a `process` work pool
- worker started locally or on a dev VM

### 10.2 Concurrency

Be conservative initially.

Suggested initial behavior:
- standardization can batch across all selected courses
- per-course semantic extraction can run concurrently up to a configurable limit
- per-course candidate generation can run concurrently up to a configurable limit
- policy may run per-course or batched if current code structure requires it
- view derivation and bundle rendering run serially at the end

Expose concurrency controls in config or task runners only if they are easy to reason about.

### 10.3 Failure strategy

- fail the whole flow if strict coverage rules block completion
- otherwise record per-course failures and continue when safe
- summarize partial failures in manifest and Prefect artifacts

---

## 11. Artifact contract

Every run must create a stable run root like:

```text
<output_root>/<run_id>/
```

Within it create:

```text
run_manifest.json
standardized/
semantics/
candidates/
policy/
ledger/
inspection_bundle/
logs/
```

### Required manifest fields

```json
{
  "run_id": "...",
  "status": "completed|failed",
  "started_at": "...",
  "finished_at": "...",
  "strict_mode": true,
  "input_root": "...",
  "output_root": "...",
  "stage_summaries": [...],
  "artifact_index": [...],
  "warning_count": 0,
  "blocking_failure": null,
  "git_commit": "optional",
  "model_profile": "default"
}
```

### Artifact indexing

Manifest must include a machine-readable artifact index with:
- artifact type
- relative path
- stage
- row count if known
- content type

---

## 12. Compatibility layer with existing code

Implement thin adapters around current modules.

### 12.1 Standardization adapter

Wrap existing standardization code from:
- `normalize.py`
- `schemas.py`
- `pipeline.py`

Desired adapter API:

```python
def run_standardization(input_root: Path, output_dir: Path, config: RunConfig) -> StandardizationResult:
    ...
```

### 12.2 Semantics adapter

Wrap current active V3 semantic extractors:
- `extract_topics.py`
- `extract_edges.py`
- `extract_pedagogy.py`
- `mine_friction.py`

Desired adapter API:

```python
def run_semantics_for_course(course_path: Path, output_dir: Path, config: RunConfig) -> SemanticExtractionResult:
    ...
```

### 12.3 Candidate adapter

Wrap:
- `generate_candidates.py`
- `filters.py`
- `score_candidates.py`
- `dedupe.py`

Desired adapter API:

```python
def run_candidate_generation_for_course(semantic_inputs: SemanticExtractionResult, output_dir: Path, config: RunConfig) -> CandidateGenerationResult:
    ...
```

### 12.4 Policy adapter

Wrap current policy path:
- `question_gen_v4`
- `question_gen_v4_1`

Desired adapter API:

```python
def run_policy_for_course(candidate_result: CandidateGenerationResult, output_dir: Path, config: RunConfig) -> PolicyResult:
    ...
```

### 12.5 Ledger adapter

Wrap current V6 ledger code:
- `question_ledger_v6`

Desired adapter API:

```python
def build_ledger(policy_results: list[PolicyResult], output_dir: Path, config: RunConfig) -> LedgerResult:
    ...
```

### 12.6 Bundle adapter

Wrap existing inspection bundle rendering.

Desired adapter API:

```python
def render_inspection_bundle(context: RunContext, ledger_result: LedgerResult, output_dir: Path, config: RunConfig) -> BundleResult:
    ...
```

---

## 13. Logging and observability

### 13.1 Logging requirements

Implement structured logging with enough detail to answer:
- what stage ran
- for which run
- for which course if applicable
- how many records were consumed and emitted
- what warning or failure reason occurred

Every log line should include at least:
- `run_id`
- `stage`
- `course_id` when relevant

### 13.2 Prefect artifacts to emit

Emit these human-readable artifacts in the Prefect UI:

1. **Run overview**
   - run id
   - selected course count
   - strict mode
   - output root

2. **Stage table**
   - stage name
   - status
   - duration
   - output count
   - warning count

3. **Coverage summary**
   - foundational anchors examined
   - missing visible entry count
   - only-hidden count
   - alias-only count

4. **Artifact index**
   - links or paths to major outputs

### 13.3 Error reporting

On failure, include:
- precise failing stage
- failing course if relevant
- blocking invariant if any
- path to partial artifacts that were still produced

---

## 14. CLI and developer ergonomics

Implement a script that accepts at least:

```bash
python scripts/run_prefect_pipeline.py \
  --input-root data/raw_courses \
  --output-root data/pipeline_runs \
  --strict-mode true \
  --max-courses 10
```

Optional flags:
- `--course-id <id>` repeatable
- `--overwrite-existing`
- `--persist-to-db`
- `--model-profile <name>`
- `--tag <value>` repeatable

Also add a deployment registration script that:
- creates or updates a deployment
- assigns a named work pool
- sets a useful deployment name
- documents how to start a matching worker

---

## 15. Deployment target for phase 1

Implement for a simple Prefect 3 setup using:

- local code execution for development
- optional Prefect server or Prefect Cloud for orchestration metadata
- `process` work pool for worker-based runs

Document:
- how to start Prefect server or connect to Prefect Cloud
- how to create the work pool
- how to start the worker
- how to register the deployment
- how to trigger a run

Do not assume container registry, Kubernetes, ECS, or S3 in phase 1.

---

## 16. Database strategy

Phase 1 database behavior:

- keep current Postgres integration optional
- do not block the Prefect rewrite on relationalizing the entire ledger
- if `persist_to_db=false`, the pipeline must still succeed and write all expected artifacts locally

If `persist_to_db=true`, the pipeline may write:
- run metadata
- stage metadata
- selected normalized entities if current code already supports it

Do not invent a large new relational schema in this phase unless required to preserve existing behavior.

---

## 17. Testing requirements

### 17.1 Unit tests

Add tests for:
- run config validation
- run context creation
- manifest generation
- stage summary serialization
- strict-mode blocking behavior
- artifact indexing

### 17.2 Integration tests

Add at least one bounded integration test that runs the Prefect pipeline over a tiny fixture set and verifies:
- flow completes successfully
- expected artifact directories are created
- `all_questions.jsonl` exists
- `inspection_report.md` exists
- manifest contains all stages

Add one strict-mode failure fixture that verifies:
- coverage failure causes failed flow state
- partial artifacts remain inspectable
- manifest records the blocking failure

### 17.3 Regression assertions

At minimum, assert these invariants after a successful run:
- ledger exists
- derived views exist
- no terminal question disappears between policy result and ledger
- no `required_entry=true` question is hidden solely because of `low_distinctiveness`

---

## 18. Acceptance criteria

Codex should treat the work as done only when all of these are true.

### Functional acceptance

1. A developer can run the new Prefect flow locally from Python.
2. The flow produces a run directory with stage-separated outputs.
3. The canonical question path is orchestrated end-to-end.
4. Strict coverage failures stop the flow with a clear error.
5. The ledger remains the authoritative final output for question states.
6. Inspection bundle outputs are still produced.
7. Existing domain behavior is preserved to the greatest extent possible.

### Orchestration acceptance

8. The pipeline is broken into meaningful flows/tasks.
9. Stage summaries and final manifest are written.
10. Prefect artifacts show run-level progress and summaries.
11. A deployment can be registered to a Prefect work pool.
12. A process worker can execute the deployment.

### Code quality acceptance

13. New code is typed.
14. New code is documented.
15. New code uses thin adapters around legacy/current logic rather than copying large blocks.
16. Tests cover both happy path and strict-mode blocking path.

---

## 19. Suggested implementation order

Codex should implement in this order.

### Phase 1: scaffolding
- create package layout
- implement config / context / summary / manifest models
- implement filesystem helpers
- implement basic logging
- implement top-level flow skeleton with stub tasks

### Phase 2: standardization wiring
- wrap standardization logic
- emit standardized artifacts
- update manifest and Prefect artifacts

### Phase 3: semantics + candidates wiring
- wrap V3 semantic extractors
- wrap candidate generation, filter, scoring, dedupe
- emit course-level outputs and summaries

### Phase 4: policy + strict failure wiring
- wrap V4.1 policy path
- surface coverage warnings
- fail strict runs appropriately

### Phase 5: ledger + derived views + bundle rendering
- wrap V6 ledger
- derive views
- render bundle
- finalize manifest

### Phase 6: deployment and docs
- add run script
- add deployment registration script
- add runbook
- verify process work pool execution

### Phase 7: tests and cleanup
- add integration fixtures
- add strict-mode failure fixture
- remove duplication
- improve docstrings and comments

---

## 20. Example pseudocode for the top-level flow

```python
from prefect import flow

@flow(name="question-generation-pipeline", log_prints=True)
def question_generation_pipeline_flow(config: RunConfig) -> RunResult:
    context = prepare_run_context(config)

    stage_summaries: list[StageSummary] = []

    standardize_summary = standardize_courses_flow(context, config)
    stage_summaries.append(standardize_summary)

    semantics_summary = extract_semantics_flow(context, config)
    stage_summaries.append(semantics_summary)

    candidates_summary = generate_candidates_flow(context, config)
    stage_summaries.append(candidates_summary)

    policy_summary = apply_policy_flow(context, config)
    stage_summaries.append(policy_summary)

    ledger_summary = build_ledger_flow(context, config)
    stage_summaries.append(ledger_summary)

    views_summary = derive_views_flow(context, config)
    stage_summaries.append(views_summary)

    bundle_summary = render_inspection_bundle_flow(context, config)
    stage_summaries.append(bundle_summary)

    result = finalize_run_manifest(context, stage_summaries)
    return result
```

---

## 21. Example deployment direction

Codex should support a deployment creation path similar to:

```python
from course_pipeline.prefect_pipeline.flows import question_generation_pipeline_flow

if __name__ == "__main__":
    question_generation_pipeline_flow.deploy(
        name="question-generation-dev",
        work_pool_name="course-pipeline-process",
        parameters={
            "config": {
                "input_root": "data/raw_courses",
                "output_root": "data/pipeline_runs",
                "strict_mode": True,
            }
        },
        build=False,
        push=False,
    )
```

If Codex chooses a YAML-based deployment definition instead, that is acceptable as long as it is current Prefect 3 style and documented.

---

## 22. Out-of-scope but design for later

The code should leave room for later phases:

- object storage for artifacts
- relationalized ledger tables
- FastAPI trigger/poll endpoints
- background run triggering from a web app
- richer Prefect work pools
- cloud execution targets
- OpenTelemetry / Prometheus / Sentry integration
- selective reruns of failed courses only

Do not implement all of these now, but avoid painting the package into a corner.

---

## 23. Final instruction to Codex

Implement the new Prefect pipeline as a **thin orchestration layer around the current canonical question-generation path**.

Prefer:
- preserving current domain behavior
- explicit manifests and artifacts
- strong typing
- useful stage boundaries
- strict invariant enforcement
- developer-friendly local execution

Avoid:
- premature infrastructure complexity
- large rewrites of core generation logic
- replacing filesystem artifacts before the new orchestration layer proves itself

The result should feel like a productionizable orchestration upgrade, not a research rewrite.
