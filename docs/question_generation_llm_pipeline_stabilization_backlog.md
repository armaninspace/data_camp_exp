# Question Generation LLM Pipeline Stabilization Backlog

Purpose: capture the immediate follow-up work after the refactor landed and the
first sample runs exposed two production regressions:

1. semantic extraction accepted schema-drifted LLM JSON and produced empty
   semantic artifacts
2. special-case seed generation for `unemployment` / `GDP per capita` skipped
   required entry definitions and triggered strict coverage failure

This backlog is intentionally narrow. It is about hardening the refactored
pipeline, not redesigning it again.

## Status

- Slice 1: completed on 2026-04-19
- Slice 2: completed on 2026-04-19
- Slice 3: completed on 2026-04-19
- Slice 4: completed on 2026-04-19
- Slice 5: completed on 2026-04-19
- Slice 6: completed on 2026-04-19
- Slice 7: completed on 2026-04-19

## Current Failures We Just Fixed

Fixed in code:
- semantic extraction now falls back when LLM output is structurally unusable
- required entry seeds are preserved for the `unemployment` metric branch

What that means:
- the pipeline now produces non-empty semantic and candidate artifacts again
- strict mode can pass the previously failing `unemployment` coverage case

What is still risky:
- semantic extraction still depends on an LLM that does not reliably honor the
  requested schema
- required-entry guarantees can still be bypassed by future special-case seed
  logic
- stage outputs can fail “softly” unless there are explicit non-empty / contract
  assertions

## Slice 1: Add Semantic Extraction Contract Normalizer

Goal:
- make the semantic extraction stage robust to the known family of LLM response
  shapes instead of relying on ad hoc coercions

Tasks:
- introduce one normalizer function that accepts:
  - strict structured semantic payloads
  - `course_semantics.topics[]` loose topic payloads
  - `skills` / `learning_outcomes` / `course_structure` style payloads
- emit one canonical intermediate structure before Pydantic validation
- record the detected response shape in a debug field or artifact

Acceptance:
- the normalizer handles the known production response shapes
- parser behavior is deterministic and test-covered
- malformed-but-JSON responses do not silently produce empty semantic outputs

## Slice 2: Add Semantic Stage Non-Empty Guards

Goal:
- fail early when semantic extraction yields an unusable course

Tasks:
- add stage-level assertions such as:
  - if normalized course has sections or overview text, semantic stage must emit
    at least one topic or explicit fallback reason
  - empty semantic outputs must produce a warning or hard failure in strict mode
- write the chosen extraction path into semantic artifacts:
  - `llm`
  - `normalized_loose_shape`
  - `heuristic_fallback`
  - `parse_failure_fallback`
  - `empty_output_fallback`

Acceptance:
- empty semantic outputs are visible immediately
- strict mode cannot proceed with a silently empty semantic layer

## Slice 3: Make Required-Entry Guarantees Stage-Level Invariants

Goal:
- remove the possibility that special-case seed logic bypasses protected entry
  generation

Tasks:
- add a post-seed invariant:
  - every `requires_entry_question` anchor must have a plain definition seed
- if missing, deterministically synthesize the protected definition seed before
  repair / expansion
- keep special-case question branches additive only; they may append but not
  replace required entry seeds

Acceptance:
- protected definition seeds exist even when custom seed logic is used
- strict coverage failures only happen when the invariant itself cannot be met

## Slice 4: Separate Anchor Eligibility From Topic Extraction

Goal:
- reduce false foundational anchors like incidental mentions inside summaries

Tasks:
- split “topic extraction” from “entry-requiring anchor eligibility”
- add conservative anchor eligibility rules using:
  - section-title weight
  - repeated mention support
  - learner-facing label checks
  - incidental mention penalties
- keep topics broad if needed, but require stronger evidence before setting
  `requires_entry_question=true`

Acceptance:
- incidental terms such as context-only mentions are less likely to become
  required-entry anchors
- anchor eligibility is inspectable and rule-based

## Slice 5: Add Stage-Transition Diagnostics

Goal:
- make it obvious where volume collapses or spikes between stages

Tasks:
- add per-course transition summaries:
  - semantic topics
  - sanitized anchors
  - seed candidates
  - repaired candidates
  - derived candidates
  - validated questions
  - visible curated questions
- add run-level deltas and suspicious thresholds

Acceptance:
- one report is enough to see where output disappeared
- sudden zero-output regressions are diagnosable without manual file spelunking

## Slice 6: Add Regression Fixtures For Known Failure Families

Goal:
- lock down the failure modes already seen in real runs

Fixtures to keep:
- `overview-segment-1`
- `www.example.com`
- `unemployment`
- `GDP per capita`
- acronym and foundational vocabulary examples
- a course where LLM semantic extraction returns non-conforming JSON

Acceptance:
- each failure family has a direct unit or integration regression test
- the sample run bug class cannot silently reappear

## Slice 7: Tighten Micro-Design Boundaries

Goal:
- clean up a few small design seams that made the regressions easier to create

Recommended micro-design changes:
- introduce a single `SemanticStageResult` model instead of passing loosely
  structured dicts between extraction, sanitation, and bridging
- introduce a single `SeedGenerationInvariantReport` that records:
  - anchors requiring entry
  - protected seeds found
  - protected seeds synthesized
  - missing protected seeds
- isolate special-case seed generators behind helpers such as:
  - `emit_metric_special_case_candidates(...)`
  - `emit_tool_special_case_candidates(...)`
  so they cannot accidentally bypass shared invariant enforcement

Acceptance:
- stage handoffs become easier to reason about
- special-case generation logic no longer owns correctness-critical guarantees

## Recommended Order

1. Slice 3
2. Slice 2
3. Slice 1
4. Slice 5
5. Slice 4
6. Slice 6
7. Slice 7

Rationale:
- required-entry guarantees and empty-stage detection are the highest-risk
  correctness issues
- schema normalization should be improved, but the pipeline is already safer now
  that unusable LLM output falls back
- micro-design cleanup should happen after the guardrails are in place

## Definition Of Done

- semantic extraction cannot silently succeed with zero usable outputs
- every required-entry anchor has a protected definition seed or an explicit
  failure reason
- strict coverage failures only reflect real downstream coverage issues
- run artifacts clearly show where output changed between stages
- the current regression families are test-covered
