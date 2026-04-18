# Question Generation Pseudo-Algorithm

This document summarizes the repo's implied pseudo-algorithm for generating learner question/answer pairs from a course.

## Overview

The pipeline treats generated questions as reusable learner-intent templates, not as personalized predictions. The goal is to build a traceable question cache with canonical answers grounded in the scraped course YAML.

In short:

`course YAML -> learning claims -> learner intents -> strict question groups -> variations + canonical answers -> cache-first runtime matching`

## Pseudo-Algorithm

1. Parse the scraped course YAML.  
   Use `title`, `summary`, `overview`, and especially `syllabus`.

2. Extract grounded learning claims.  
   Infer what a reasonably successful student would likely learn. Each claim must include confidence, rationale, and citations back to YAML fields.

3. For each claim, generate likely learner intents.  
   Turn the claim into a small set of common beginner questions. These are question templates or priors, not personalized predictions.

4. Split intents into strict question groups.  
   Only keep questions in the same group if all four of these match:
   - learner intent
   - requested knowledge or skill
   - pedagogical move
   - ideal answer content

   If any of these differ, create a new group.

5. Create one canonical question per group.  
   Example: `How do I create a vector in R?`

6. Generate several surface-form variations per group.  
   Example:
   - `Show me how to make a vector in R.`
   - `How can I create a vector?`

   These are paraphrases only, not new intents.

7. Write one canonical answer per group.  
   Keep it short, direct, and grounded in the course evidence. Attach citations and lineage:

   `course -> claim -> question_group -> variation -> canonical_answer`

8. Assign deterministic IDs.  
   - `question_group_id = course_id + claim_id + intent_slug`
   - `variation_id = question_group_id + normalized_variation_slug`
   - `canonical_answer_id = question_group_id + answer_version`

9. Store and export the cache artifacts.  
   Persist:
   - question groups
   - variations
   - canonical answers
   - provenance metadata

10. Runtime retrieval uses cache-first matching.  
    - normalize learner question
    - exact match against variations
    - semantic match against variations and canonical questions
    - if confidence is high, return canonical answer
    - otherwise fall back to the LLM

11. Log everything for improvement.  
    Track hits, misses, fallback frequency, grouping quality, and candidate new questions for cache warming.

## Key Constraint

The generated questions are not intended to represent all possible learner questions. They are a traceable, cache-first fast path built from course claims.

## V1 vs V2

### V1

The original approach is primarily claim-centered:
- extract learning claims from course YAML
- turn claims into learner questions
- group paraphrases into question groups
- attach canonical answers

Strengths:
- strong traceability
- simple lineage
- high alignment to course-described learning outcomes

Weaknesses:
- tends to overproduce syllabus-shaped questions
- underproduces vocabulary and jargon questions
- misses many natural "why" questions
- misses prerequisite and clarification questions that real learners often ask

### V2

The proposed V2 approach is learner-centered and friction-aware:
- extract learning claims
- extract learner-friction candidates from jargon, methods, acronyms, and process terms
- generate questions from both claims and friction terms
- cover multiple intent families such as definition, purpose, mechanism, comparison, and procedure

Strengths:
- closer to real learner behavior
- better coverage of terminology and confusion points
- better support for fast-path beginner Q/A

Tradeoffs:
- more candidate questions to rank and deduplicate
- more opportunities for drift if evidence-grounding is weak
- requires additional filtering and evaluation steps
