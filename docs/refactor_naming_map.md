# Refactor Naming Map

## Purpose

This document defines the stable domain vocabulary for the active question
pipeline.

The versioned question-generation packages have been removed. The remaining
historical package name in this area is `question_ledger_v6`, which is a
compatibility name rather than the intended architectural vocabulary.

The stable package surface introduced for refactoring is:

- [questions/candidates](/code/src/course_pipeline/questions/candidates)
- [questions/policy](/code/src/course_pipeline/questions/policy)
- [questions/ledger](/code/src/course_pipeline/questions/ledger)
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
- implementation package today: [questions/candidates](/code/src/course_pipeline/questions/candidates)

### Question Candidate Generation, Filtering, Scoring, Dedupe, Selection

- stable term: `candidate generation`
- implementation package today: [questions/candidates](/code/src/course_pipeline/questions/candidates)

### Visibility, Serveability, Canonicalization, Retention

- stable term: `policy classification`
- implementation package today: [questions/policy](/code/src/course_pipeline/questions/policy)

### Foundational Anchor Detection And Entry Coverage

- stable term: `coverage enforcement`
- implementation package today: [questions/policy](/code/src/course_pipeline/questions/policy)

### Ledger Assembly And Derived Views

- stable term: `question ledger`
- implementation package today: [questions/ledger](/code/src/course_pipeline/questions/ledger)
- compatibility package: [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)

### Bundle And Report Rendering

- stable term: `inspection publishing`
- implementation packages today:
  - [questions/candidates](/code/src/course_pipeline/questions/candidates)
  - [questions/policy](/code/src/course_pipeline/questions/policy)
  - [questions/ledger](/code/src/course_pipeline/questions/ledger)
  - [question_ledger_v6](/code/src/course_pipeline/question_ledger_v6)
- stable wrapper: [questions/inspection.py](/code/src/course_pipeline/questions/inspection.py)

## Current Migration Rule

Current rule:

- orchestration code should import through `course_pipeline.questions.*`
- docs should describe the stable domain names first
- `question_ledger_v6` should be treated as compatibility residue, not as the
  preferred implementation path

## End-State Goal

The eventual end state is:

- stable domain package names in both architecture and implementation
- no runtime dependence on version-labeled package imports
- version labels retained only in bounded historical notes, if at all
