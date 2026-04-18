# Backlog

## Assessment

The fix note in
[codex_fix_question_cache_pipeline.md](/code/docs/codex_fix_question_cache_pipeline.md:1)
is directionally correct and should replace the earlier “grow the cache layer”
mindset with a stricter “make the cache trustworthy” mindset.

What is correct:

1. The current cache generator is too loose.
2. Atomic group extraction needs to be separated from answer generation.
3. Variations must be generated only after the canonical answer is fixed.
4. Same-answer validation, answer-fit validation, grounding validation, and
   coverage audit should all be hard gates.
5. Runtime should only serve accepted variations tied to validated groups and
   validated answers.

What this means for the current implementation:

1. The current single-step claim-to-group generation should be refactored into
   staged generation.
2. The current heuristic variation validator is not sufficient on its own.
3. The current pipeline can still silently lose claim coverage through rejected
   groups unless coverage is explicitly audited.
4. The current runtime matcher should only query runtime-eligible artifacts once
   validation status fields exist.

## Fix Backlog

## Slice 1: Refactor generation order
- Split question-cache generation into explicit stages:
  - claim atomization
  - canonical answer generation
  - variation generation
  - validators
  - coverage audit
- Remove the old pattern of generating groups, variations, and answers in one
  model call.
- Tag each persisted artifact with its generation stage.

Acceptance criteria:
- no variations are generated before canonical answers
- stage outputs are inspectable independently
- failed earlier stages block later stages

## Slice 2: Add validation and audit schema fields
- Update `claim_question_groups` with:
  - `generation_stage`
  - `validator_status`
  - `coverage_status`
- Update `question_group_variations` with:
  - `candidate_source`
  - `validation_decision`
  - `validation_reason`
  - `accepted_for_runtime`
- Update `canonical_answers` with:
  - `answer_fit_status`
  - `grounding_status`
  - `grounding_reason`
  - `answer_scope_notes`
- Add:
  - `question_cache_validation_logs`
  - `claim_coverage_audit`

Acceptance criteria:
- schema supports accepted vs rejected artifacts cleanly
- audit status is queryable by course and claim
- validation logs are machine-readable

## Slice 3: Implement claim atomization stage
- Add a prompt and module that converts one claim into atomic question groups
  only.
- Forbid variations and answers at this stage.
- Prefer splitting over merging when intent boundaries are uncertain.
- Persist explicit `no_groups_reason` when a claim cannot safely produce groups.

Acceptance criteria:
- every claim ends in either groups or an explicit no-group reason
- atomized groups are narrower than the current first-pass groups

## Slice 4: Implement canonical answer generation stage
- Generate one answer per atomic question group.
- Keep answers short, direct, and evidence-bound.
- Ban unsupported examples and unsupported extra steps.
- Make answer generation consume only:
  - canonical question
  - claim text
  - citations

Acceptance criteria:
- one group maps to one answer
- answers directly answer the canonical question
- answers do not overreach the evidence basis

## Slice 5: Implement variation generation stage
- Generate candidate paraphrases only after the answer exists.
- Ban synthetic phrasing such as:
  - “What is the way to…”
  - “What is the process to…”
  - “How would one…”
- Generate 2–4 variations max.
- Allow zero accepted variations if none truly preserve the same answer.

Acceptance criteria:
- variation generation is downstream of answer generation
- candidate variations are visibly more natural than the current outputs

## Slice 6: Implement validator services
- Add validator modules for:
  - same-answer variation validation
  - answer-to-question fit
  - evidence grounding
  - coverage audit
- Persist every validator decision with rationale and model version.
- Block runtime serving for any failed validator.

Acceptance criteria:
- validator outputs are deterministic or at least stable enough for bounded runs
- rejected artifacts remain inspectable
- runtime-eligible artifacts are explicitly marked

## Slice 7: Enforce runtime gating
- Change the matcher so it only considers:
  - validated question groups
  - accepted variations
  - answers with fit pass and grounding pass
- Add explicit miss reasons:
  - `no_match`
  - `ambiguous_match`
  - `variation_rejected`
  - `answer_unvalidated`
  - `grounding_failed`
  - `follow_up_or_repair`
  - `claim_uncovered`

Acceptance criteria:
- rejected cache artifacts cannot be served accidentally
- miss reasons become inspectable and analyzable

## Slice 8: Improve inspection tooling
- Extend YAML export so each course shows:
  - source claim
  - atomic groups
  - canonical answer
  - candidate variations
  - validation decisions
  - coverage audit result
- Add CLI commands:
  - `validate-question-cache`
  - `audit-question-cache-coverage`
  - `inspect-question-group`
- Make accepted vs rejected variations visually obvious in exported YAML.

Acceptance criteria:
- one-course inspection is enough to diagnose why a group was accepted or rejected
- coverage gaps are easy to spot

## Slice 9: Add regression fixtures and tests
- Keep `7630` as the primary regression fixture.
- Add explicit test cases for:
  - positive same-answer grouping
  - negative same-answer grouping
  - answer-fit failure
  - grounding failure
  - coverage-audit failure
- Add replay fixtures for both accepted and rejected groups.

Acceptance criteria:
- the known `7630` vector examples keep passing
- current bad cases such as loose `LO1` and `LO5` groupings are captured

## Slice 10: Rebuild bounded cache runs and compare
- Rebuild the `7630` cache after the staged refactor.
- Compare:
  - group counts
  - accepted-variation precision
  - coverage completeness
  - runtime hit quality
- Do not expand to broader runs until bounded quality improves.

Acceptance criteria:
- every source claim is accounted for
- false merges decrease
- accepted runtime artifacts are fewer but safer

## Recommended Execution Order

1. Slice 2
2. Slice 1
3. Slice 3
4. Slice 4
5. Slice 5
6. Slice 6
7. Slice 7
8. Slice 8
9. Slice 9
10. Slice 10

## Definition Of Done

1. Every source claim is accounted for.
2. No variation is runtime-eligible unless the same canonical answer truly fits.
3. No answer is runtime-eligible unless answer-fit and grounding validators pass.
4. Runtime uses only accepted artifacts.
5. Inspection tooling makes failures obvious at the per-course YAML level.
