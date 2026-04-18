# Question Generation V4 Backlog

This backlog implements the policy-layer requirements in:

- [question_gen_v4_bundle_readme.md](/code/docs/inspection_bundle_4/question_gen_v4_bundle_readme.md)
- [question_gen_v4_policy_vision.md](/code/docs/inspection_bundle_4/question_gen_v4_policy_vision.md)
- [question_gen_v4_policy_diagram.md](/code/docs/inspection_bundle_4/question_gen_v4_policy_diagram.md)
- [question_gen_v4_codex_handoff.md](/code/docs/inspection_bundle_4/question_gen_v4_codex_handoff.md)

## Assessment

The V4 direction makes sense.

V3 improved candidate quality and balance, but it still ends in a mostly
single-purpose terminal decision.

V4 fixes that by separating:

- curation
- direct serving
- alias mapping
- analysis retention
- hard rejection

That is a real improvement because a question can be:

- too duplicative for the curated set
- still safe and useful for cache serving
- or useful only as an alias

without being a bad candidate overall.

## Slice 1: Create a dedicated V4 package

- Add `src/course_pipeline/question_gen_v4/`
- Implement:
  - `policy_models.py`
  - `tag_families.py`
  - `canonicalize.py`
  - `policy_score.py`
  - `serveability_gate.py`
  - `assign_policy_bucket.py`
  - `build_cache_entries.py`
  - `retention.py`
  - `policy_metrics.py`
  - `run_v4_policy.py`

Acceptance criteria:
- V4 is isolated from V3 generation logic
- V4 operates on V3 artifacts, not raw course YAML directly

## Slice 2: Add V4 policy config

- Add `question_gen_v4_policy_config.yaml`
- Support:
  - validity thresholds
  - serving thresholds
  - curation thresholds
  - family balance targets
  - canonicalization thresholds
  - retention policy

Acceptance criteria:
- bucket behavior is tunable without code edits

## Slice 3: Add policy models

- Implement:
  - `PolicyScores`
  - `FamilyTagSet`
  - `CanonicalGroup`
  - `PolicyDecision`
  - `RetentionRecord`
  - `CacheEntry`

Acceptance criteria:
- every V4 artifact has a typed model

## Slice 4: Implement family tagging

- Tag candidates with one or more of:
  - `entry`
  - `bridge`
  - `procedural`
  - `friction`
  - `diagnostic`
  - `transfer`
- Preserve rationale for each tag

Acceptance criteria:
- family coverage is inspectable per course

## Slice 5: Implement canonicalization and alias mapping

- Group semantically equivalent intents
- Select one canonical candidate where appropriate
- Mark remaining members as:
  - alias
  - duplicate non-canonical

Acceptance criteria:
- aliases route to canonical items rather than becoming independent surface items
- duplicate intent is visible in persisted metadata

## Slice 6: Implement policy scoring

- Score dimensions:
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

Acceptance criteria:
- every candidate receives policy scores separate from V3 scores
- score dimensions are persisted

## Slice 7: Implement validity gate and serveability gate

- Validity gate:
  - invalid -> `hard_reject`
- Serveability gate:
  - decide whether direct cache serving is allowed
  - require more than correctness alone

Acceptance criteria:
- invalid candidates never survive into active buckets
- serveability decisions include reason codes

## Slice 8: Implement final bucket assignment

- Assign exactly one of:
  - `curated_core`
  - `cache_servable`
  - `alias_only`
  - `analysis_only`
  - `hard_reject`
- Preserve all reason codes

Acceptance criteria:
- every candidate gets exactly one bucket
- alias candidates do not appear as independent curated items

## Slice 9: Implement cache-entry building

- Build canonical cache entries from:
  - `curated_core`
  - `cache_servable`
- attach aliases to canonical items
- never serve `analysis_only` or `hard_reject`

Acceptance criteria:
- active cache entries are emitted
- alias mappings are explicit

## Slice 10: Implement policy metrics and retention

- Emit:
  - bucket distribution
  - family coverage
  - canonical vs alias share
  - cache-servable rate
  - analysis-only rate
  - hard-reject rate
- emit retention records

Acceptance criteria:
- every run produces policy metrics
- retention intent is inspectable

## Slice 11: Wire V4 into pipeline and CLI

- Add a CLI command that runs V4 from an existing V3 run directory
- Persist per-course V4 artifacts and run-level summaries

Acceptance criteria:
- bounded V4 run can be executed from CLI
- artifacts are stored under a run directory

## Slice 12: Add V4 review bundle

- Build review docs from `curated_core`
- include:
  - selected curated questions and answers
  - bucket summaries
  - aliases and cache summary where helpful

Acceptance criteria:
- inspection output is easy to compare to V3

## Slice 13: Run V4 on the latest bounded V3 time-series run

- use the latest successful bounded V3 run for:
  - `24491`
  - `24593`
  - `24594`
- generate:
  - V4 policy artifacts
  - V4 review docs
  - inspection bundle
  - implementation report

Acceptance criteria:
- `docs/inspection_bundle_5` exists
- bucket distributions and curated/core distinctions are visible

## Refinement Slice A: Penalize generic scaffolded wording

- Add explicit penalties for questions whose wording is mostly a reusable scaffold with weak topic-specific substance
- Examples:
  - `Why does X matter in this course?`
  - `How would I apply X to the kind of data used here?`
  - `What would make X fail in a realistic case?`
- Reduce `serviceability`, `pedagogical_value`, and `answer_stability` for these forms unless there is strong friction support

Acceptance criteria:
- generic course-context questions stop dominating `curated_core`
- thin questions can still survive as `analysis_only` when useful for tuning

## Refinement Slice B: Make curation family-aware, not score-only

- Enforce stronger balance for:
  - `entry`
  - `friction`
  - `diagnostic`
  - `transfer`
- Prefer a smaller curated set with broader family coverage over a larger set of similarly templated questions

Acceptance criteria:
- `curated_core` is not dominated by one family
- at least one non-entry family is represented whenever the course supports it

## Refinement Slice C: Tighten cache-serving eligibility

- Require stronger evidence for a question to become `cache_servable`
- Quarantine questions with:
  - heavy course-context dependence
  - low answer stability
  - generic stem wording
  - weak groundedness despite passing validity

Acceptance criteria:
- `cache_servable` is materially smaller and safer than the raw valid set
- clearly thin prompts move to `analysis_only`

## Refinement Slice D: Improve canonicalization diagnostics

- Keep current canonicalization rules, but add clearer diagnostics for:
  - grouped aliases
  - non-grouped near-duplicates
  - reasons a candidate remained canonical
- Do not force aliasing across distinct topical content just because the template stem is similar

Acceptance criteria:
- canonicalization behavior is inspectable in reports
- review docs make it obvious whether low alias counts are expected or a weakness

## Refinement Slice E: Publish V4 implementation report and inspection bundle

- Add:
  - `docs/question_gen_v4_implementation_report.md`
  - `docs/inspection_bundle_5/README.md`
  - representative course review docs
  - copied V4 run report

Acceptance criteria:
- the new inspection bundle is self-contained
- the report explains what changed from the initial V4 pass

## Execution Order

1. Slice 1
2. Slice 2
3. Slice 3
4. Slice 4
5. Slice 5
6. Slice 6
7. Slice 7
8. Slice 8
9. Slice 9
10. Slice 10
11. Slice 11
12. Slice 12
13. Slice 13
