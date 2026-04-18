# Question Generation V4.1 — Codex Handoff

Implement the V4.1 persistence-and-coverage slice.

## Goal

Fix the pipeline so that:
- every validated-correct question is logged before curation
- curation is non-destructive
- missing visible beginner entry questions for foundational concepts produce explicit warnings

## Required architectural changes

### 1. Persist before curate
Refactor the pipeline so that any candidate with:
- `correctness >= correctness_threshold`
- `groundedness >= groundedness_threshold`

is written to persistent storage before:
- ranking
- diversity balancing
- visible-set selection
- quota pruning
- semantic dedupe suppression

### 2. Replace destructive curation with delivery-class assignment
Current delete/drop behavior for validated-correct candidates must be replaced with assignment into:
- `curated_visible`
- `cache_servable`
- `alias_only`
- `analysis_only`

Invalid candidates still go to:
- `hard_reject`

### 3. Add foundational anchor coverage audit
After classification, run an audit:

For each `foundational_vocabulary_anchor`:
- find canonical entry-question candidates
- determine whether one is visible
- if none is visible, create coverage warning

### 4. Preserve non-visible reasons
For every validated-correct candidate that is not visible, persist:
- `delivery_class`
- `visible = false`
- `non_visible_reasons[]`

### 5. Update inspection bundle output
Inspection artifacts must include:
- all validated-correct candidates
- visible curated subset
- hidden-but-correct candidates
- canonical/alias mapping
- anchor coverage warnings

## Suggested implementation plan

### Step A — schema updates
Add or extend persisted candidate record with fields:
- `candidate_id`
- `question`
- `answer`
- `topic_ids`
- `canonical_id`
- `is_correct`
- `is_grounded`
- `delivery_class`
- `visible`
- `non_visible_reasons`
- `scores`
- `source_refs`
- `is_foundational_anchor`
- `is_required_entry_candidate`

### Step B — pipeline refactor
Split current downstream logic into:
1. generation
2. validation
3. persistence
4. canonicalization
5. classification
6. visible selection
7. coverage audit
8. inspection export

### Step C — anchor coverage logic
Implement machine-readable coverage warning object with fields:
- `warning_id`
- `concept_id`
- `concept_label`
- `warning_type`
- `has_hidden_correct_variants`
- `candidate_ids`
- `message`

### Step D — inspection exporter
Add exporter sections:
- `validated_correct_all`
- `visible_curated`
- `hidden_correct`
- `alias_map`
- `coverage_warnings`

## Pseudocode target

```python
candidates = generate_candidates(content)

validated = []
rejected = []

for c in candidates:
    eval = validate_candidate(c)
    if eval.is_correct and eval.is_grounded:
        c.is_correct = True
        c.is_grounded = True
        persist_candidate(c)   # invariant: happens before curation
        validated.append(c)
    else:
        c.delivery_class = "hard_reject"
        persist_reject_audit(c, eval)
        rejected.append(c)

canonicalized = canonicalize(validated)
classified = classify_delivery(canonicalized)
visible = select_visible_subset(classified)
warnings = audit_anchor_coverage(classified, visible)

export_inspection_bundle(
    validated_correct_all=classified,
    visible_curated=visible,
    hidden_correct=[c for c in classified if not c.visible],
    coverage_warnings=warnings,
)
```

## Acceptance criteria

### Functional
- a validated-correct candidate is always discoverable in storage
- a non-visible validated-correct candidate has a delivery class and a non-visible reason
- a foundational anchor without visible canonical entry coverage produces warning output
- inspection bundle shows hidden correct candidates distinctly from hard rejects

### Deliverables expected from implementation
- updated pipeline code
- updated config
- updated schemas
- updated inspection bundle
- regression tests
- short implementation note documenting where persistence now occurs
