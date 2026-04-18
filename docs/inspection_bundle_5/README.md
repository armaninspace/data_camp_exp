# Inspection Bundle 5

This bundle contains the refined V4 policy output after reviewing the V4
requirements in [inspection_bundle_4](/code/docs/inspection_bundle_4) and
tightening the policy implementation.

## What is included

- [question_gen_v4_report.md](/code/docs/inspection_bundle_5/question_gen_v4_report.md)
- [24491_forecasting-in-r.md](/code/docs/inspection_bundle_5/24491_forecasting-in-r.md)
- [24593_visualizing-time-series-data-in-r.md](/code/docs/inspection_bundle_5/24593_visualizing-time-series-data-in-r.md)
- [24594_case-study-analyzing-city-time-series-data-in-r.md](/code/docs/inspection_bundle_5/24594_case-study-analyzing-city-time-series-data-in-r.md)
- [question_gen_v4_implementation_report.md](/code/docs/inspection_bundle_5/question_gen_v4_implementation_report.md)
- [question_gen_v4_backlog.md](/code/docs/inspection_bundle_5/question_gen_v4_backlog.md)

## Why this bundle is different from the first V4 pass

The refined pass adds three concrete policy improvements:

- generic scaffolded question stems are penalized and often quarantined
- `curated_core` now requires serveability and uses family-aware selection
- concrete beginner questions are preserved instead of being over-penalized

## Source run

- V3 source run: `20260417T182414Z`
- V4 refined run: `20260417T231539Z`

Run artifacts live under
[20260417T231539Z](/code/data/pipeline_runs/20260417T231539Z).
