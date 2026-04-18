# Questions

## Defaults

### 1. Does the traceable question-cache idea make sense?
Default answer: yes, but only as a layer on top of learning outcomes, not on
top of the removed topic/edge/question stack described in the tasking note.

### 2. What should be the source substrate for the cache layer?
Default answer: normalized courses plus cited learning outcomes.

### 3. Should the next push depend on topic graphs, pedagogical profiles, or predicted questions?
Default answer: no. Those are not part of the current repo state and should not
be reintroduced implicitly.

### 4. What should be the first cache milestone?
Default answer: bounded claim-to-question-group generation with strict lineage
and human-inspectable outputs.

### 5. Should strict equivalence be treated as a hard rule?
Default answer: yes. If ideal answer content changes, it is a different
question group.

### 6. What should define question-group identity?
Default answer: course, claim, learner intent, and pedagogical move.

### 7. What should define variation identity?
Default answer: normalized paraphrase text within a single question group.

### 8. Should “what”, “how”, and “why” questions be grouped together by default?
Default answer: no. Group them together only if the ideal answer content is
actually the same.

### 9. How should IDs be generated?
Default answer: deterministically from `course_id`, `claim_id`, intent slug,
normalized variation text, and answer version.

### 10. Should citations be inherited from claims or regenerated from scratch?
Default answer: inherit claim citations by default and only add new citations if
they remain YAML-traceable.

### 11. Should canonical answers be short or expansive in the MVP?
Default answer: short, direct, and trust-building.

### 12. Should the first runtime matcher use embeddings?
Default answer: no. Start with deterministic normalization and lexical matching
first.

### 13. When should semantic matching be added?
Default answer: only after the lexical baseline and group boundaries are shown
to be reliable.

### 14. What should count as a cache hit?
Default answer: a high-confidence match with sufficient margin over competing
candidates and no obvious follow-up or repair intent.

### 15. What should bypass the cache immediately?
Default answer: follow-ups, repair requests, execution errors, ambiguous
questions, and requests for a different explanation style.

### 16. What should the first fallback implementation do?
Default answer: log the miss reason and nearest lineage, then use a simple LLM
fallback path without trying to be an adaptive tutor.

### 17. Should fallback traffic be used for cache warming?
Default answer: yes, but only as candidate data for review, not automatic
promotion.

### 18. What is the primary failure mode to optimize against?
Default answer: false grouping. Returning the wrong cached answer is worse than
falling back.

### 19. What should be the first evaluation fixture?
Default answer: `7630`, because its learning outcomes split cleanly into obvious
beginner intents such as vectors, matrices, factors, data frames, and lists.

### 20. What should count as success for the next push?
Default answer: bounded generation of traceable question groups, strict
variation boundaries, inspectable YAML artifacts, deterministic matcher hits,
and clean miss logging.
