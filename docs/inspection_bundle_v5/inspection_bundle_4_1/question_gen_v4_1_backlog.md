# Question Generation V4.1 Backlog

This backlog implements the persistence-and-coverage requirements in:

- [question_gen_v4_1_bundle_readme.md](/code/docs/req_bundle_4_1/question_gen_v4_1_bundle_readme.md)
- [question_gen_v4_1_policy_addendum.md](/code/docs/req_bundle_4_1/question_gen_v4_1_policy_addendum.md)
- [question_gen_v4_1_codex_handoff.md](/code/docs/req_bundle_4_1/question_gen_v4_1_codex_handoff.md)
- [question_gen_v4_1_tests.md](/code/docs/req_bundle_4_1/question_gen_v4_1_tests.md)
- [question_gen_v4_1_schema.json](/code/docs/req_bundle_4_1/question_gen_v4_1_schema.json)
- [question_gen_v4_1_config_patch.yaml](/code/docs/req_bundle_4_1/question_gen_v4_1_config_patch.yaml)

## Assessment

The V4.1 requirements make sense.

V4 already improved policy classification, but it still centers the final
decision object on bucket assignment. V4.1 correctly separates:

- validation
- durable existence
- delivery class
- visibility
- coverage audit

That directly addresses the failure mode where a correct beginner question
could disappear from the visible set and leave no inspectable trace.

## Slice 1: Add V4.1 config and data models

- add a V4.1 config loader or config merge path
- add models for:
  - persisted validated-correct ledger records
  - coverage warnings
  - inspection export sections

Acceptance criteria:
- schema fields in the V4.1 handoff are represented in code

## Slice 2: Persist validated-correct candidates before curation

- split policy execution into:
  - validation
  - persistence
  - canonicalization
  - classification
  - visible selection
- persist every candidate passing correctness and groundedness thresholds
  before visible-set logic runs

Acceptance criteria:
- every validated-correct candidate is stored even if not visible later
- invalid candidates are separated into reject audit only

## Slice 3: Replace destructive curation with delivery-class plus visibility

- map V4 buckets onto V4.1 delivery classes:
  - `curated_visible`
  - `cache_servable`
  - `alias_only`
  - `analysis_only`
  - `hard_reject`
- add:
  - `visible`
  - `non_visible_reasons`

Acceptance criteria:
- hidden validated-correct candidates have delivery class and reason codes
- visible selection is separate from existence

## Slice 4: Add foundational anchor detection and required entry flags

- identify `foundational_vocabulary_anchor` concepts from V3 topics and
  candidate patterns
- mark candidate records with:
  - `is_foundational_anchor`
  - `is_required_entry_candidate`

Acceptance criteria:
- anchor treatment is machine-visible in persisted records

## Slice 5: Add anchor coverage audit

- for each foundational anchor, check whether a visible canonical
  definition question exists
- emit warnings for:
  - `missing_visible_canonical_entry`
  - `only_hidden_correct_entry_exists`
  - `only_alias_entry_exists`
  - `definition_generation_failed`

Acceptance criteria:
- missing visible beginner entry coverage becomes machine-readable

## Slice 6: Export V4.1 inspection artifacts

- emit run-level and per-course artifacts for:
  - `validated_correct_all`
  - `visible_curated`
  - `hidden_correct`
  - `coverage_warnings`
  - alias map
  - hard reject summary

Acceptance criteria:
- inspection output shows hidden-but-correct distinctly from invalid rejects

## Slice 7: Update reports and review bundle

- extend review docs with:
  - visible curated questions
  - hidden but correct questions with non-visible reasons
  - coverage warnings

Acceptance criteria:
- the inspection package answers:
  - did we generate it?
  - did we keep it?
  - did we show it?

## Slice 8: Regression checks and bounded rerun

- compile and dry-run the new stage
- rerun on:
  - `24491`
  - `24593`
  - `24594`
- publish `inspection_bundle_4_1`

Acceptance criteria:
- validated-correct questions cannot disappear silently
- `inspection_bundle_4_1` exists with the new sections
