# Intermediate Response Notes

## Purpose

This note captures two things:

1. a sample of current precomputed question/answer pairs
2. an assessment of whether an ELIZA-like bot should be used to stall while a
   slower LLM answer is being prepared

## Sample Precomputed Question/Answer Pairs

The current runtime-eligible examples come from `Introduction to R (7630)` in
the bounded question-cache run `20260414T044551Z`.

### Pair 1

Question:
`How do you use basic r syntax for calculations?`

Answer:
`You use basic R syntax for calculations by entering expressions in the console and assign variables using the assignment operator.`

### Pair 2

Question:
`How do you name vectors in R?`

Answer:
`You can name vectors in R by assigning names to their elements using the names() function.`

### Pair 3

Question:
`How do you compare vectors in R?`

Answer:
`You can compare vectors in R using comparison operators to evaluate relationships between their elements.`

### Pair 4

Question:
`How do you name lists in R?`

Answer:
`You can name lists in R by assigning names to their elements.`

### Pair 5

Question:
`How do you apply r skills to analyze simple real-world datasets?`

Answer:
`You apply R skills to analyze simple real-world datasets by practicing with real data sets, such as analyzing gambling results using vectors or examining box office numbers of movies.`

## Assessment Of An ELIZA-Like Bot

If the goal is to deceptively stall the user, that is a bad idea.

Reasons:

1. it creates trust debt
2. it conflicts with the app's explicit `cache_hit` and `cache_miss` framing
3. it risks giving low-value filler that feels evasive
4. it can accidentally contradict the final grounded answer

So the recommendation is:

Do not build a deceptive ELIZA bot.

Build a transparent intermediate response layer instead.

## Recommended Model

The intermediate layer should act as a latency bridge, not as a fake answerer.

### What it should do

1. acknowledge the question quickly
2. state that the request was a `cache miss`
3. briefly reflect the question type
4. explain that course context is being checked
5. hand off to the final LLM answer when ready

### What it should not do

1. pretend it already knows the answer
2. invent instructional content
3. provide partial technical guidance that may be wrong
4. mimic competence it does not have

## Example Intermediate Responses

### Procedural question

User:
`How do I create a vector in R?`

Intermediate response:
`Cache miss. This looks like a procedural question about an R operation. I’m checking the course context for the most relevant grounded answer.`

### Debugging question

User:
`Why does x(2) fail on my vector?`

Intermediate response:
`Cache miss. This looks like a debugging question about vector indexing in R. I’m preparing a grounded answer from the course context.`

### Definition question

User:
`What is a factor in R?`

Intermediate response:
`Cache miss. This looks like a concept question about categorical data in R. I’m checking the course material for the best grounded explanation.`

## Suggested Runtime Policy

1. If `cache_hit`, return the final cached answer immediately.
2. If `cache_miss` and expected latency is short, return only the final answer.
3. If `cache_miss` and expected latency is noticeable, show an intermediate
   bridge message first.
4. Replace or append with the final LLM answer once it is ready.

## Suggested Implementation Shape

The bridge can be deterministic.

Inputs:

1. `course_id`
2. incoming question text
3. cache result
4. coarse question type heuristic

Outputs:

1. `cache_miss` notice
2. one short reflective sentence
3. one short progress sentence

## Question Type Heuristics

Simple heuristics are sufficient for the bridge:

1. starts with `how do`, `how can`, `show me how`:
   procedural
2. starts with `why does`, `why is`, includes `error`, `fail`, `not working`:
   debugging
3. starts with `what is`, `what are`, `define`, `explain`:
   concept
4. starts with `when should`, `which one`, `compare`:
   comparison

## Product Recommendation

The best version of this feature is:

1. honest
2. short
3. deterministic
4. visually distinct from the final answer

In other words:

Use an intermediate response layer for latency smoothing, not an ELIZA bot for
deception.
