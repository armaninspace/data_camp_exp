# Question Generation Algorithm V2 Proposal

## Problem

The current question-generation approach is too claim-centered.

It starts from extracted learning outcomes and turns them into learner questions. That keeps the output aligned to course content, but it tends to miss the kinds of questions a real learner actually asks while trying to understand the material.

In practice, this leads to undercoverage of:
- vocabulary questions
- motivation or "why" questions
- jargon clarification questions
- comparison questions
- procedural setup questions
- interpretation questions

For example, in `Forecasting in R (24491)`, a realistic learner may ask:
- `What is smoothing?`
- `Why do we need smoothing?`
- `What is exponential smoothing?`
- `What other kinds of smoothing are there?`
- `What does ARIMA stand for?`
- `What is a benchmark?`
- `What is a benchmark method?`
- `How do I visualize a time series?`

These are natural learner questions, but the current algorithm underproduces them because it derives questions too literally from claims such as "apply exponential smoothing" or "apply ARIMA models."

## Goal

Generate questions that are still grounded in the scraped course description, but are much closer to what a typical learner would actually ask.

The proposed V2 algorithm should:
- preserve traceability to course evidence
- stay grounded in scraped YAML
- better cover beginner-natural question forms
- model likely learner friction around terminology and concepts
- keep the existing cache-friendly structure of question groups, variations, and canonical answers

## Core Shift

The main change is:

Instead of generating questions only from learning claims, generate them from both:
- course claims
- learner-friction signals in the course text

This means the system should treat the course YAML not only as a description of what is taught, but also as a source of clues about what learners will find confusing, unfamiliar, or worth asking about.

## Proposed V2 Pipeline

1. Parse the course YAML.  
   Use `title`, `summary`, `overview`, `subjects`, and especially `syllabus`.

2. Extract grounded learning claims.  
   Keep the current step that infers what a reasonably successful student would likely learn.

3. Extract learner-friction candidates from the YAML.  
   Identify terms, phrases, and concepts that are likely to trigger learner questions.

   These include:
   - technical terms
   - abbreviations and acronyms
   - named methods
   - statistical tests
   - tools or packages
   - contrastive concepts
   - process steps

   Example candidates from `24491`:
   - `time series`
   - `forecasting`
   - `benchmark methods`
   - `forecast accuracy`
   - `exponential smoothing`
   - `ARIMA`
   - `white noise`
   - `Ljung-Box test`
   - `trend`
   - `seasonality`
   - `repeated cycles`

4. Build a concept-intent map.  
   For each claim or friction term, generate possible learner intents.

   Recommended intent families:
   - definition: `What is X?`
   - terminology expansion: `What does X stand for?`
   - purpose: `Why do we use X?`
   - mechanism: `How does X work?`
   - comparison: `How is X different from Y?`
   - procedure: `How do I do X in R?`
   - interpretation: `What does X tell me?`
   - selection: `When should I use X?`
   - diagnostic: `How do I know if X is happening?`
   - prerequisite: `What do I need to know before using X?`

5. Generate beginner-natural candidate questions.  
   Use plain learner wording, not syllabus wording.

   Prefer:
   - `What is exponential smoothing?`
   - `Why do we use benchmark methods?`
   - `How do I visualize a time series in R?`

   Avoid overly formal claim restatements like:
   - `How do I apply exponential smoothing methods to forecast time series data in R?`

6. Score candidate questions for learner-likeness.  
   Rank questions higher if they are:
   - directly triggered by jargon in the course text
   - likely for beginners or early intermediates
   - short and naturally phrased
   - useful as fast-path cache candidates

   Rank lower if they are:
   - awkward restatements of learning outcomes
   - too broad to answer well from course evidence
   - too advanced relative to the course level
   - redundant with another question group

7. Filter for evidence-groundedness.  
   Keep only questions whose answer can be supported by the scraped YAML and course evidence, or by minimal explanation directly anchored to the named concepts in the YAML.

   This is important because V2 should be more learner-centered without drifting into unguided domain tutoring.

8. Group questions using strict equivalence rules.  
   Preserve the existing grouping rule:
   two questions belong in the same group only if they share the same:
   - learner intent
   - requested knowledge or skill
   - pedagogical move
   - ideal answer content

9. Create canonical question groups.  
   For each group, store:
   - canonical question
   - learner-friendly variations
   - pedagogical move
   - citations
   - source claim or source friction term

10. Create canonical answers.  
    Answers should remain:
    - short
    - direct
    - beginner-friendly
    - traceable to evidence

    The answer layer should distinguish answer styles such as:
    - short definition
    - short why-explanation
    - quick comparison
    - how-to starter
    - interpretation hint

11. Store lineage with broader provenance.  
    Preserve `course -> claim -> question_group -> variation -> canonical_answer`, but allow a question to also be linked to:
    - a friction term
    - a jargon span
    - a course section that likely triggered the question

12. Evaluate on learner realism, not just semantic cleanliness.  
    In addition to grouping quality, measure:
    - learner-likeness
    - jargon coverage
    - why-question coverage
    - prerequisite-question coverage
    - redundancy rate
    - answer usefulness

## New Data Elements

V2 likely needs extra intermediate artifacts.

### Learner Friction Candidate

```yaml
friction_candidate:
  course_id: "24491"
  candidate_id: "24491_fc_01"
  text: "ARIMA"
  candidate_type: "acronym"
  source_field: "overview"
  evidence: "ARIMA models"
  confidence: 0.91
```

### Concept-Intent Candidate

```yaml
concept_intent_candidate:
  course_id: "24491"
  candidate_id: "24491_ci_01"
  source_type: "friction_candidate"
  source_id: "24491_fc_01"
  concept: "ARIMA"
  intent_family: "terminology_expansion"
  canonical_question_draft: "What does ARIMA stand for?"
  confidence: 0.88
```

These artifacts make it possible to audit why a question was generated.

## Example: Forecasting in R (`24491`)

### Current-style questions

- How do you start analyzing a time series in R?
- What is an ARIMA model used for?
- How are ARIMA and exponential smoothing different?

These are fine, but incomplete.

### V2-style question set

- What is forecasting?
- What is a time series?
- How do I visualize a time series in R?
- What is trend in a time series?
- What is seasonality?
- What are repeated cycles?
- What is white noise?
- What is the Ljung-Box test used for?
- What is a benchmark forecast?
- What is a benchmark method?
- Why do we use benchmark methods?
- What is forecast accuracy?
- Why does forecast accuracy matter?
- What is smoothing?
- Why do we use smoothing?
- What is exponential smoothing?
- How does exponential smoothing work?
- What other kinds of smoothing are there?
- What does ARIMA stand for?
- What is an ARIMA model?
- How is ARIMA different from exponential smoothing?
- When would I use ARIMA instead of exponential smoothing?

This set is much closer to the likely question surface of a real learner.

## Design Principles for V2

1. Grounded, but not literal.  
   The system should stay anchored to the course text without simply paraphrasing claims.

2. Learner-centered, not syllabus-centered.  
   Prefer the question a confused learner would ask over the sentence an analyst would write.

3. Cover friction, not just mastery.  
   Questions should reflect likely confusion points, not only intended outcomes.

4. Prefer natural language.  
   Use short, plain-English phrasing that sounds like a real learner.

5. Keep strict answer-group boundaries.  
   Do not collapse definition, comparison, and why-questions into one group just because they mention the same term.

6. Preserve traceability.  
   Every generated question should still point back to course evidence and its generation rationale.

## Suggested Prompting Strategy

Instead of one prompt that maps YAML directly to learning outcomes and then questions, V2 should use at least three prompt stages:

1. `claims_from_course_yaml`
   Extract likely learning outcomes with citations.

2. `learner_friction_from_course_yaml`
   Extract terms, concepts, and phrases likely to trigger learner questions.

3. `questions_from_claims_and_friction`
   Generate learner-natural questions across intent families, grounded in both claims and friction candidates.

This separation should improve both coverage and auditability.

## Risks

- Overgeneration of trivial questions
- Drift into questions not well supported by the course description
- Redundant questions across closely related jargon terms
- Increased need for ranking and deduplication

These are manageable if the pipeline includes scoring, filtering, and strict equivalence grouping.

## Recommendation

Adopt V2 as a layered question-generation pipeline:

`course YAML -> learning claims + learner-friction candidates -> concept-intent candidates -> learner-natural questions -> strict question groups -> canonical answers`

This preserves the current traceable cache design while making the generated questions substantially more realistic for actual learners.
