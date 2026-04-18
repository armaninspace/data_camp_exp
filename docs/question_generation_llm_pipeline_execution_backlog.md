# Question Generation LLM Pipeline Execution Backlog

Purpose: turn [question_generation_llm_pipeline_enhancement_backlog_v2.md](/code/docs/question_generation_llm_pipeline_enhancement_backlog_v2.md) into an implementation plan against the current codebase.

This backlog assumes:
- the existing deterministic normalization, policy, ledger, and bundle validation stay in place
- the current bounded LLM repair / expansion path remains additive
- answer generation stays downstream from validated questions

## Current State

Already implemented:
- bounded LLM candidate repair
- bounded LLM candidate expansion
- deterministic candidate merge with provenance
- Prefect artifactization for repair / expansion / merge
- planned and actual LLM metering in run manifests
- live metered review-answer bundle path
- automatic inspection bundle builder with scoped validation

Not yet implemented from v2:
- early LLM semantic extraction
- deterministic semantic sanitation / canonicalization layer
- semantic artifacts and semantic CLI surface
- seed generation split as an explicit stage
- standalone answer-generation pipeline with validation artifacts
- integrated orchestration path for the refactored architecture

## Architecture Target

Desired flow:

1. deterministic normalization
2. LLM semantic extraction
3. deterministic semantic sanitation / canonicalization
4. seed question generation
5. LLM candidate repair
6. LLM grounded expansion
7. deterministic filtering / scoring / policy
8. foundational coverage audit
9. V6 ledger
10. derived views
11. automatic inspection bundle build + validation

Separate downstream flow:

1. validated questions
2. LLM answer generation
3. answer-fit / grounding validation
4. answer artifacts

## Slice 0: Freeze Current Behavior

Status: completed

Goal:
- establish the current enhanced path as the baseline before inserting the earlier semantic stage

Tasks:
- document the current artifact contract for:
  - `semantics/`
  - `candidates/`
  - `policy/`
  - `ledger/`
  - `review_bundle/`
- add a small architecture note showing which current stages are heuristic vs LLM-backed
- capture one known-good enhanced run as a regression fixture reference

Acceptance:
- there is a short doc describing the current run artifact layout and stage ownership
- tests clearly distinguish existing behavior from the new semantic refactor work

## Slice 1: Semantic Schemas

Status: completed

Goal:
- define the new structured semantic layer without wiring it into the pipeline yet

Add:
- `src/course_pipeline/semantic_schemas.py`

Models:
- `TopicRecord`
- `AnchorCandidate`
- `AliasGroupRecord`
- `FrictionRecord`
- `SemanticDecisionRecord`
- `SemanticValidationReport`

Requirements:
- every record includes `course_id`
- every extracted record includes `confidence`
- every extracted record includes `source_fields`
- every extracted record includes `evidence_spans`
- every sanitation keep / drop / merge decision preserves provenance

Acceptance:
- schemas exist and are test-covered
- representative fixtures validate successfully

## Slice 2: LLM Semantic Extraction

Status: completed

Goal:
- add a new LLM stage immediately after normalization that produces structured semantic records

Add:
- `src/course_pipeline/semantic_extract_llm.py`
- optional `src/course_pipeline/semantic_render.py`

Behavior:
- input: normalized course
- output:
  - topic records
  - anchor candidates
  - alias groups
  - friction records
- output must be structured JSON, not free text
- extraction must be bounded and course-grounded

Metering:
- add a new planned stage such as `semantic_extract`

Artifacts:
- `semantic_topics.jsonl`
- `semantic_anchors.jsonl`
- `semantic_alias_groups.jsonl`
- `semantic_frictions.jsonl`
- per-course `semantic_yaml/<course_id>.yaml`

Acceptance:
- the extractor can run with and without an OpenAI key
- no-key mode fails closed or falls back explicitly, not silently
- metering is recorded when the LLM path runs

## Slice 3: Deterministic Semantic Validation And Sanitation

Status: completed

Goal:
- prevent junk anchors from reaching seed generation

Add:
- `src/course_pipeline/semantic_validate.py`

Rules:
- normalize whitespace, punctuation, and case
- reject URL/domain/site-name artifacts
- reject placeholder headings
- reject weak labels like `overview-segment-1`
- merge near-duplicates conservatively
- preserve keep / drop / merge reasoning

Artifacts:
- `semantic_validation_report.json`
- sanitized:
  - `topics.jsonl`
  - `edges.jsonl` or semantic-equivalent relationship outputs
  - `pedagogy.jsonl`
  - `friction_points.jsonl`
- decision logs for dropped or merged anchors

Important note:
- this slice should produce outputs compatible enough that existing downstream policy and ledger code can still run

Acceptance:
- junk anchors are flagged or removed before candidate generation
- known bad labels are caught in tests
- provenance is preserved for sanitation decisions

## Slice 4: Bridge Current Semantics To New Semantic Layer

Status: completed

Goal:
- adapt the current heuristic semantics contract to consume sanitized semantic records

Tasks:
- map sanitized semantic records into the current downstream shapes used by:
  - candidate generation
  - policy
  - ledger
- keep existing deterministic consumers stable while the semantic stage changes underneath them

Files likely touched:
- `src/course_pipeline/prefect_pipeline/tasks/semantics.py`
- `src/course_pipeline/questions/candidates/pipeline.py`
- `src/course_pipeline/pipeline.py`

Acceptance:
- downstream stages do not need a full rewrite
- the pipeline can swap from heuristic semantics to sanitized semantic artifacts with minimal churn

## Slice 5: Explicit Seed Generation Stage

Status: completed

Goal:
- separate seed generation from later repair / expansion

Add:
- `src/course_pipeline/question_seed_generate.py`
- optional `src/course_pipeline/question_refine_schemas.py`

Behavior:
- input: sanitized semantic layer
- output: bounded seed candidates for:
  - entry
  - bridge
  - procedural
  - friction
  - diagnostic
  - transfer

Requirements:
- foundational anchors still require plain beginner entry questions
- acronym companions may be added but never replace plain definitions
- seed generation stays deterministic and template-driven

Artifacts:
- `seed_candidates.jsonl`

Acceptance:
- current candidate generation behavior is preserved or improved
- required-entry coverage logic remains intact

## Slice 6: Re-Target LLM Repair To Seed Candidates

Status: completed

Goal:
- keep the current repair implementation, but make seed candidates the formal upstream input

Tasks:
- rename or adapt payload construction to talk about seeds instead of raw heuristic candidates
- preserve keep / rewrite / drop completeness
- preserve no-drop rules for required-entry questions

Files likely touched:
- `src/course_pipeline/question_refine_llm.py`
- `src/course_pipeline/questions/candidates/pipeline.py`

Acceptance:
- every seed candidate exits as `keep`, `rewrite`, or `drop`
- foundational plain definitions are never removed

## Slice 7: Re-Target LLM Expansion To Sanitized Semantics

Status: completed

Goal:
- make the expansion prompt depend on the sanitized semantic layer rather than the old heuristic structures

Tasks:
- prioritize grounded additions for:
  - procedural
  - diagnostic
  - transfer
  - misconception
  - comparison
- keep derivations bounded
- avoid paraphrase spam

Files likely touched:
- `src/course_pipeline/question_expand_llm.py`
- `src/course_pipeline/question_llm_merge.py`

Acceptance:
- derived questions remain bounded and grounded
- provenance survives merge cleanly

## Slice 8: Semantic Confidence Through Scoring

Status: completed

Goal:
- thread semantic confidence into deterministic downstream scoring without handing control to the LLM

Tasks:
- add optional score components:
  - `semantic_confidence`
  - `llm_repair_confidence`
  - `llm_derivation_confidence`
- keep score aggregation deterministic

Files likely touched:
- `src/course_pipeline/questions/candidates/models.py`
- `src/course_pipeline/questions/candidates/score_candidates.py`
- policy score adapters as needed

Acceptance:
- confidence is available for inspection and tuning
- score behavior stays deterministic and testable

## Slice 9: Semantic CLI Surface

Status: completed

Goal:
- add standalone tooling for the new semantic stage

Commands:
- `run-semantic-extract-llm`
- `inspect-semantic-run`

Optional:
- a narrow command to run validation/sanitation only against existing semantic outputs

Acceptance:
- a user can inspect semantic artifacts without running the full pipeline
- docs show expected inputs and outputs

## Slice 10: Standalone Question Refinement CLI

Status: completed

Goal:
- finish the pending CLI work from the original backlog

Commands:
- `run-question-seed-gen`
- `run-question-repair-llm`
- `run-question-expand-llm`
- `inspect-question-refine-run`

Acceptance:
- repair / expand can be executed independently for debugging
- refinement artifacts can be inspected without running the full Prefect path

## Slice 11: Separate Answer Generation Pipeline

Status: completed

Goal:
- formalize answer generation as downstream from validated questions

Add:
- `src/course_pipeline/answer_schemas.py`
- `src/course_pipeline/answer_generate_llm.py`
- `src/course_pipeline/answer_validate_llm.py`

Behavior:
- input: validated questions only
- output:
  - generated answers
  - validation logs
  - review answers
- answer artifacts stay outside the authoritative ledger

Artifacts:
- `generated_answers.jsonl`
- `answer_validation_logs.jsonl`
- `review_answers.jsonl`
- per-course `answer_yaml/<course_id>.yaml`

Acceptance:
- answers never mutate the ledger
- validation can reject unsupported or weak answers explicitly

## Slice 12: Prefect Orchestration Refactor

Status: completed

Goal:
- wire the new semantic and answer stages into the Prefect flow without collapsing stage boundaries

Tasks:
- update `tasks/semantics.py` to run:
  - semantic extraction
  - semantic validation / sanitation
- keep candidate, policy, ledger, and bundle stages deterministic downstream
- add optional answer generation after validated questions
- update manifest stage summaries and artifact indexing

Acceptance:
- Prefect flow reflects the new architecture
- question generation and answer generation remain separate

## Slice 13: Integrated CLI Orchestration

Status: completed

Goal:
- expose an end-to-end entrypoint for the refactored architecture

Command:
- `run-pipeline-refactor`

Suggested stages:
1. normalization
2. semantic extraction
3. semantic validation
4. seed generation
5. repair
6. expansion
7. deterministic policy
8. ledger
9. optional answer generation
10. bundle build

Acceptance:
- the full refactored path is runnable without manual stage chaining
- optional answer generation can be toggled independently

## Slice 14: Regression And Quality Gates

Status: completed

Goal:
- codify the high-risk failure modes from v2

Tests to add:
- semantic extraction:
  - junk anchors are rejected
  - evidence spans are preserved
  - near-duplicate anchors merge conservatively
- refinement:
  - required-entry questions are never dropped
  - repaired questions preserve anchor identity
  - derived questions remain bounded
- answers:
  - only validated questions get answers
  - unsupported answers are flagged
- bundles:
  - scope drift fails
  - count mismatch fails
  - suspicious anchors surface clearly
- regressions:
  - foundational plain definitions remain visible
  - `unemployment` coverage failure remains visible
  - `overview-segment-1` does not survive to final artifacts

Acceptance:
- each known failure mode has a direct automated test

## Recommended Delivery Order

Recommended order:
1. Slice 0
2. Slice 1
3. Slice 2
4. Slice 3
5. Slice 4
6. Slice 5
7. Slice 6
8. Slice 7
9. Slice 8
10. Slice 9
11. Slice 10
12. Slice 11
13. Slice 12
14. Slice 13
15. Slice 14

Rationale:
- the semantic layer is the biggest architecture gap and should land before more downstream refinement work
- the current repair / expand work should be preserved, not rewritten
- answer generation should be formalized only after validated question outputs are stable

## Exit Criteria

This backlog is complete when:
- early semantic extraction is LLM-assisted and structured
- semantic sanitation blocks junk anchors before question generation
- repair / expansion use the sanitized semantic layer
- answer generation is downstream and separate
- the V6 ledger remains authoritative for questions
- bundles build automatically and validate scope/count consistency
- the refactored path is CLI-runnable and test-covered
