# LLM API Metering

## Requirement

Every LLM-backed pipeline step must emit durable metering records tied to the current run.

At minimum, each model/API call must record:

- `run_id`
- `stage`
- entity scope identifiers where applicable, such as `course_id`, `claim_id`, or `question_group_id`
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

Metering artifacts must be persisted alongside other run artifacts so model-dependent stages remain traceable, inspectable, and auditable.

## Current Implementation

The current live implementation writes:

- `llm_metering.jsonl`

under the run root for live LLM-backed review-answer stages.

Current metered live stages:

- candidate review answers
- policy review answers

Current implementation path:

- [llm_metering.py](/code/src/course_pipeline/llm_metering.py)

The metering artifact is designed to be:

- durable per run
- reproducible
- append-only within a run
- suitable for later inspection and cost analysis

## Constraint

All future model-call stages should use the shared metering path rather than
adding ad hoc call logging.
