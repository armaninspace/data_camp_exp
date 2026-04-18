# Codex Handoff: Implement Question Generation V3

## Goal

Implement V3 as a modular pipeline that converts normalized instructional source text into a balanced, high-value set of learner questions.

The defining change from V2 is:
- V2: generation-first
- V3: structure-first, friction-first, ranker-driven

## Deliverables

Build the following modules.

### 1) `normalize.py`
Responsibilities:
- accept raw course-like documents
- normalize metadata fields
- recover explicit sections
- infer pseudo-sections when necessary
- emit `CanonicalDocument`

Required output type:
- `CanonicalDocument`
- `Section`

### 2) `extract_topics.py`
Responsibilities:
- run section-level topic extraction
- emit fine-grained `TopicNode` records
- support topic types described in the spec
- preserve source provenance

Required output type:
- `list[TopicNode]`

### 3) `extract_edges.py`
Responsibilities:
- infer local topic graph relations
- emit `TopicEdge` records
- support at least: `prerequisite_of`, `contrasts_with`, `confused_with`, `evaluated_by`, `uses`, `decision_depends_on`

Required output type:
- `list[TopicEdge]`

### 4) `extract_pedagogy.py`
Responsibilities:
- infer pedagogical signals per topic
- emit `PedagogicalProfile`
- include misconceptions, sticking points, evidence of mastery

Required output type:
- `list[PedagogicalProfile]`

### 5) `mine_friction.py`
Responsibilities:
- derive `FrictionPoint` objects from topics, edges, and pedagogy
- do not require explicit source wording like "common mistake"
- infer friction from contrast, tradeoff, method choice, failure, prerequisite gap, and transfer

Required output type:
- `list[FrictionPoint]`

### 6) `generate_candidates.py`
Responsibilities:
- generate candidates by fixed slot
- slots: novice orientation, novice definition, developing procedural, developing comparison, developing misconception, proficient diagnostic, proficient transfer
- overgenerate intentionally

Required output type:
- `list[QuestionCandidate]`

### 7) `filters.py`
Responsibilities:
- implement low-answerability rejection
- implement low-instructional-value rejection
- implement malformed or unsupported rejection
- return structured rejection reasons

Required output type:
- kept candidates
- rejected candidates with reasons

### 8) `score_candidates.py`
Responsibilities:
- compute candidate scores using configurable weights
- expose dimension-level scores and total score
- support easy tuning from config

Required output type:
- `list[ScoredCandidate]`

### 9) `dedupe.py`
Responsibilities:
- semantic deduplication by intent
- keep strongest representative candidate
- record duplicate clusters

Required output type:
- deduplicated candidates
- duplicate cluster metadata

### 10) `select_final.py`
Responsibilities:
- constrained selection using configurable quotas
- enforce groundedness threshold
- enforce type and mastery balance
- return final selected set and selection diagnostics

Required output type:
- final selected questions
- selection summary

### 11) `pipeline.py`
Responsibilities:
- orchestrate all stages
- persist intermediate artifacts for inspection
- log metrics and rejection counts
- provide a single `run_question_gen_v3(document)` entry point

---

## Data models

Implement these models as Pydantic classes or dataclasses.

### CanonicalDocument
```python
class Section(BaseModel):
    section_index: int
    title: str
    summary: str
    source: Literal["explicit", "inferred"]

class CanonicalDocument(BaseModel):
    doc_id: str
    title: str
    summary: str = ""
    overview: str = ""
    level: str | None = None
    tooling: list[str] = []
    subjects: list[str] = []
    sections: list[Section]
```

### Topic graph artifacts
```python
class TopicNode(BaseModel):
    topic_id: str
    label: str
    aliases: list[str] = []
    topic_type: str
    description: str
    source_section_ids: list[int] = []
    confidence: float

class TopicEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str
    rationale: str
    confidence: float
```

### Pedagogy and friction
```python
class PedagogicalProfile(BaseModel):
    topic_id: str
    cognitive_modes: list[str] = []
    abstraction_level: str
    notation_load: str
    procedure_load: str
    likely_misconceptions: list[str] = []
    likely_sticking_points: list[str] = []
    evidence_of_mastery: list[str] = []

class FrictionPoint(BaseModel):
    friction_id: str
    topic_id: str
    friction_type: str
    prompting_signal: str
    learner_symptom: str
    why_it_matters: str
    severity: float
    confidence: float
```

### Question artifacts
```python
class QuestionCandidate(BaseModel):
    candidate_id: str
    topic_id: str
    slot: str
    mastery_band: Literal["novice", "developing", "proficient"]
    question_type: str
    question_text: str
    rationale: str
    source_support: list[str] = []

class CandidateScore(BaseModel):
    friction_value: float
    specificity: float
    answer_richness: float
    mastery_fit: float
    novelty: float
    groundedness: float
    total: float

class ScoredCandidate(BaseModel):
    candidate: QuestionCandidate
    score: CandidateScore
    rejection_flags: list[str] = []
```

---

## Required config surface

Load from YAML or JSON.

Required config groups:
- confidence thresholds
- score weights
- taxonomy quotas
- semantic dedupe thresholds
- per-slot generation counts

Read these defaults from `question_gen_v3_config.yaml`.

---

## Functional requirements

### Topic extraction
- must extract more granular learning units than broad section headings
- must support explicit and inferred topics
- must attach provenance

### Friction mining
- must infer friction without depending on exact phrases like "common mistake"
- must create friction points from contrast, tradeoff, choice, prerequisite gap, and failure modes

### Candidate generation
- must generate by slot rather than freeform only
- must be able to overgenerate at least 2x the final desired output count

### Filtering
- must reject thin-answer questions
- must reject broad heading paraphrases
- must reject unsupported candidates
- must log human-readable rejection reasons

### Scoring
- must compute dimension-level scores and total
- must allow weight tuning without code changes

### Selection
- must enforce quota policy
- must return diagnostics if quotas cannot be satisfied
- must keep provenance for every selected question

---

## Suggested APIs

```python
def normalize_document(raw_doc: dict) -> CanonicalDocument: ...

def extract_topics(doc: CanonicalDocument) -> list[TopicNode]: ...

def extract_edges(doc: CanonicalDocument, topics: list[TopicNode]) -> list[TopicEdge]: ...

def extract_pedagogy(doc: CanonicalDocument, topics: list[TopicNode], edges: list[TopicEdge]) -> list[PedagogicalProfile]: ...

def mine_friction(topics: list[TopicNode], edges: list[TopicEdge], pedagogy: list[PedagogicalProfile]) -> list[FrictionPoint]: ...

def generate_candidates(doc: CanonicalDocument, topics: list[TopicNode], edges: list[TopicEdge], pedagogy: list[PedagogicalProfile], frictions: list[FrictionPoint], config: dict) -> list[QuestionCandidate]: ...

def filter_candidates(candidates: list[QuestionCandidate], doc: CanonicalDocument, topics: list[TopicNode], config: dict) -> tuple[list[QuestionCandidate], list[dict]]: ...

def score_candidates(candidates: list[QuestionCandidate], topics: list[TopicNode], edges: list[TopicEdge], frictions: list[FrictionPoint], config: dict) -> list[ScoredCandidate]: ...

def dedupe_candidates(scored: list[ScoredCandidate], config: dict) -> tuple[list[ScoredCandidate], list[dict]]: ...

def select_final(scored: list[ScoredCandidate], config: dict, target_n: int) -> tuple[list[ScoredCandidate], dict]: ...

def run_question_gen_v3(raw_doc: dict, config: dict) -> dict: ...
```

---

## Implementation guidance

### Use structured outputs
If LLM-backed extraction is used:
- use strict schema validation
- retry malformed outputs
- store raw completion text for debugging

### Preserve provenance
Every topic, friction point, and candidate should be traceable back to:
- source document id
- section index
- supporting text span or source note

### Keep intermediate files
Persist stage artifacts for debugging:
- normalized document
- topics
- edges
- pedagogy
- friction points
- raw candidates
- rejected candidates with reasons
- scored candidates
- final selection

### Make rejection visible
Rejection visibility is mandatory. Silent filtering will make tuning too hard.

---

## Acceptance criteria

### AC1: Structure extraction
Given a valid normalized input document,
- pipeline emits at least one section
- pipeline emits at least one topic per substantive section
- topic records include provenance and confidence

### AC2: Friction mining
Given source content with multiple methods, contrasts, or diagnostics,
- friction miner emits at least one friction point tied to those signals
- friction records are not empty when content clearly contains choice or failure structure

### AC3: Candidate quality gate
Given a candidate whose answer would be mostly tautological or "not specified",
- filters reject it
- rejection reason is recorded

### AC4: Scoring transparency
Given a surviving candidate,
- system returns dimension-level scores and total score
- score weights are loaded from config, not hardcoded

### AC5: Balanced final set
Given a large enough candidate pool,
- final selection respects configured caps and minimum shares
- if quotas cannot be met, diagnostics explain which quota failed

### AC6: Dedupe
Given multiple rephrasings of the same learner question,
- dedupe keeps one representative
- duplicate cluster metadata is returned

### AC7: End-to-end output
`run_question_gen_v3()` returns a payload containing:
- normalized document
- intermediate counts
- rejection summaries
- final selected questions
- final distribution by type and mastery band

---

## Minimal test plan

Implement unit tests for:
- section inference
- topic type normalization
- friction inference heuristics
- thin-answer filter
- semantic dedupe
- quota-aware selection
- score computation from config

Implement one end-to-end fixture test that verifies:
- pipeline completes without error
- final set includes non-definition questions
- proficient share is non-zero when suitable inputs contain diagnostics or transfer opportunities

---

## Output contract

Suggested top-level pipeline return shape:

```python
{
  "doc_id": str,
  "counts": {
    "sections": int,
    "topics": int,
    "edges": int,
    "friction_points": int,
    "raw_candidates": int,
    "filtered_out": int,
    "deduped_out": int,
    "selected": int,
  },
  "distributions": {
    "question_types": dict[str, int],
    "mastery_bands": dict[str, int],
  },
  "artifacts": {
    "topics": list[TopicNode],
    "edges": list[TopicEdge],
    "pedagogy": list[PedagogicalProfile],
    "friction_points": list[FrictionPoint],
    "rejections": list[dict],
    "selected_questions": list[ScoredCandidate],
  }
}
```

---

## Priorities

If implementation time is tight, do these first:
1. friction mining
2. low-value filtering
3. score-based ranking
4. quota-aware selection
5. better provenance and diagnostics

This ordering gives the biggest quality lift fastest.
