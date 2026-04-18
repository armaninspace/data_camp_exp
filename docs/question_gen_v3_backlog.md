# Question Generation V3 Backlog

This backlog implements the design in:

- [question_gen_v3_spec.md](/code/docs/req_bundle_3/question_gen_v3_spec.md)
- [question_gen_v3_codex_handoff.md](/code/docs/req_bundle_3/question_gen_v3_codex_handoff.md)
- [question_gen_v3_eval_rubric.md](/code/docs/req_bundle_3/question_gen_v3_eval_rubric.md)

## Assessment

The V3 direction makes sense.

The core improvement over V2 is not "better prompting." It is a better
decision structure:

- extract instructional structure first
- infer friction explicitly
- overgenerate candidates by slot
- reject low-value questions
- score by instructional value signals
- enforce balanced final selection

That directly addresses the V2 failures:

- too many generic definition questions
- too many broad heading paraphrases
- too few diagnostic, comparison, misconception, and transfer questions
- too many questions with thin answers

## Slice 1: Create a dedicated V3 package

- Add `src/course_pipeline/question_gen_v3/`
- Implement separate modules:
  - `models.py`
  - `normalize.py`
  - `extract_topics.py`
  - `extract_edges.py`
  - `extract_pedagogy.py`
  - `mine_friction.py`
  - `generate_candidates.py`
  - `filters.py`
  - `score_candidates.py`
  - `dedupe.py`
  - `select_final.py`
  - `pipeline.py`

Acceptance criteria:
- V3 code is isolated from V2 logic
- each stage can be run and inspected independently

## Slice 2: Add V3 config

- Add `question_gen_v3_config.yaml`
- Support:
  - confidence thresholds
  - score weights
  - quota policy
  - dedupe thresholds
  - per-slot generation counts

Acceptance criteria:
- score and selection behavior can be tuned without code edits

## Slice 3: Implement document normalization

- Convert normalized course rows into `CanonicalDocument`
- Preserve sections from syllabus when present
- Infer pseudo-sections if needed from overview

Acceptance criteria:
- each V3 run emits a normalized document artifact
- each document has at least one section

## Slice 4: Implement fine-grained topic extraction

- Extract subtopics per section
- Support topic types:
  - concept
  - procedure
  - tool
  - metric
  - diagnostic
  - comparison_axis
  - failure_mode
  - decision_point
  - prerequisite
- Preserve provenance and confidence

Acceptance criteria:
- broad chapter titles are split into finer topic units when possible
- topic records include source section ids and confidence

## Slice 5: Implement edge extraction

- Infer topic graph relations:
  - prerequisite_of
  - part_of
  - contrasts_with
  - confused_with
  - evaluated_by
  - uses
  - decision_depends_on
  - failure_revealed_by

Acceptance criteria:
- multi-method or evaluative sections produce at least some edges
- edge output is inspectable and grounded

## Slice 6: Implement pedagogy extraction

- Emit pedagogical profiles per topic
- Infer:
  - cognitive modes
  - abstraction level
  - notation load
  - procedure load
  - likely misconceptions
  - likely sticking points
  - evidence of mastery

Acceptance criteria:
- topics have pedagogical context beyond raw labels

## Slice 7: Implement friction mining

- Create `FrictionPoint` objects from:
  - topic types
  - contrasts
  - tradeoffs
  - diagnostics
  - prerequisite gaps
  - failure modes
  - broad-to-specific transitions
- Do not depend on explicit mistake wording

Acceptance criteria:
- friction points are created for method choice, comparison, or diagnostic-heavy material
- friction records explain why the question matters

## Slice 8: Implement slot-based candidate generation

- Generate by fixed slots:
  - novice_orientation
  - novice_definition
  - developing_procedural
  - developing_comparison
  - developing_misconception
  - proficient_diagnostic
  - proficient_transfer
- Overgenerate intentionally

Acceptance criteria:
- candidate pool is larger than the final selected set
- proficient questions are not just relabeled definition questions

## Slice 9: Implement low-value filters

- Reject:
  - broad heading paraphrases
  - thin-answer questions
  - unsupported questions
  - malformed questions
  - mastery-misaligned questions
  - weak duplicates
- Log structured rejection reasons

Acceptance criteria:
- rejected candidates are persisted and inspectable
- rejection reasons are human-readable

## Slice 10: Implement scoring and deduplication

- Score dimensions:
  - friction_value
  - specificity
  - answer_richness
  - mastery_fit
  - novelty
  - groundedness
- Deduplicate on semantic intent

Acceptance criteria:
- dimension-level scores are visible
- duplicate clusters are persisted

## Slice 11: Implement balanced selection

- Select final questions under quota constraints:
  - minimum friction-linked share
  - minimum advanced share
  - minimum proficient share
  - maximum definition share
- Emit diagnostics if quotas are not met

Acceptance criteria:
- final output cannot collapse into safe novice definitions
- selection summary explains what happened

## Slice 12: Add V3 run artifacts and CLI

- Add a V3 CLI command
- Persist:
  - normalized documents
  - topics
  - edges
  - pedagogy
  - friction points
  - raw candidates
  - rejected candidates
  - scored candidates
  - duplicate clusters
  - final selected questions
  - selection summary
  - run report

Acceptance criteria:
- a bounded V3 run can be executed from CLI
- intermediate artifacts are stored under a run directory

## Slice 13: Add review-bundle generation for V3

- Generate grounded Q/A review docs from selected questions
- Preserve scraped summary, overview, and syllabus text

Acceptance criteria:
- one review doc per course
- review docs are suitable for manual inspection

## Slice 14: Run bounded V3 on the target R time-series courses

- Run V3 on:
  - `24491`
  - `24593`
  - `24594`
- Produce:
  - run artifacts
  - review docs
  - inspection bundle
  - implementation report

Acceptance criteria:
- `docs/inspection_bundle_3` exists
- output set is visibly less generic than V2

## Execution Order

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 4
5. Slice 5
6. Slice 6
7. Slice 7
8. Slice 8
9. Slice 9
10. Slice 10
11. Slice 11
12. Slice 12
13. Slice 13
14. Slice 14
