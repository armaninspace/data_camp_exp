# Question Generation Algorithm V2 Backlog

This backlog implements the design in
[question_gen_algo_v2.md](/code/docs/question_gen_algo_v2.md:1).

The goal is to add a new candidate-question generation stage that is:
- learner-centered
- chapter-aware
- topic-aware
- friction-aware
- natural-language-oriented
- provenance-preserving

This backlog intentionally treats candidate question generation as separate from
the existing question-cache layer.

## Slice 1: Add V2 artifact schemas

- Add typed schemas for:
  - source evidence excerpts
  - generation basis
  - extracted topics
  - learner-friction candidates
  - candidate questions
- Keep output fields aligned with `question_gen_algo_v2.md`.

Acceptance criteria:
- schemas can represent chapter context, topic context, provenance, and score
- serialized artifacts are JSONL-friendly

## Slice 2: Add semantic extraction stage

- Implement a stage that reads normalized course data and extracts:
  - topics
  - prerequisites
  - contrasts
  - confusions
  - learner-friction candidates
- Prefer `syllabus` when present.
- Fall back to `overview` when `syllabus` is sparse or missing.

Acceptance criteria:
- each course produces inspectable topic and friction artifacts
- extraction preserves source evidence excerpts
- learner-friction candidates are explicit, not implicit

## Slice 3: Add candidate-question generation stage

- Generate candidate questions from:
  - chapter context
  - topics
  - friction candidates
  - contrasts
  - confusions
  - prerequisites
- Use the V2 generation unit:
  - `(chapter, topic, question_type, mastery_band)`
- Do not generate directly from `claim -> paraphrase`.

Acceptance criteria:
- outputs include definition, purpose, how-to, comparison, misconception, and interpretation questions
- questions remain grounded in source text

## Slice 4: Add natural-language preference rules

- Enforce preference for learner-natural wording.
- Penalize syllabus-shaped, analyst-shaped, or awkward phrasing.
- Prefer concise questions that sound like what a learner would type into a chat box.

Acceptance criteria:
- generated questions read like natural learner questions
- claim-restatement style prompts are reduced

## Slice 5: Add scoring, deduping, and canonicalization

- Score candidate questions on:
  - grounding
  - learner likelihood
  - pedagogical value
  - distinctiveness
  - answerability
  - naturalness
- Deduplicate near-duplicates.
- Keep one canonical candidate per intent for this stage.

Acceptance criteria:
- duplicate questions are filtered
- low-quality or weakly grounded questions are removed
- final artifacts are stable enough for bounded reruns

## Slice 6: Add run artifacts and report output

- Write run artifacts under `data/pipeline_runs/<run_id>/`.
- Export:
  - `courses.jsonl`
  - `chapters.jsonl`
  - `topics.jsonl`
  - `learner_friction_candidates.jsonl`
  - `candidate_questions.jsonl`
  - `question_gen_v2_report.md`
  - `errors.jsonl`

Acceptance criteria:
- artifacts are inspectable without the database
- report summarizes counts by course, question type, and mastery band

## Slice 7: Add CLI wiring

- Add a CLI command to run question generation V2.
- Add support for bounded runs and course filtering.
- Keep the V2 stage separate from `build-question-cache`.

Acceptance criteria:
- a bounded run can be executed from the command line
- specific course IDs can be targeted

## Slice 8: Add review-bundle export

- Add a review export that turns candidate questions into a per-course Markdown bundle.
- For each course, include:
  - Q/A pairs
  - scraped summary
  - scraped overview
  - scraped syllabus text
- Keep this as a review artifact, not as the canonical runtime layer.

Acceptance criteria:
- one self-contained Markdown file exists per course
- questions are learner-centered and answers are grounded

## Slice 9: Run bounded V2 generation for time-series R courses

- Run V2 for:
  - `24491`
  - `24593`
  - `24594`
- Build review docs from the resulting artifacts.
- Produce a short run report.

Acceptance criteria:
- new Q/A docs exist for each of the three courses
- outputs visibly improve over the earlier claim-shaped questions

## Slice 10: Document residual gaps

- Record what V2 still does not solve well.
- Note likely next improvements:
  - better topic normalization across chapters
  - stronger misconception detection
  - answer generation or ranking as a later layer

Acceptance criteria:
- final report is honest about remaining limitations

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
