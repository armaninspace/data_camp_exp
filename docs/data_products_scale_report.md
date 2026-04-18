# Pipeline Data Products Scale Report

## Executive Summary

The bundled pipeline artifacts show that output scale is already substantial
enough to require automated evaluation and sampling-based review.

The main scale facts are:

1. the full-corpus current semantic run produced `537` course records,
   `1501` chapter records, and `536` course-level learning-outcome payloads
2. those `536` course-level payloads contain `2218` nested learning outcomes,
   which is the better measure of semantic volume
3. the bounded question-cache sample expanded `8` claims into `21` question
   groups, `21` variations, `21` canonical answers, and `50` validation logs
4. the legacy semantic run already showed multiplicative artifact growth on only
   `10` courses, including `92` topics and `202` predicted questions
5. execution-error counts are low, but low execution-error counts do not imply
   semantic quality

The practical conclusion is:

1. scale is no longer hypothetical
2. manual review alone will not be sufficient
3. future reporting should distinguish clearly between bounded sample evidence
   and full-corpus evidence

## Methodology

Counts in this report were derived from the bundled artifacts in
[docs/bundle_data_products](/code/docs/bundle_data_products).

Counting rules:

1. JSONL artifact counts are line counts of non-empty JSONL rows
2. nested learning-outcome counts are the sum of `len(learning_outcomes)` inside
   each course-level payload row
3. bundled YAML inspection files are counted only as inspection artifacts, not
   as semantic records
4. ratios are computed from the bundled counts, not from inferred estimates

Source files used:

1. [manifest.json](/code/docs/bundle_data_products/manifest.json:1)
2. [scale_summary.json](/code/docs/bundle_data_products/scale_summary.json:1)
3. bundled JSONL files under:
   - [legacy_semantic_run_20260413T215831Z](/code/docs/bundle_data_products/legacy_semantic_run_20260413T215831Z)
   - [learning_outcomes_sample_run_20260414T025608Z](/code/docs/bundle_data_products/learning_outcomes_sample_run_20260414T025608Z)
   - [question_cache_sample_run_20260414T044551Z](/code/docs/bundle_data_products/question_cache_sample_run_20260414T044551Z)
   - [learning_outcomes_full_corpus_run_20260414T052429Z](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z)

## Run Inventory

| Run | Type | Course rows | Chapter rows | Primary semantic rows | Validation or error rows | Bundled YAML inspections |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `20260413T215831Z` | bounded sample, legacy semantic | 10 | 20 | 92 topics, 103 edges, 20 pedagogical profiles, 202 predicted questions | 0 errors | 0 |
| `20260414T025608Z` | bounded sample, learning outcomes | 3 | 25 | 3 learning-outcome payload rows, 23 nested learning outcomes | 0 errors | 3 |
| `20260414T044551Z` | bounded sample, question cache | not included in bundle as course rows | not included in bundle as chapter rows | 21 question groups, 21 variations, 21 canonical answers | 50 validation logs, 8 coverage audits, 0 errors | 1 |
| `20260414T052429Z` | full corpus, learning outcomes | 537 | 1501 | 536 learning-outcome payload rows, 2218 nested learning outcomes | 1 error | 4 |

## Artifact Count Tables

### Legacy Semantic Run `20260413T215831Z`

This is a bounded sample run of the older semantic stack.

| Artifact | Count |
| --- | ---: |
| `courses.jsonl` | 10 |
| `chapters.jsonl` | 20 |
| `topics.jsonl` | 92 |
| `edges.jsonl` | 103 |
| `pedagogical_profiles.jsonl` | 20 |
| `predicted_questions.jsonl` | 202 |
| `errors.jsonl` | 0 |

Interpretation:

1. even on `10` courses, the old stack multiplied quickly into topic, edge, and
   generated-question artifacts
2. the old `predicted_questions` layer was especially prolific relative to the
   small course count

### Learning-Outcomes Sample Run `20260414T025608Z`

This is a bounded sample run of the current learning-outcomes layer.

| Artifact | Count |
| --- | ---: |
| `courses.jsonl` | 3 |
| `chapters.jsonl` | 25 |
| `learning_outcomes.jsonl` payload rows | 3 |
| nested learning outcomes inside payloads | 23 |
| `learning_outcome_errors.jsonl` | 0 |
| bundled YAML inspection files | 3 |

Per-course nested learning outcomes in the sample:

| Course | Title | Nested learning outcomes |
| --- | --- | ---: |
| `7630` | `Introduction to R` | 8 |
| `7631` | `Introduction to Python` | 3 |
| `24370` | `Statistician in R` | 12 |

Interpretation:

1. course-level payload rows understate semantic volume
2. even in a 3-course run, nested outcomes already total `23`

### Question-Cache Sample Run `20260414T044551Z`

This is a bounded sample run of the corrected staged question-cache layer.

| Artifact | Count |
| --- | ---: |
| `claim_question_groups.jsonl` | 21 |
| `question_group_variations.jsonl` | 21 |
| `canonical_answers.jsonl` | 21 |
| `question_cache_validation_logs.jsonl` | 50 |
| `claim_coverage_audit.jsonl` | 8 |
| `question_cache_errors.jsonl` | 0 |
| bundled YAML inspection files | 1 |

Additional runtime-quality counts from the bundled sample:

| Measure | Count |
| --- | ---: |
| groups with `validator_status=validated` | 5 |
| answers passing both fit and grounding | 5 |
| variations accepted for runtime | 5 |
| claims with produced question groups | 8 |

Interpretation:

1. the cache layer expands one bounded course into dozens of intermediate and
   validator artifacts
2. runtime-eligible artifacts are a strict subset of generated artifacts

### Full-Corpus Learning-Outcomes Run `20260414T052429Z`

This is the only bundled full-corpus current semantic run.

| Artifact | Count |
| --- | ---: |
| `courses.jsonl` | 537 |
| `chapters.jsonl` | 1501 |
| `learning_outcomes.jsonl` payload rows | 536 |
| nested learning outcomes inside payloads | 2218 |
| `learning_outcome_errors.jsonl` | 1 |
| bundled YAML inspection files | 4 |

Interpretation:

1. `536` payload rows already imply substantial scale
2. the more informative semantic count is `2218` nested learning outcomes

## Scale Ratios

### Legacy Semantic Ratios

| Ratio | Value |
| --- | ---: |
| chapters per course | `20 / 10 = 2.0` |
| topics per course | `92 / 10 = 9.2` |
| predicted questions per course | `202 / 10 = 20.2` |
| predicted questions per topic | `202 / 92 = 2.20` |
| edges per topic | `103 / 92 = 1.12` |

### Question-Cache Sample Ratios

| Ratio | Value |
| --- | ---: |
| question groups per covered claim | `21 / 8 = 2.63` |
| validation logs per question group | `50 / 21 = 2.38` |
| runtime-eligible groups per generated group | `5 / 21 = 23.8%` |
| runtime-eligible answers per generated answer | `5 / 21 = 23.8%` |

### Full-Corpus Learning-Outcomes Ratios

| Ratio | Value |
| --- | ---: |
| chapters per course | `1501 / 537 = 2.80` |
| successful payload rows per course row | `536 / 537 = 99.8%` |
| nested learning outcomes per successful payload | `2218 / 536 = 4.14` |
| nested learning outcomes per course row | `2218 / 537 = 4.13` |

### Full-Corpus Learning-Outcomes Distribution

For nested learning outcomes per course payload:

| Statistic | Value |
| --- | ---: |
| minimum | 0 |
| median | 4 |
| mean | 4.14 |
| maximum | 12 |
| courses with more than 10 outcomes | 2 |
| courses with 0 outcomes | 70 |

Interpretation:

1. the median course is modest in output volume
2. the corpus still contains a meaningful tail of zero-outcome payloads
3. nested counts provide a more accurate picture of reviewer workload than
   payload-row counts alone

## Review Burden Interpretation

The counts imply three different review burdens.

### 1. Manual Close Reading Burden

This is appropriate for:

1. bundled per-course YAML inspections
2. a handful of bounded sample courses
3. representative failure cases

### 2. Sampling Burden

This is appropriate for:

1. the `2218` nested learning outcomes in the full-corpus run
2. the bounded question-cache artifacts, where each claim can expand into
   several intermediate records
3. spot-checking citation grounding and redundancy

### 3. Automated Quantitative Burden

This is necessary for:

1. corpus-wide distributions
2. validator pass rates
3. duplication rates
4. zero-output course analysis
5. run-over-run comparison

The core takeaway is that the current data-product scale already exceeds what
can be responsibly understood through ad hoc manual browsing alone.

## Error Footprint

Using the bundled runs:

| Run | Error count |
| --- | ---: |
| legacy semantic sample `20260413T215831Z` | 0 |
| learning-outcomes sample `20260414T025608Z` | 0 |
| question-cache sample `20260414T044551Z` | 0 |
| full-corpus learning-outcomes `20260414T052429Z` | 1 |

Important caveat:

Low execution-error counts indicate pipeline stability, not semantic quality.

## Main Findings

1. the current production semantic substrate already operates at corpus scale
2. nested learning-outcome counts are the correct scale unit for semantic
   review, not just payload-row counts
3. the question-cache layer multiplies artifacts quickly even in a bounded
   sample and therefore needs quantitative validation, not just manual review
4. the legacy semantic pipeline also expanded rapidly, which helps explain why
   artifact count reporting is necessary before quality claims
5. the current scale justifies automated evaluation and structured sampling as
   the next reporting layer

## Recommended Next Step

Use this scale report as the front section of a broader evaluation package, then
follow it with:

1. learning-outcome quality sampling
2. question-cache validator outcome analysis
3. duplication and redundancy analysis
4. zero-output and weak-evidence course analysis

## Refresh Note

The machine-readable summary for this report can be regenerated with:

```bash
python scripts/generate_data_products_scale_summary.py
```
