# Question Generation V3 Implementation Report

## Assessment

The V3 requirement bundle was directionally correct.

The strongest part of the new effort is the shift from:

- generation-first

to:

- structure-first
- friction-first
- filter and rank before final selection

That is the right response to the V2 failure mode where grounded questions were
still often too generic or not worth asking.

## Implemented

Backlog:

- [question_gen_v3_backlog.md](/code/docs/question_gen_v3_backlog.md)

New package:

- [question_gen_v3](/code/src/course_pipeline/question_gen_v3)

Key modules:

- [models.py](/code/src/course_pipeline/question_gen_v3/models.py)
- [normalize.py](/code/src/course_pipeline/question_gen_v3/normalize.py)
- [extract_topics.py](/code/src/course_pipeline/question_gen_v3/extract_topics.py)
- [extract_edges.py](/code/src/course_pipeline/question_gen_v3/extract_edges.py)
- [extract_pedagogy.py](/code/src/course_pipeline/question_gen_v3/extract_pedagogy.py)
- [mine_friction.py](/code/src/course_pipeline/question_gen_v3/mine_friction.py)
- [generate_candidates.py](/code/src/course_pipeline/question_gen_v3/generate_candidates.py)
- [filters.py](/code/src/course_pipeline/question_gen_v3/filters.py)
- [score_candidates.py](/code/src/course_pipeline/question_gen_v3/score_candidates.py)
- [dedupe.py](/code/src/course_pipeline/question_gen_v3/dedupe.py)
- [select_final.py](/code/src/course_pipeline/question_gen_v3/select_final.py)
- [pipeline.py](/code/src/course_pipeline/question_gen_v3/pipeline.py)
- [question_gen_v3_config.yaml](/code/src/course_pipeline/question_gen_v3/question_gen_v3_config.yaml)

Main pipeline wiring:

- [pipeline.py](/code/src/course_pipeline/pipeline.py)
- [cli.py](/code/src/course_pipeline/cli.py)

## Bounded V3 Run

Final successful run:

- run id: `20260417T182414Z`
- run dir: [20260417T182414Z](/code/data/pipeline_runs/20260417T182414Z)

Generated run report:

- [question_gen_v3_report.md](/code/data/pipeline_runs/20260417T182414Z/question_gen_v3_report.md)

Review docs:

- [24491_forecasting-in-r.md](/code/data/pipeline_runs/20260417T182414Z/review_bundle/24491_forecasting-in-r.md)
- [24593_visualizing-time-series-data-in-r.md](/code/data/pipeline_runs/20260417T182414Z/review_bundle/24593_visualizing-time-series-data-in-r.md)
- [24594_case-study-analyzing-city-time-series-data-in-r.md](/code/data/pipeline_runs/20260417T182414Z/review_bundle/24594_case-study-analyzing-city-time-series-data-in-r.md)

## Counts

Bounded run totals:

- topics: `28`
- edges: `23`
- friction points: `23`
- raw candidates: `109`
- rejected candidates: `18`
- final selected questions: `24`
- errors: `0`

Per course:

- `24491`: `8` selected questions
- `24593`: `8` selected questions
- `24594`: `8` selected questions

## Inspection Bundle

Published copies:

- [inspection_bundle_3](/code/docs/inspection_bundle_3)

## Outcome

This V3 result is not perfect, but it is materially better than the earlier V2
bundle in two important ways:

1. the selected questions are less dominated by generic definition prompts
2. the final set is explicitly balanced toward comparison, diagnostic,
   misconception, transfer, and procedure questions

## Residual Gaps

- Some selected questions are still more abstract than ideal.
- Topic extraction is still heuristic-heavy rather than fully semantic.
- Review answers are grounded but still generated after selection, so answer
  richness is estimated rather than directly validated before selection.
- The current implementation does not yet use the reviewer rubric as an
  automated evaluation harness.

## Recommended Next Steps

1. Add a small gold review set and use the rubric in
   [question_gen_v3_eval_rubric.md](/code/docs/req_bundle_3/question_gen_v3_eval_rubric.md)
   for side-by-side V2 vs V3 review.
2. Improve topic extraction for broad first chapters and tool-heavy case-study
   sections.
3. Add an explicit low-answerability validator that uses sampled answer drafts
   before final selection.
