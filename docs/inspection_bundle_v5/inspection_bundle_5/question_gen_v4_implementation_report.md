# Question Generation V4 Implementation Report

## Scope

This report covers the refinement pass driven by the V4 policy docs in
[inspection_bundle_4](/code/docs/inspection_bundle_4).

V4 remains a policy layer on top of V3. The refinement work did not replace
V3 generation. It changed how V3 candidates are evaluated for:

- `curated_core`
- `cache_servable`
- `analysis_only`
- `alias_only`
- `hard_reject`

## What changed

### 1. Generic scaffold detection

Added explicit detection for thin reusable stems such as:

- `Why does X matter in this course?`
- `How would I apply X to the kind of data used here?`
- `What would make X fail in a realistic case?`
- `When would I need to adapt X instead of applying it the same way every time?`

These now trigger policy penalties rather than being treated as normal
serviceable questions.

### 2. Stronger serviceability gate

`cache_servable` now requires more than basic correctness.

The gate now penalizes:

- generic template wording
- heavy course-context dependence
- unstable answers
- orientation questions that are mostly course-framing rather than direct learner help

This moved many thin questions from `cache_servable` to `analysis_only`.

### 3. Beginner questions preserved

The first refinement pass was too strict and suppressed valid entry
questions such as `What is exponential smoothing?`

That was corrected by adding targeted boosts for short grounded
definition and procedure questions when they are concrete and not generic.

### 4. Family-aware curation

`curated_core` is no longer a simple score sort.

Curation now:

- requires the candidate to be serveable
- caps curated size per course
- seeds the curated set with family coverage when available
- prevents the curated set from filling with only one lane of question types

### 5. Stronger telemetry

The V4 report now includes:

- curated-core count
- top reason codes
- clearer bucket diagnostics

## Final bounded run

- V3 source run: `20260417T182414Z`
- V4 run: `20260417T231539Z`
- V4 report: [question_gen_v4_report.md](/code/data/pipeline_runs/20260417T231539Z/question_gen_v4_report.md)

## Outcome

### Course `24491`

- `8` curated
- `12` cache-servable
- `15` analysis-only

Result:
The final set keeps concrete forecasting questions like ARIMA,
benchmarking, exponential smoothing, and forecast-accuracy diagnostics,
while generic `trend/seasonality/repeated cycles` scaffolds are mostly
quarantined.

### Course `24593`

- `3` curated
- `6` cache-servable
- `3` analysis-only

Result:
The final set centers on the real learner decision boundary between
univariate and multivariate views instead of repeating generic plotting
scaffolds.

### Course `24594`

- `4` curated
- `12` cache-servable
- `20` analysis-only

Result:
The final set now favors the actual case-study friction points
around merging, isolating periods, and combining data sources rather than
surface-level `what is X?` overproduction.

## Residual gaps

### 1. Alias count is still zero

This is not a V4 failure by itself. The V3 candidate set is already fairly
deduplicated, and the remaining high-similarity questions often differ by
topic content rather than only by phrasing.

The current V4 policy intentionally does not collapse:

- `What is trend?`
- `What is seasonality?`

into aliases, because they are distinct concepts even if the wording frame
matches.

### 2. Review answers are still only as good as the source text allows

The policy now picks better questions, but some generated short answers are
still generic because the scraped descriptions are short and high-level.

That is a downstream answer-generation limitation, not mainly a policy
bucket problem.

### 3. `24594` still has a large `analysis_only` share

That is partly intentional. The course description produces many generic
topic-level question frames that are valid enough to inspect but too thin
to serve directly.

## Assessment

The refinement pass is a real improvement over the first V4 attempt.

The main win is not more volume. The win is that the pipeline now makes a
clearer distinction between:

- questions worth curating
- questions safe enough to serve
- questions worth retaining only for analysis

That matches the stated V4 policy direction.
