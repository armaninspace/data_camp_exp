# Question Generation V4.1 — Tests and Regression Plan

## Test objective

Verify that validated-correct questions never disappear and that missing visible beginner anchors are surfaced explicitly.

## Unit tests

### 1. Persist-before-curate invariant
Given:
- candidate passes correctness and groundedness

Assert:
- candidate record is written before any visible selection step runs

### 2. Non-destructive curation
Given:
- validated-correct candidate not selected for visible set

Assert:
- candidate still exists in storage
- `delivery_class != hard_reject`
- `visible == false`
- `non_visible_reasons` is populated

### 3. Hidden correct candidate in cache bucket
Given:
- candidate is clear, correct, grounded, but not in final visible set

Assert:
- `delivery_class == cache_servable`
- candidate appears in hidden-correct export

### 4. Alias preservation
Given:
- candidate is semantically equivalent to canonical question

Assert:
- candidate persists with `delivery_class == alias_only`
- canonical linkage is preserved

### 5. Hard reject separation
Given:
- incorrect or unsupported candidate

Assert:
- does not appear in validated-correct export
- reject audit persists minimal metadata

## Coverage audit tests

### 6. Missing visible canonical entry warning
Given:
- foundational anchor exists
- correct hidden definition candidate exists
- no visible canonical definition question exists

Assert:
- coverage warning emitted with type `only_hidden_correct_entry_exists`

### 7. Alias-only coverage warning
Given:
- only alias variants exist for foundational anchor
- no visible canonical definition question exists

Assert:
- coverage warning emitted with type `only_alias_entry_exists`

### 8. Definition generation failure warning
Given:
- foundational anchor detected
- no definition candidate generated at all

Assert:
- coverage warning emitted with type `definition_generation_failed`

## Inspection bundle tests

### 9. Hidden correct section present
Assert inspection bundle contains:
- `validated_correct_all`
- `visible_curated`
- `hidden_correct`
- `coverage_warnings`

### 10. Non-visible reason preservation
Assert hidden-correct rows include reason codes such as:
- `quota_displacement`
- `canonicalized_under_other_question`
- `kept_for_cache_not_visible`

## Done criteria

This test suite passes only if:
- validated-correct questions cannot disappear silently
- hidden-but-correct questions are inspectable
- missing visible beginner coverage is machine-detectable
