# Question Generation V4.1 Bundle for Codex

This bundle is the implementation package for the fix discussed in chat.

## Core objective

Fix the failure mode where obvious beginner questions are either:
1. never generated, or
2. generated correctly and then silently removed by curation.

## Non-negotiable invariants

### Invariant 1 — persist before curate
If a candidate question is validated as correct and grounded, it must be written to persistent storage before any ranking, deduplication, balancing, or visible-set selection.

### Invariant 2 — curation is non-destructive
Curation may assign a `delivery_class`, but it may not delete or suppress the existence of validated-correct candidates.

### Invariant 3 — foundational entry coverage must be auditable
For each `foundational_vocabulary_anchor`, the system must detect whether a visible canonical entry question exists. If not, emit a coverage warning even if correct hidden variants exist.

## Included files

- `question_gen_v4_1_policy_addendum.md`
- `question_gen_v4_1_codex_handoff.md`
- `question_gen_v4_1_config_patch.yaml`
- `question_gen_v4_1_schema.json`
- `question_gen_v4_1_tests.md`
- `question_gen_v4_1_diagram.md`

## Expected outcome

After this slice:
- every validated-correct candidate is logged
- visible curation is a routing decision, not a deletion step
- beginner anchor questions cannot disappear silently
- inspection bundles can show:
  - all validated-correct candidates
  - visible curated subset
  - hidden-but-correct candidates
  - missing anchor coverage warnings

## Definition of done

This slice is complete only if:
- a validated-correct question can no longer vanish without a trace
- a missing visible beginner anchor creates a machine-readable warning
- inspection output includes hidden-but-correct questions and their non-visible reasons
