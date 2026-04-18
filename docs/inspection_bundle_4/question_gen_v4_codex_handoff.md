# Codex Handoff: Implement Question Generation V4 Policy Layer

## Goal

Implement V4 as a **policy and retention layer** on top of the existing V3 generation pipeline.

V3 remains responsible for:
- normalization
- structure extraction
- friction mining
- candidate generation
- filtering
- scoring
- deduplication

V4 adds:
- question-family tagging
- canonicalization and alias mapping
- separate curation vs serving decisions
- retention bucket assignment
- cache-serving eligibility
- policy telemetry

## Core design change

Move from a single terminal decision:

```text
selected vs rejected
```

To a multi-bucket decision:

```text
curated_core
cache_servable
alias_only
analysis_only
hard_reject
```

## Deliverables

Build the following modules.

### 1) `policy_models.py`
Implement Pydantic models or dataclasses for V4 policy artifacts.

Required classes:
- `PolicyScores`
- `FamilyTagSet`
- `CanonicalGroup`
- `PolicyDecision`
- `RetentionRecord`
- `CacheEntry`

### 2) `tag_families.py`
Responsibilities:
- assign one or more family tags to each candidate
- allowed tags: `entry`, `bridge`, `procedural`, `friction`, `diagnostic`, `transfer`
- support multi-tagging
- preserve rationale for each assigned tag

Input:
- deduplicated scored candidates
- topic and friction context

Output:
- candidates with family tags

### 3) `canonicalize.py`
Responsibilities:
- group semantically equivalent learner intents
- choose one canonical item per group when appropriate
- mark remaining items as alias or non-canonical duplicates
- emit canonical-group metadata

Required behavior:
- prefer clearer, more serviceable, more grounded canonical forms
- avoid independent canonical items when intent is effectively identical
- keep alias phrasing for retrieval and matching

### 4) `policy_score.py`
Responsibilities:
- compute policy-layer scores independently of V3 selection score
- support these dimensions:
  - correctness
  - groundedness
  - contradiction_risk
  - coherence
  - query_likelihood
  - pedagogical_value
  - answer_richness
  - mastery_fit
  - distinctiveness
  - serviceability
  - context_dependence
  - answer_stability

Notes:
- some of these may be estimated heuristically from existing V3 artifacts
- some may be derived from LLM judgments or templates
- keep implementation modular so scoring functions can be upgraded independently

### 5) `serveability_gate.py`
Responsibilities:
- decide whether a candidate is eligible for direct cache serving
- do not rely on correctness alone
- require serviceability, clarity, and answer stability
- return decision reason codes

Output:
- `servable: bool`
- structured reason codes

### 6) `assign_policy_bucket.py`
Responsibilities:
- assign exactly one of:
  - `curated_core`
  - `cache_servable`
  - `alias_only`
  - `analysis_only`
  - `hard_reject`
- implement staged decision logic
- preserve all reason codes and thresholds used

### 7) `build_cache_entries.py`
Responsibilities:
- create cache records from `curated_core` and `cache_servable`
- map aliases to canonical cache entries
- suppress direct serving from `analysis_only` and `hard_reject`

Required behavior:
- prefer canonical answers over duplicate copies
- support multiple question variants pointing to one canonical item

### 8) `retention.py`
Responsibilities:
- persist artifacts according to retention class
- full retention for:
  - `curated_core`
  - `cache_servable`
  - `alias_only`
  - `analysis_only`
- audit-only retention for:
  - `hard_reject`

### 9) `policy_metrics.py`
Responsibilities:
- compute policy-level telemetry
- output batch metrics and per-document diagnostics

Required metrics:
- entry share
- friction share
- canonical vs alias share
- duplicate-intent rate
- cache-servable rate
- analysis-only rate
- hard-reject rate
- family coverage
- mastery-band coverage

### 10) `run_v4_policy.py`
Responsibilities:
- orchestrate the V4 policy stage
- accept V3 artifacts as input
- emit final policy decisions, curated set, cache records, and metrics

Required entry point:
- `run_question_gen_v4_policy(v3_result)`

## Data models

### Policy scores
```python
class PolicyScores(BaseModel):
    correctness: float
    groundedness: float
    contradiction_risk: float
    coherence: float
    query_likelihood: float
    pedagogical_value: float
    answer_richness: float
    mastery_fit: float
    distinctiveness: float
    serviceability: float
    context_dependence: float
    answer_stability: float
```

### Family tags
```python
class FamilyTagSet(BaseModel):
    tags: list[str] = []
    rationale_by_tag: dict[str, str] = {}
```

### Canonical groups
```python
class CanonicalGroup(BaseModel):
    group_id: str
    canonical_candidate_id: str
    member_candidate_ids: list[str]
    alias_candidate_ids: list[str] = []
    rationale: str
```

### Policy decision
```python
class PolicyDecision(BaseModel):
    candidate_id: str
    canonical_id: str | None = None
    family_tags: list[str] = []
    policy_bucket: str
    servable: bool = False
    scores: PolicyScores
    reason_codes: list[str] = []
```

### Retention record
```python
class RetentionRecord(BaseModel):
    candidate_id: str
    policy_bucket: str
    store_full_record: bool
    store_answer_text: bool
    store_audit_only: bool
```

### Cache entry
```python
class CacheEntry(BaseModel):
    cache_id: str
    canonical_candidate_id: str
    canonical_question: str
    canonical_answer: str
    alias_questions: list[str] = []
    source_refs: list[str] = []
    active: bool = True
```
```

## Decision logic

Implement the policy as a staged pipeline.

### Stage 1: validity gate
If any of the following is true, assign `hard_reject`:
- correctness below threshold
- groundedness below threshold
- contradiction risk above threshold
- coherence below threshold
- malformed artifact

### Stage 2: family tagging
Assign one or more families.

### Stage 3: canonicalization
Determine whether the candidate is:
- canonical
- alias
- duplicate
- distinct canonical item

### Stage 4: serving decision
A candidate is `servable` only if:
- valid
- serviceability above threshold
- context dependence below threshold
- answer stability above threshold
- not superseded by a better canonical item

### Stage 5: curation decision
A candidate is eligible for `curated_core` only if:
- valid
- pedagogical_value above threshold
- distinctiveness above threshold
- answer_richness above threshold
- contributes to family / mastery balance

### Stage 6: final bucket assignment
Suggested priority order:
1. `hard_reject`
2. `alias_only`
3. `curated_core`
4. `cache_servable`
5. `analysis_only`

Notes:
- `alias_only` wins when the candidate is a useful phrasing variant but should not be independently curated or served
- `cache_servable` is not the same as `curated_core`
- `analysis_only` is the default quarantine bucket for non-fatal rejects

## Reason codes

Implement reason codes so downstream inspection is easy.

Examples:
- `invalid_unsupported`
- `invalid_low_groundedness`
- `invalid_contradiction_risk`
- `family_entry`
- `family_friction`
- `canonical_selected`
- `alias_of_canonical`
- `not_distinct_enough_for_curation`
- `servable_pass`
- `servable_fail_context_dependence`
- `servable_fail_instability`
- `curation_pass`
- `curation_fail_low_pedagogical_value`
- `curation_fail_balance_cap`
- `quarantined_analysis_only`

## Required config surface

Load from YAML or JSON.

Required groups:
- validity thresholds
- serving thresholds
- curation thresholds
- family-balance targets
- canonicalization thresholds
- retention policy
- metric toggles

Read defaults from `question_gen_v4_policy_config.yaml`.

## Acceptance criteria

### Policy correctness
- every candidate gets exactly one policy bucket
- every candidate receives reason codes
- invalid candidates always resolve to `hard_reject`
- aliases never become independent canonical items without justification

### Cache policy
- only `curated_core` and `cache_servable` can produce active cache entries
- `alias_only` routes to canonical items
- `analysis_only` never produces active cache entries

### Observability
- batch metrics must be emitted for every run
- per-document family coverage must be visible
- bucket distributions must be inspectable

### Retention
- `hard_reject` stores audit metadata only
- all other buckets store full records unless disabled by config

## Suggested rollout plan

### Phase 1
- implement policy models
- implement family tagging
- implement bucket assignment with heuristic scoring
- emit metrics

### Phase 2
- implement canonicalization and alias mapping
- build cache entries from canonical items
- add config-driven thresholds

### Phase 3
- refine serviceability and query-likelihood scoring
- add reviewer calibration loops
- optimize canonical selection quality

## Expected outputs

The V4 policy stage should emit:
- `curated_questions.json`
- `cache_entries.json`
- `policy_decisions.json`
- `canonical_groups.json`
- `policy_metrics.json`
- `retention_manifest.json`
