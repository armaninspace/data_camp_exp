# Inspection Bundle 4.1

This bundle contains the V4.1 persistence-and-coverage implementation based
on [req_bundle_4_1](/code/docs/req_bundle_4_1).

## What changed relative to V4

V4.1 does not mainly change scoring. It changes auditability.

The new guarantees are:

- validated-correct candidates are persisted before curation
- visible selection is non-destructive
- hidden-but-correct candidates are exported explicitly
- missing visible beginner-anchor coverage produces machine-readable warnings

## Included files

- [question_gen_v4_1_report.md](/code/docs/inspection_bundle_4_1/question_gen_v4_1_report.md)
- [question_gen_v4_1_backlog.md](/code/docs/inspection_bundle_4_1/question_gen_v4_1_backlog.md)
- [question_gen_v4_1_implementation_report.md](/code/docs/inspection_bundle_4_1/question_gen_v4_1_implementation_report.md)
- [24491_forecasting-in-r.md](/code/docs/inspection_bundle_4_1/24491_forecasting-in-r.md)
- [24593_visualizing-time-series-data-in-r.md](/code/docs/inspection_bundle_4_1/24593_visualizing-time-series-data-in-r.md)
- [24594_case-study-analyzing-city-time-series-data-in-r.md](/code/docs/inspection_bundle_4_1/24594_case-study-analyzing-city-time-series-data-in-r.md)

## Source run

- V3 source run: `20260417T182414Z`
- V4.1 run: `20260417T235527Z`

Full artifacts live under
[20260417T235527Z](/code/data/pipeline_runs/20260417T235527Z).
