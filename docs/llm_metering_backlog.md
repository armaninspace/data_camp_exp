# LLM Metering Backlog

## Goal

Add durable per-run LLM metering for every live model-backed pipeline step.

Current live LLM-backed stages:

- candidate review-answer generation in
  `src/course_pipeline/questions/candidates/pipeline.py`
- policy review-answer generation in
  `src/course_pipeline/questions/policy/run_policy.py`

## Requirements

Each model/API call must persist a metering record with at least:

- `run_id`
- `stage`
- entity scope identifiers where applicable
- `provider`
- `model`
- prompt or template version
- timestamp
- latency
- input token count
- output token count
- retry count
- cache hit/miss status
- estimated cost

## Implementation Approach

1. Add a shared metering model and recorder.
2. Add a shared JSON LLM client wrapper that records metering for each call.
3. Thread `run_id` and `run_dir` into live review-answer paths.
4. Persist top-level per-run metering JSONL.
5. Add tests for metering records and stage integration.

## Slices

### Slice 1: Backlog And Insertion Points

- identify all live LLM call sites
- document the shared insertion strategy

Acceptance:

- backlog exists
- scope is limited to real live call sites

### Slice 2: Shared Metering Substrate

- add `LLMMeteringRecord`
- add cost estimation helper
- add JSONL append helper if needed
- add recorder that persists `llm_metering.jsonl` under the run root

Acceptance:

- metering records can be written deterministically in tests

### Slice 3: Shared Metered LLM Client

- move duplicated OpenAI chat-completions request logic into one reusable client
- record latency, token usage, cache status, retry count, and estimated cost
- include entity scope in recorded rows

Acceptance:

- one successful model call writes one metering record
- one failed model call still writes a metering record with error context

### Slice 4: Candidate Review-Answer Integration

- update candidate review-answer generation to use the shared metered client
- write candidate-stage metering with prompt version metadata

Acceptance:

- candidate review bundle generation emits metering rows

### Slice 5: Policy Review-Answer Integration

- update policy review-answer generation to use the shared metered client
- write policy-stage metering with prompt version metadata

Acceptance:

- policy review bundle generation emits metering rows

### Slice 6: Tests And Inspection

- add unit tests for recorder and client behavior
- add integration tests for candidate and policy review bundle metering
- verify no regression in existing pipeline smoke tests

Acceptance:

- targeted metering tests pass
- existing regression suite still passes
