# Question Generation LLM Pipeline Enhancement Backlog

Goal: add bounded LLM-assisted repair and grounded expansion without replacing the existing heuristic candidate path.

## Slice 1: Schemas And Provenance

Status: completed

- add repair / expansion / merge schemas
- add provenance fields to `QuestionCandidate`
- preserve source lineage through merge

## Slice 2: LLM Repair Stage

Status: completed

- add bounded repair prompt + parser
- keep every original candidate in an explicit state: keep / rewrite / drop
- preserve protected foundational definitions
- fallback conservatively when no OpenAI key is configured

## Slice 3: LLM Expansion Stage

Status: completed

- add bounded grounded-expansion prompt + parser
- create only derived candidates with explicit provenance
- fallback to no-op when no OpenAI key is configured

## Slice 4: Integrated Candidate Merge

Status: completed

- merge original + repaired + derived candidates
- keep original ids where possible
- assign derived ids with deterministic slugs
- feed merged candidates into existing filter / score / dedupe flow

## Slice 5: Artifactization In Prefect Pipeline

Status: completed

- write `candidate_repairs.jsonl`
- write `candidate_expansions.jsonl`
- write `candidate_merge_report.jsonl`
- write `merged_candidates.jsonl`
- write per-course `question_refine.yaml`
- write per-course `question_expand.yaml`

## Slice 6: Metering Plan Alignment

Status: completed

- include `candidate_repair`
- include `candidate_expand`
- keep existing answer-generation stages in the planned metering summary

## Slice 7: CLI Surface For Standalone Repair / Expand Commands

Status: pending

- add explicit CLI entry points for repair-only and expand-only runs
- add inspect commands for refinement artifacts

## Slice 8: Inspection Publication

Status: pending

- run the enhanced path with a visible OpenAI key
- verify metering and refinement artifacts
- publish `inspection_bundle_9`
