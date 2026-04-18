# Refactor Naming Map

## Purpose

This document defines the stable domain vocabulary for the active question
pipeline.

The repo still contains historical package names such as `question_gen_v3`,
`question_gen_v4`, `question_gen_v4_1`, and `question_ledger_v6`. Those names
reflect implementation history, not the intended long-term architecture.

The stable package surface introduced for refactoring is:

- [questions/candidates.py](/code/src/course_pipeline/questions/candidates.py)
- [questions/policy.py](/code/src/course_pipeline/questions/policy.py)
- [questions/ledger.py](/code/src/course_pipeline/questions/ledger.py)
- [questions/inspection.py](/code/src/course_pipeline/questions/inspection.py)

## Naming Policy

Use these rules when naming active pipeline components:

1. Name by responsibility, not by generation number.
2. Prefer one stable domain term per stage.
3. Treat version labels as migration details, not API names.
4. Keep orchestration code importing the stable `course_pipeline.questions.*`
   surface.

## Mapping

### Input And Standardization

- current stable term: `standardization`
- current code:
  - [normalize.py](/code/src/course_pipeline/normalize.py)
  - [pipeline.py](/code/src/course_pipeline/pipeline.py)

### Topic, Edge, Pedagogy, And Friction Extraction

- stable term: `candidate extraction`
- implementation package today: [question_gen_v3](/code/src/course_pipeline/question_gen_v3)
- stable wrapper: [questions/candidates.py](/code/src/course_pipeline/questions/candidates.py)

### Question Candidate Generation, Filtering, Scoring, Dedupe, Selection

- stable term: `candidate generation`
- implementation package today: [question_gen_v3](/code/src/course_pipeline/question_gen_v3)
- stable wrapper: [questions/candidates.py](/code/src/course_pipeline/questions/candidates.py)

### Visibility, Serveability, Canonicalization, Retention

- stable term: `policy classification`
- implementation packages today:
  - [question_gen_v4](/code/src/course_pipeline/question_gen_v4)
  - [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)
- stable wrapper: [questions/policy.py](/code/src/course_pipeline/questions/policy.py)

### Foundational Anchor Detection And Entry Coverage

- stable term: `coverage enforcement`
- implementation package today: [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)
- stable wrapper: [questions/policy.py](/code/src/course_pipeline/questions/policy.py)

### Ledger Assembly And Derived Views

- stable term: `question ledger`
- implementation package today: [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)
- stable wrapper: [questions/ledger.py](/code/src/course_pipeline/questions/ledger.py)

### Bundle And Report Rendering

- stable term: `inspection publishing`
- implementation packages today:
  - [question_gen_v3](/code/src/course_pipeline/question_gen_v3)
  - [question_gen_v4](/code/src/course_pipeline/question_gen_v4)
  - [question_gen_v4_1](/code/src/course_pipeline/question_gen_v4_1)
  - [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)
- stable wrapper: [questions/inspection.py](/code/src/course_pipeline/questions/inspection.py)

## Current Migration Rule

Until the internal moves are complete:

- versioned packages may continue to exist as implementation homes
- orchestration code should import through `course_pipeline.questions.*`
- docs should describe the stable domain names first

## End-State Goal

The eventual end state is:

- stable domain package names in both architecture and implementation
- no runtime dependence on version-labeled package imports outside the wrapper
  compatibility layer
- version labels retained only in migration notes, if at all
