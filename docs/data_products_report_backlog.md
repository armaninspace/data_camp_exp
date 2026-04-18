# Data Products Report Backlog

## Assessment

The response to
[data_products_report_proposal.md](/code/docs/data_products_report_proposal.md:1)
is correct. The proposal is already strong, and the missing work is mostly
about sharpening method and turning the proposal into an actual report.

The main follow-up slices are:

1. make methodology explicit
2. distinguish bounded sample runs from the full-corpus run everywhere
3. count nested learning outcomes, not just course-level payload rows
4. convert the proposal into a finished scale report

## Backlog

## Slice 1: Add methodology

Goal:
- explain exactly how artifact counts were derived

Tasks:

1. Define counting rules for JSONL rows.
2. Define counting rules for nested structures inside payload rows.
3. Define how bundled YAML inspection files are counted.
4. State the source files used for each count.

Acceptance criteria:

1. a reviewer can reproduce every top-line count
2. row counts and nested counts are not conflated

## Slice 2: Separate sample versus full-corpus framing

Goal:
- avoid mixing bounded sample evidence with corpus-scale evidence

Tasks:

1. Label each run as `bounded sample` or `full corpus`.
2. Keep sample-run conclusions scoped to those runs.
3. Reserve corpus-scale claims for `20260414T052429Z`.

Acceptance criteria:

1. no report section implies sample runs are corpus-complete
2. no corpus claim relies only on bounded runs

## Slice 3: Add nested learning-outcome counts

Goal:
- represent semantic volume more honestly

Tasks:

1. Count total nested learning outcomes in the sample run.
2. Count total nested learning outcomes in the full-corpus run.
3. Add per-course distribution statistics for the full-corpus run:
   - min
   - median
   - mean
   - max
4. Highlight that course-level payload row counts understate semantic volume.

Acceptance criteria:

1. both payload counts and nested counts are reported
2. the report makes the distinction explicit

## Slice 4: Publish the actual scale report

Goal:
- replace the proposal-only state with a finished report

Tasks:

1. Write a report with:
   - executive summary
   - methodology
   - run inventory
   - artifact count tables
   - scale ratios
   - review burden interpretation
   - error footprint
2. Use counts from:
   - [manifest.json](/code/docs/bundle_data_products/manifest.json:1)
   - bundled JSONL files
3. Include nested learning-outcome counts and distribution statistics.

Acceptance criteria:

1. the report is self-contained
2. the report can be reviewed without reopening the proposal

## Slice 5: Optional automation follow-up

Goal:
- reduce future manual reporting work

Tasks:

1. Add a small script that regenerates the scale tables from the bundled data.
2. Emit a machine-readable summary JSON alongside the report.

Acceptance criteria:

1. future updates do not require hand-recomputing the tables
2. report refresh is repeatable

Status:
- implemented via [generate_data_products_scale_summary.py](/code/scripts/generate_data_products_scale_summary.py:1)
- emits [scale_summary.json](/code/docs/bundle_data_products/scale_summary.json:1)

## Recommended Execution Order

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 4
5. Slice 5
