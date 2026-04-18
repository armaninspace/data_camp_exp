# Bundle Data Products

This folder contains a compact bundle of representative pipeline work products
for external review and quantitative analysis.

The goal is not to mirror the full repository output tree. The goal is to give
a reviewer a small but meaningful set of files that show the main pipeline
stages and the main quality questions.

## What Is Included

### 1. Legacy Semantic Run

Folder:
[legacy_semantic_run_20260413T215831Z](/code/docs/bundle_data_products/legacy_semantic_run_20260413T215831Z)

This is the older pipeline shape that existed before the system was reduced and
reframed.

Included work products:

1. `courses.jsonl`
2. `chapters.jsonl`
3. `topics.jsonl`
4. `edges.jsonl`
5. `pedagogical_profiles.jsonl`
6. `predicted_questions.jsonl`
7. `errors.jsonl`

Why this matters:

1. it shows the older topic or graph or question-generation substrate
2. it helps quantify how the old semantic layer differed from the current one
3. it gives a baseline for measuring overclaim and artifact drift

Suggested quantitative review questions:

1. How many topics, edges, pedagogical profiles, and predicted questions were
   produced per course?
2. How sparse or dense is the old graph structure?
3. How repetitive are the old predicted questions?
4. How often do predicted questions appear unsupported or generic?

### 2. Learning Outcomes Sample Run

Folder:
[learning_outcomes_sample_run_20260414T025608Z](/code/docs/bundle_data_products/learning_outcomes_sample_run_20260414T025608Z)

This is the bounded cited learning-outcome extraction run used during early
semantic validation.

Included work products:

1. `courses.jsonl`
2. `chapters.jsonl`
3. `learning_outcomes.jsonl`
4. `learning_outcome_errors.jsonl`
5. per-course YAML inspection files:
   - [7630.yaml](/code/docs/bundle_data_products/learning_outcomes_sample_run_20260414T025608Z/learning_outcomes_yaml/7630.yaml)
   - [7631.yaml](/code/docs/bundle_data_products/learning_outcomes_sample_run_20260414T025608Z/learning_outcomes_yaml/7631.yaml)
   - [24370.yaml](/code/docs/bundle_data_products/learning_outcomes_sample_run_20260414T025608Z/learning_outcomes_yaml/24370.yaml)

Why this matters:

1. it shows the first current-generation semantic layer
2. it exposes citation use directly
3. it is small enough for close manual review

Suggested quantitative review questions:

1. How many learning outcomes are produced per course?
2. How many citations support each outcome?
3. What is the distribution of `knowledge_type`, `process_level`, `dok_level`,
   and `solo_level`?
4. How often do outcomes seem redundant or too broad?
5. How often are outcomes strongly grounded in chapter evidence versus only
   course-level evidence?

### 3. Question Cache Sample Run

Folder:
[question_cache_sample_run_20260414T044551Z](/code/docs/bundle_data_products/question_cache_sample_run_20260414T044551Z)

This is the corrected staged question-cache run used for quality diagnosis.

Included work products:

1. `claim_question_groups.jsonl`
2. `question_group_variations.jsonl`
3. `canonical_answers.jsonl`
4. `question_cache_validation_logs.jsonl`
5. `claim_coverage_audit.jsonl`
6. `question_cache_errors.jsonl`
7. per-course YAML inspection file:
   - [7630.yaml](/code/docs/bundle_data_products/question_cache_sample_run_20260414T044551Z/question_cache_yaml/7630.yaml)

Why this matters:

1. it shows the decomposition from learning outcomes into atomic question groups
2. it shows runtime acceptance versus rejection
3. it exposes validator outcomes and coverage accounting

Suggested quantitative review questions:

1. How many question groups are produced per learning outcome claim?
2. What fraction of canonical answers pass `answer_fit`?
3. What fraction pass `grounding`?
4. What fraction of groups become runtime-eligible?
5. How many claims end up with no accepted group?
6. How repetitive are canonical questions across claims?
7. What are the most common validator failure reasons?

### 4. Full-Corpus Learning Outcomes Run

Folder:
[learning_outcomes_full_corpus_run_20260414T052429Z](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z)

This is the full-corpus cited learning-outcomes run.

Included work products:

1. `courses.jsonl`
2. `chapters.jsonl`
3. `learning_outcomes.jsonl`
4. `learning_outcome_errors.jsonl`
5. sample per-course YAMLs from the full run:
   - [7630.yaml](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z/learning_outcomes_yaml/7630.yaml)
   - [205171.yaml](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z/learning_outcomes_yaml/205171.yaml)
   - [275594.yaml](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z/learning_outcomes_yaml/275594.yaml)
   - [121395.yaml](/code/docs/bundle_data_products/learning_outcomes_full_corpus_run_20260414T052429Z/learning_outcomes_yaml/121395.yaml)

Why this matters:

1. it gives the true scale distribution for the current semantic layer
2. it allows reviewer-level aggregate analysis
3. it includes the final error file for corpus completion analysis

Suggested quantitative review questions:

1. What is the distribution of learning-outcome counts per course?
2. What is the error rate across the corpus?
3. What taxonomic distributions dominate the corpus?
4. How often do courses have weak coverage notes or obvious evidence gaps?
5. How often do low-information or malformed source courses still receive
   plausible-looking outcomes?

## Machine-Readable Inventory

See:
[manifest.json](/code/docs/bundle_data_products/manifest.json:1)

This file lists every bundled file, its size, and JSONL record counts where
applicable.

There is also a higher-level report summary here:
[scale_summary.json](/code/docs/bundle_data_products/scale_summary.json:1)

It can be regenerated with:

```bash
python scripts/generate_data_products_scale_summary.py
```

## What To Quantify

If someone is writing a quantitative report, the most useful metrics are:

1. record counts by artifact class
2. per-course output cardinality
3. validator pass or fail rates
4. coverage rates
5. citation counts per semantic claim
6. taxonomy distributions
7. error counts and error categories
8. duplication or repetition rates in generated text

## Recommended Report Structure

1. Corpus and run overview
2. Learning-outcome output distributions
3. Question-cache quality and validator results
4. Legacy versus current pipeline comparison
5. Error analysis
6. Reviewer judgment on trustworthiness and readiness

## Notes

1. The current production-quality semantic substrate is learning outcomes.
2. The question-cache layer is implemented but still quality-limited.
3. The legacy semantic run is included for comparison, not as a recommended
   target architecture.
