# Data Products Scale Report Artifact

This is a compact inspection artifact derived from:

1. [data_products_scale_report.md](/code/docs/data_products_scale_report.md:1)
2. [bundle_data_products/scale_summary.json](/code/docs/bundle_data_products/scale_summary.json:1)
3. [bundle_data_products/manifest.json](/code/docs/bundle_data_products/manifest.json:1)

## Top-Line Summary

1. full-corpus current semantic run:
   - `537` course rows
   - `1501` chapter rows
   - `536` learning-outcome payload rows
   - `2218` nested learning outcomes
   - `1` execution error
2. bounded question-cache sample:
   - `21` question groups
   - `21` variations
   - `21` canonical answers
   - `50` validation logs
   - `5` runtime-eligible groups
3. bounded legacy semantic sample:
   - `92` topics
   - `103` edges
   - `202` predicted questions

## Inspection Table

| Run | Type | Core scale facts |
| --- | --- | --- |
| `20260413T215831Z` | bounded sample, legacy semantic | `10` courses, `20` chapters, `92` topics, `103` edges, `202` predicted questions |
| `20260414T025608Z` | bounded sample, learning outcomes | `3` courses, `25` chapters, `3` payload rows, `23` nested learning outcomes |
| `20260414T044551Z` | bounded sample, question cache | `21` groups, `21` variations, `21` answers, `50` validation logs, `5` runtime-eligible groups |
| `20260414T052429Z` | full corpus, learning outcomes | `537` courses, `1501` chapters, `536` payload rows, `2218` nested learning outcomes, `1` error |

## Ratios Worth Inspecting

| Measure | Value |
| --- | ---: |
| legacy topics per course | `9.2` |
| legacy predicted questions per course | `20.2` |
| legacy predicted questions per topic | `2.20` |
| question-cache groups per covered claim | `2.63` |
| question-cache validation logs per group | `2.38` |
| question-cache runtime-eligible groups per generated group | `23.8%` |
| full-corpus chapters per course | `2.80` |
| full-corpus successful payloads per course | `99.8%` |
| full-corpus nested outcomes per payload | `4.14` |

## Full-Corpus Learning Outcomes Distribution

| Statistic | Value |
| --- | ---: |
| minimum nested outcomes per payload | `0` |
| median nested outcomes per payload | `4` |
| mean nested outcomes per payload | `4.14` |
| maximum nested outcomes per payload | `12` |
| payloads with `0` nested outcomes | `70` |
| payloads with more than `10` nested outcomes | `2` |

## Why This Artifact Matters

1. it makes pipeline scale legible in one place
2. it distinguishes bounded sample runs from the full-corpus run
3. it highlights that nested semantic counts matter more than payload-row counts
4. it shows that question-cache expansion is already large enough to require
   quantitative review

## Recommended Next Review Step

Use this artifact as the front page for inspection, then open:

1. [data_products_scale_report.md](/code/docs/data_products_scale_report.md:1) for narrative interpretation
2. [bundle_data_products/scale_summary.json](/code/docs/bundle_data_products/scale_summary.json:1) for machine-readable counts
3. [bundle_data_products/README.md](/code/docs/bundle_data_products/README.md:1) for artifact-class descriptions
