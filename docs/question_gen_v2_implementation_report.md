# Question Generation V2 Implementation Report

## Scope

Implemented the candidate-question generation pipeline described in
[question_gen_algo_v2.md](/code/docs/question_gen_algo_v2.md:1) as a new,
separate stage in the course pipeline.

Also added a review-bundle export that turns generated candidate questions into
grounded Q/A Markdown docs for manual inspection.

## Backlog

Tracking doc:

- [question_gen_algo_v2_backlog.md](/code/docs/question_gen_algo_v2_backlog.md)

Implemented slices:

- Slice 1: V2 artifact schemas
- Slice 2: semantic extraction stage
- Slice 3: candidate-question generation stage
- Slice 4: natural-language preference rules
- Slice 5: scoring, deduping, canonicalization
- Slice 6: run artifacts and report output
- Slice 7: CLI wiring
- Slice 8: review-bundle export
- Slice 9: bounded run for the three target time-series R courses

## Code Changes

Primary implementation files:

- [question_gen_v2.py](/code/src/course_pipeline/question_gen_v2.py)
- [pipeline.py](/code/src/course_pipeline/pipeline.py)
- [cli.py](/code/src/course_pipeline/cli.py)
- [schemas.py](/code/src/course_pipeline/schemas.py)
- [README.md](/code/README.md)

## Bounded Run

Question generation V2 run:

- run id: `20260417T135100Z`
- run dir: [20260417T135100Z](/code/data/pipeline_runs/20260417T135100Z)

Review bundle output:

- [24491_forecasting-in-r.md](/code/data/pipeline_runs/20260417T135100Z/review_bundle/24491_forecasting-in-r.md)
- [24593_visualizing-time-series-data-in-r.md](/code/data/pipeline_runs/20260417T135100Z/review_bundle/24593_visualizing-time-series-data-in-r.md)
- [24594_case-study-analyzing-city-time-series-data-in-r.md](/code/data/pipeline_runs/20260417T135100Z/review_bundle/24594_case-study-analyzing-city-time-series-data-in-r.md)

Convenience copies under `docs`:

- [review_bundle_v2](/code/docs/review_bundle_v2)

## Artifact Counts

From the bounded run:

- topics: `13`
- learner-friction candidates: `3`
- candidate questions: `57`
- errors: `0`

Per course:

- `24491`: `20` candidate questions
- `24593`: `16` candidate questions
- `24594`: `21` candidate questions

Generated run report:

- [question_gen_v2_report.md](/code/data/pipeline_runs/20260417T135100Z/question_gen_v2_report.md)

## Observed Improvements

- The generated questions are materially less claim-shaped than the earlier
  claim-to-question outputs.
- `24491` now includes learner-natural prompts around plotting, benchmark
  methods, forecast accuracy, exponential smoothing, ARIMA, and advanced
  methods.
- The new stage preserves chapter context and topic labels in the artifacts.
- The review bundle is now self-contained per course: Q/A pairs first, then
  scraped summary, overview, and syllabus.

## Residual Gaps

- Learner-friction extraction is still underproducing on some courses. In this
  bounded run, `24491` and `24593` ended up with `0` explicit friction
  candidates, even though the final questions are better than before.
- Some generated questions are still a little broad or generic.
- Review answers are grounded, but they are a review artifact rather than a
  canonical runtime answer layer.
- There is no dedicated test suite yet for V2 outputs.

## Recommended Next Steps

1. Add regression fixtures for a small set of courses and expected question
   families.
2. Strengthen friction extraction so jargon-heavy courses surface more
   definition and motivation questions explicitly.
3. Add a lightweight validation pass for candidate-question quality before
   review-bundle answer generation.
