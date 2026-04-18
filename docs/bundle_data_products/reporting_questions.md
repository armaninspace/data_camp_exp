# Reporting Questions

Use this as a checklist for a quantitative reviewer working from the bundled
data products.

## High-Level

1. How many courses are represented in each bundled run?
2. How many records exist in each artifact table?
3. Which artifact classes are current versus legacy?

## Learning Outcomes

1. What is the mean, median, and range of learning outcomes per course?
2. What is the mean number of citations per learning outcome?
3. What percentage of outcomes rely on chapter citations versus only summary or
   overview citations?
4. What are the frequencies of:
   - `knowledge_type`
   - `process_level`
   - `dok_level`
   - `solo_level`
5. How many outcomes appear duplicative within a course?

## Question Cache

1. How many question groups are generated per claim?
2. What fraction of groups are rejected?
3. What fraction of answers pass `answer_fit`?
4. What fraction of answers pass `grounding`?
5. What fraction of claims end with at least one runtime-eligible pair?
6. What are the most common failure reasons in validation logs?

## Legacy Semantic Layer

1. How many topics and edges are produced per course?
2. How many predicted questions are produced per topic or per course?
3. How repetitive are old predicted questions?
4. How often do old predicted questions appear unsupported by source evidence?

## Full-Corpus Completion

1. What is the final success count?
2. What is the error count?
3. Are there identifiable error clusters by course type or source quality?
4. Do malformed or low-information courses still produce outputs that look
   falsely confident?
