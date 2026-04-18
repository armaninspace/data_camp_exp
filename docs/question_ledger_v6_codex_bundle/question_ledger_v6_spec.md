# Question Ledger V6 Spec

## Product decision

The pipeline should end in a **complete question ledger**, not a shortlist.

The ledger is the authoritative record of every generated question and its routing metadata.
Visibility, curation, caching, and aliasing are all downstream views over that ledger.

## Pipeline

```text
extract topics
-> detect anchors
-> generate question candidates
-> validate correctness + groundedness
-> normalize canonical phrasing
-> persist all candidates to ledger
-> assign delivery_class
-> derive views
-> emit inspection report
```

## Required outputs

### 1) Authoritative ledger
`all_questions.jsonl`

Contains one row per generated candidate, including:
- question text
- answer text
- anchor/concept metadata
- family and type tags
- correctness / groundedness
- canonical vs alias
- delivery class
- visibility status
- reasons
- scores
- provenance

### 2) Derived views
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

## Delivery classes

Every candidate must end in exactly one of:

- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`
- `hard_reject`

## Question families

Use at least:
- `entry`
- `bridge`
- `procedural`
- `friction`
- `diagnostic`
- `transfer`

## Question types

Use at least:
- `definition`
- `purpose`
- `comparison`
- `procedure`
- `misconception`
- `diagnostic`
- `application`

## Anchor policy

Foundational anchors should be tracked explicitly.
For anchors, the ledger and inspection report should show:

- `coverage_status`
- `generated_count`
- `validated_correct_count`
- `visible_count`
- `cache_servable_count`
- `analysis_only_count`
- `hard_reject_count`
- whether a required entry question exists
- whether a required entry question is visible

## Non-destructive policy

No validated-correct question may disappear because of curation.
Curation chooses a delivery class and visibility; it does not delete the record.

## Inspection report structure

The human-readable report should support:
- grouping by anchor
- grouping by delivery class
- grouping by question family/type
- visibility analysis
- missing coverage warnings
- reasons for non-visible items

## Minimum record fields

- `question_id`
- `question_text`
- `answer_text`
- `anchor_id`
- `anchor_label`
- `anchor_type`
- `question_family`
- `question_type`
- `mastery_band`
- `canonical`
- `alias`
- `canonical_target`
- `required_entry`
- `validated_correct`
- `grounded`
- `serviceable`
- `delivery_class`
- `visible`
- `non_visible_reasons`
- `tags`
- `scores`
- `source_refs`

## Key invariants

1. Every generated candidate is written to `all_questions.jsonl`.
2. Every candidate has exactly one `delivery_class`.
3. Every validated-correct candidate survives in the ledger.
4. Aliases route to canonical questions instead of competing with them.
5. Derived views must be reproducible from the ledger alone.
