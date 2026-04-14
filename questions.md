# Questions

## Defaults

### 1. Where does the pipeline stop?
Default answer: after deterministic standardization of courses and chapters.

### 2. Should the pipeline use any LLM extraction?
Default answer: no.

### 3. Should the pipeline build graph tables?
Default answer: no.

### 4. Should the pipeline generate learner questions?
Default answer: no.

### 5. What should count as the canonical course identifier?
Default answer: use the trailing numeric id from `final_url` when available,
otherwise fall back to the YAML filename stem.

### 6. How should sparse courses be handled?
Default answer: always ingest them, recover pseudo-chapters deterministically
from `overview`, and record lower confidence rather than dropping the course.
