# Data Products Report Proposal

## Purpose

This proposed report is designed to quantify the scale of the pipeline outputs
using the bundled artifacts in
[docs/bundle_data_products](/code/docs/bundle_data_products).

The emphasis is simple:

1. count what the pipeline produces
2. show how artifact volume changes across stages
3. show how bounded sample runs compare to the larger corpus run
4. make the current scale legible before deeper quality analysis

## Proposed Report Title

`Pipeline Data Products Scale Report`

## Proposed Audience

This report is aimed at:

1. technical reviewers
2. research or evaluation stakeholders
3. product or infrastructure stakeholders who need to understand pipeline scale
4. anyone deciding where deeper quality review should focus

## Core Reporting Question

How many structured artifacts does the pipeline produce at each stage, and what
does that imply about scale, review burden, and downstream evaluation scope?

## Recommended Report Sections

### 1. Executive Summary

This section should answer:

1. how many courses were processed in each included run
2. how many artifacts were produced in each run
3. where scale expands most sharply
4. where errors remain low versus where quality risk remains high

### 2. Run Inventory

This section should include a table with one row per bundled run:

1. legacy semantic run `20260413T215831Z`
2. learning-outcomes sample run `20260414T025608Z`
3. question-cache sample run `20260414T044551Z`
4. full-corpus learning-outcomes run `20260414T052429Z`

Suggested columns:

1. run name
2. run type
3. course records
4. chapter records
5. primary semantic records
6. validation or error records
7. per-course YAML inspection files included in the bundle

### 3. Artifact Count Tables

This is the core of the report.

Each artifact class should be counted explicitly.

#### Legacy Semantic Run `20260413T215831Z`

From [manifest.json](/code/docs/bundle_data_products/manifest.json:1):

1. `courses.jsonl`: `10`
2. `chapters.jsonl`: `20`
3. `topics.jsonl`: `92`
4. `edges.jsonl`: `103`
5. `pedagogical_profiles.jsonl`: `20`
6. `predicted_questions.jsonl`: `202`
7. `errors.jsonl`: `0`

Why this is useful:

1. it shows how quickly the old pipeline multiplied records
2. it highlights the old question-generation scale relative to course count

#### Learning-Outcomes Sample Run `20260414T025608Z`

1. `courses.jsonl`: `3`
2. `chapters.jsonl`: `25`
3. `learning_outcomes.jsonl`: `3`
4. `learning_outcome_errors.jsonl`: `0`
5. bundled YAML inspections: `3`

Important note:

`learning_outcomes.jsonl` contains one payload per course, not one row per
learning outcome. The report should separately count the nested learning
outcomes inside those payloads if deeper scale analysis is needed.

#### Question-Cache Sample Run `20260414T044551Z`

1. `claim_question_groups.jsonl`: `21`
2. `question_group_variations.jsonl`: `21`
3. `canonical_answers.jsonl`: `21`
4. `claim_coverage_audit.jsonl`: `8`
5. `question_cache_validation_logs.jsonl`: `50`
6. `question_cache_errors.jsonl`: `0`
7. bundled YAML inspections: `1`

Why this is useful:

1. it shows the expansion from claims into groups, variations, answers, and
   validations
2. it highlights reviewer burden from intermediate generated artifacts

#### Full-Corpus Learning-Outcomes Run `20260414T052429Z`

1. `courses.jsonl`: `537`
2. `chapters.jsonl`: `1501`
3. `learning_outcomes.jsonl`: `536`
4. `learning_outcome_errors.jsonl`: `1`
5. bundled YAML inspections: `4`

Why this is useful:

1. it shows the true current scale of the production semantic substrate
2. it gives corpus-level scope for downstream evaluation

### 4. Derived Scale Ratios

This section should compute ratios, not just raw counts.

Recommended ratios:

1. chapters per course
2. topics per course in the legacy run
3. predicted questions per course in the legacy run
4. predicted questions per topic in the legacy run
5. question groups per claim in the question-cache sample
6. validation logs per question group in the question-cache sample
7. learning-outcome payload success rate in the full-corpus run

Example scale observations already visible:

1. legacy predicted questions:
   `202 questions / 10 courses = 20.2 questions per course`
2. legacy topics:
   `92 topics / 10 courses = 9.2 topics per course`
3. legacy edges:
   `103 edges / 92 topics = 1.12 edges per topic`
4. full-corpus chapters:
   `1501 chapters / 537 courses = about 2.8 chapters per course`
5. full-corpus learning-outcome payload completion:
   `536 successful outputs / 537 courses = about 99.8%`
6. question-cache validation density:
   `50 validation logs / 21 question groups = about 2.38 validation logs per group`

### 5. Review Burden Interpretation

This section should convert counts into implications.

Examples:

1. full-corpus learning outcomes already imply hundreds of course-level semantic
   payloads to review
2. question-cache generation expands one bounded course into dozens of
   intermediate records
3. the legacy semantic stack produced substantial multiplicative growth even on
   only `10` courses

This section should answer:

1. what can feasibly be manually reviewed
2. what requires sampling
3. what requires automated quantitative checks

### 6. Error Footprint

This section should remain simple and factual.

Using the bundled data:

1. legacy semantic sample errors: `0`
2. learning-outcomes sample errors: `0`
3. question-cache sample errors: `0`
4. full-corpus learning-outcomes errors: `1`

This section should note that low execution-error counts do not imply high
semantic quality.

### 7. Recommended Figures

Suggested visuals:

1. bar chart of artifact counts by run
2. stacked bar chart of artifact classes within each run
3. ratio chart showing multiplicative expansion by stage
4. small completion chart for the full-corpus learning-outcomes run

## Suggested Key Takeaways

The report should likely surface these themes:

1. the pipeline already produces artifacts at meaningful scale
2. the current learning-outcomes layer is the main corpus-scale semantic output
3. the question-cache layer multiplies artifacts quickly even in bounded runs
4. artifact volume alone justifies automated evaluation and sampling-based
   review
5. scale is no longer hypothetical; quality review now needs to catch up to
   output volume

## Minimal Report Version

If the reviewer wants the shortest useful version, it should include only:

1. one table of artifact counts by run
2. one table of scale ratios
3. one short interpretation section
4. one short error summary

## Source For This Proposal

This proposal is based on:

1. [docs/bundle_data_products/README.md](/code/docs/bundle_data_products/README.md:1)
2. [docs/bundle_data_products/manifest.json](/code/docs/bundle_data_products/manifest.json:1)
3. the bundled sample artifacts for legacy semantic outputs, learning outcomes,
   question cache outputs, and the full-corpus learning-outcomes run
