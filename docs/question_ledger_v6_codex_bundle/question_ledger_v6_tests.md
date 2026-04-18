# Question Ledger V6 Tests

## Acceptance tests

1. The pipeline emits `all_questions.jsonl`.
2. Every generated candidate appears exactly once in `all_questions.jsonl`.
3. Every ledger row has exactly one `delivery_class`.
4. Every derived view can be reconstructed from `all_questions.jsonl`.
5. No validated-correct question disappears from the ledger.
6. `inspection_report.md` shows non-visible reasons for hidden correct questions.
7. Alias rows point to a canonical target and do not compete for visibility.

## Suggested regression tests

- Generated candidate count equals ledger row count.
- Visible curated count equals number of rows with `delivery_class=curated_visible`.
- Cache-servable count equals number of rows with `delivery_class=cache_servable`.
- Alias view contains only rows with `delivery_class=alias_only`.
- Hidden correct questions remain queryable in the ledger.
- Hard rejects never appear in visible or cache views.
