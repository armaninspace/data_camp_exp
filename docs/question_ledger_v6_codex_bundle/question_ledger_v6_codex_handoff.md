# Question Ledger V6 Codex Handoff

Implement a ledger-first end state for the question generation pipeline.

## Objective

Stop treating curation as deletion.
The pipeline should preserve all generated questions in a single ledger and derive all downstream views from that ledger.

## Required code changes

### 1) Add authoritative ledger emission
Create `all_questions.jsonl` as the canonical output of the pipeline.
Every candidate question must be persisted to this file.

### 2) Add normalized routing metadata
Each row must include:
- anchor metadata
- family/type tags
- correctness/groundedness
- canonical/alias fields
- delivery class
- visibility info
- reasons
- scores
- source refs

### 3) Replace destructive curation
Current curation logic should become a delivery-class assignment step.
It must not drop validated-correct questions.

### 4) Add derived views
Emit:
- `visible_curated.jsonl`
- `cache_servable.jsonl`
- `aliases.jsonl`
- `anchors_summary.json`
- `inspection_report.md`

These must be derivable from `all_questions.jsonl`.

### 5) Add inspection report
The report should group questions by anchor and show:
- counts by delivery class
- whether required entry coverage exists
- whether required entry coverage is visible
- reasons when items are hidden
- canonical vs alias status

### 6) Add canonicalization-friendly fields
Distinguish:
- canonical intent representative
- alias-only surface forms
- canonical target mapping

## Suggested implementation shape

### Data model
Use one ledger row model plus an anchor summary model.

### Flow
1. generate candidates
2. validate
3. normalize question phrasing
4. persist to ledger
5. assign `delivery_class`
6. derive view files
7. emit inspection report

## Delivery class rules

- `curated_visible`: best surfaced set
- `cache_servable`: not visible, but directly useful to serve
- `alias_only`: maps to canonical item
- `analysis_only`: preserved for analysis only
- `hard_reject`: invalid / unsupported / malformed

## Acceptance criteria

- `all_questions.jsonl` exists and contains all generated candidates
- no validated-correct question disappears from the ledger
- every row has exactly one `delivery_class`
- derived views are consistent with the ledger
- inspection report explains why a correct question is hidden

## Nice-to-have

- deterministic stable ordering by anchor and canonical id
- unique IDs that are reproducible across reruns
- a flag or mode to emit only sample slices for inspection
