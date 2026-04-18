You are updating an existing Python pipeline that generates learner-question artifacts from scraped course metadata.

Your task is to implement a refactor of the pipeline so that:
1. LLMs are used earlier for semantic extraction
2. deterministic code remains responsible for normalization, policy enforcement, ledgering, and bundle validation
3. question generation and answer generation remain separate pipelines
4. inspection bundles are built automatically and fail on scope/count inconsistencies

This is an additive refactor, not a full rewrite.

==================================================
HIGH-LEVEL ARCHITECTURE TO IMPLEMENT
==================================================

Current problems to solve:
- semantic extraction is too heuristic and lets junk anchors through
- richer learner questions are still awkward or underproduced
- answer generation is not cleanly integrated and should stay separate
- inspection bundles can drift out of scope or mismatch their manifests

New target architecture:

raw YAML
-> deterministic normalization
-> LLM semantic extraction
-> deterministic semantic sanitation / canonicalization
-> seed question generation
-> LLM candidate repair
-> LLM grounded expansion
-> deterministic filtering / scoring / policy
-> foundational coverage audit
-> V6 ledger
-> derived views
-> automatic bundle builder + validator

separately:

validated questions
-> LLM answer generation
-> answer-fit / grounding validation
-> answer/cache artifacts

Important constraints:
- Do NOT remove the ledger-first architecture
- Do NOT merge question generation and answer generation into one stage
- Do NOT replace deterministic normalization
- Do NOT silently drop artifacts or bundle inconsistencies
- Do NOT allow unsupported concepts to be introduced by LLM stages

==================================================
PART 1: KEEP THESE DETERMINISTIC
==================================================

Preserve or strengthen these deterministic components:
- YAML parsing
- course_id recovery
- chapter normalization / recovery
- run metadata / manifests
- filtering / scoring / policy enforcement
- foundational coverage audit
- V6 ledger normalization
- derived view generation
- inspection bundle validation

These should remain reproducible and inspectable.

==================================================
PART 2: ADD EARLY LLM SEMANTIC EXTRACTION
==================================================

Build a new semantic stage immediately after normalization.

New flow:
normalized course
-> LLM semantic extraction
-> deterministic semantic sanitation / canonicalization

New module suggestions:
- src/course_pipeline/semantic_extract_llm.py
- src/course_pipeline/semantic_validate.py
- src/course_pipeline/semantic_schemas.py
- src/course_pipeline/semantic_render.py

LLM semantic extraction should produce structured records, not free text.

Suggested schemas:

TopicRecord
- course_id
- topic_id
- label
- aliases
- topic_type
- description
- source_fields
- evidence_spans
- confidence

AnchorCandidate
- course_id
- anchor_id
- label
- normalized_label
- anchor_type
- foundational_candidate: bool
- learner_facing: bool
- requires_entry_question: bool
- rationale
- evidence_spans
- confidence

AliasGroupRecord
- course_id
- canonical_label
- aliases
- rationale
- confidence

FrictionRecord
- course_id
- anchor_id
- friction_type
- description
- rationale
- evidence_spans
- confidence

Hard requirements:
- every semantic record must cite supporting source field(s)
- every semantic record must include confidence
- LLM output must be validated before downstream use
- semantically junk anchors must be flagged or removed before question generation

Junk anchors to catch:
- domains / URLs
- raw site names
- placeholder headings
- weak inferred labels like "overview-segment-1"
- generic headings with no pedagogical meaning

Implement deterministic sanitation rules after LLM extraction:
- normalize whitespace, punctuation, case
- reject obvious URL/domain artifacts
- reject placeholder-like labels
- merge near-duplicate aliases conservatively
- preserve evidence and provenance for every keep/drop decision

Artifacts to emit:
- semantic_topics.jsonl
- semantic_anchors.jsonl
- semantic_alias_groups.jsonl
- semantic_frictions.jsonl
- semantic_validation_report.json
- semantic_yaml/<course_id>.yaml

CLI additions:
- run-semantic-extract-llm
- inspect-semantic-run

==================================================
PART 3: UPDATE QUESTION GENERATION
==================================================

Question generation should now use the sanitized semantic layer.

New flow:
sanitized semantic layer
-> seed question generation
-> LLM candidate repair
-> LLM grounded expansion
-> deterministic filter / score / policy
-> coverage audit
-> ledger

Keep seed generation template-driven and bounded.
Do NOT let the LLM freely generate the whole question set from scratch.

New module suggestions:
- src/course_pipeline/question_seed_generate.py
- src/course_pipeline/question_repair_llm.py
- src/course_pipeline/question_expand_llm.py
- src/course_pipeline/question_merge.py
- src/course_pipeline/question_refine_schemas.py

Stage A: seed question generation
Use semantic anchors and frictions to generate bounded candidate families:
- entry
- bridge
- procedural
- friction
- diagnostic
- transfer

Preserve current required-entry logic:
- foundational anchors must still get canonical plain beginner definitions
- acronym companion questions may exist, but cannot replace plain definitions

Stage B: LLM candidate repair
Input:
- normalized course
- sanitized semantic records
- raw seed candidates

Task:
- keep good questions unchanged
- rewrite awkward questions
- drop irreparable ones with explicit reasons
- preserve source lineage

Hard rules:
- no unsupported content
- no dropping required entry questions
- no replacing plain canonical definitions with richer variants
- every source candidate must end as keep | rewrite | drop

Output schema:
CandidateRepairRecord
- course_id
- source_question_id
- action
- original_question
- repaired_question
- repair_reason
- grounding_rationale
- confidence
- derived_by_llm = false

Stage C: LLM grounded expansion
Input:
- normalized course
- sanitized semantic records
- repaired candidates

Task:
- add a small number of grounded missing learner questions
- prioritize gaps in procedural, diagnostic, transfer, misconception, comparison
- avoid duplicates
- keep bounded

Hard rules:
- no unsupported concepts
- no weak paraphrase spam
- no replacing required-entry questions
- every added question must include rationale and evidence basis

Output schema:
DerivedCandidateRecord
- course_id
- question_text
- question_family
- question_type
- mastery_band
- anchor_label
- derivation_reason
- grounding_rationale
- confidence
- derived_by_llm = true

Stage D: merge and provenance
Merge:
- seed candidates
- repaired candidates
- derived candidates

Preserve fields:
- source_kind = seed | repaired | derived
- source_question_id
- llm_stage
- provenance_note

Then pass merged candidates into existing deterministic filter / score / policy stages.

Add optional score fields:
- semantic_confidence
- llm_repair_confidence
- llm_derivation_confidence

Artifacts to emit:
- seed_candidates.jsonl
- candidate_repairs.jsonl
- candidate_expansions.jsonl
- candidate_merge_report.jsonl
- question_refine_yaml/<course_id>.yaml

CLI additions:
- run-question-seed-gen
- run-question-repair-llm
- run-question-expand-llm
- inspect-question-refine-run

==================================================
PART 4: KEEP ANSWER GENERATION SEPARATE
==================================================

Do NOT mix answers into the question refinement stage.

Add or improve a separate answer pipeline:

validated questions
-> answer generation
-> answer-fit / grounding validation
-> answer artifacts

Only run answer generation for questions that pass policy, e.g.:
- curated_visible
- later, strong cache_servable candidates

New module suggestions:
- src/course_pipeline/answer_generate_llm.py
- src/course_pipeline/answer_validate_llm.py
- src/course_pipeline/answer_schemas.py

Suggested answer schema:
AnswerGenerationRecord
- question_id
- course_id
- answer_text
- answer_style
- grounding_rationale
- evidence_refs
- answer_fit_score
- groundedness_score
- validation_state

Hard rules:
- answer generation is downstream of validated questions
- answer text is not required in the V6 ledger
- answer artifacts should remain separate from the authoritative question ledger

Artifacts:
- generated_answers.jsonl
- answer_validation_logs.jsonl
- review_answers.jsonl
- answer_yaml/<course_id>.yaml

CLI additions:
- run-answer-generate-llm
- validate-answer-generation
- inspect-answer-run

==================================================
PART 5: AUTOMATIC INSPECTION BUNDLE BUILDER
==================================================

Implement an automatic bundle builder that creates a self-consistent bundle from a run id.

New module suggestions:
- src/course_pipeline/bundle_builder.py
- src/course_pipeline/bundle_validate.py
- src/course_pipeline/bundle_render.py
- src/course_pipeline/bundle_schemas.py

CLI:
- build-inspection-bundle --run-id <RUN_ID> [--course-id <ID> ...] [--strict] [--dry-run]

Bundle output structure:
inspection_bundle_<RUN_ID>/
  run_manifest.json
  validation_report.json
  inspection_report.md
  question_ledger_v6_report.md
  courses/
    <course_id>_<slug>.md
  final_deliverables/
    all_questions.jsonl
    visible_curated.jsonl
    cache_servable.jsonl
    aliases.jsonl
    anchors_summary.json

Validation rules:
1. Scope consistency
- manifest course_ids match rendered course pages
- no extra courses leak into bundle
- no extra courses appear in reports or deliverables for scoped bundles

2. Count consistency
- report totals match ledger JSONL
- per-course visible/hidden counts match filtered ledger rows
- cache counts match cache artifacts
- coverage summaries match source records

3. Run consistency
- copied artifacts belong to the requested run
- manifest run id matches requested run id

4. Suspicious anchor reporting
- surface junk anchors clearly
- fail in strict mode above threshold

5. Required file presence
- fail if required core bundle files are missing

Per-course markdown pages should include:
- visible curated Q/A pairs if available
- hidden but correct questions with reasons
- coverage warnings
- policy summary
- normalized/scraped course description

Top-level inspection report should include:
- run id
- pipeline variant
- declared course scope
- actual rendered course scope
- validation summary
- suspicious anchor summary
- coverage failure summary
- per-course quick stats

==================================================
PART 6: ORCHESTRATION
==================================================

Add an integrated end-to-end path such as:

run-pipeline-refactor --run-id <RUN_ID> [--course-id ...]

This should orchestrate:
1. deterministic normalization
2. semantic extraction
3. semantic validation/canonicalization
4. seed question generation
5. question repair
6. question expansion
7. existing deterministic filter/score/policy
8. ledger generation
9. optional answer generation
10. bundle build + validation

==================================================
PART 7: TESTS
==================================================

Add tests for:

Semantic extraction
- obvious junk anchors are flagged or removed
- near-duplicate anchors are merged conservatively
- evidence spans are preserved

Question refinement
- required-entry questions are never dropped
- repaired questions preserve anchor identity
- derived questions are bounded and grounded
- provenance is preserved across merge

Answer generation
- answers only generate for validated questions
- validation catches unsupported answers
- answers do not alter ledger integrity

Bundle builder
- scope drift causes failure
- count mismatches cause failure
- missing files cause failure
- suspicious anchor reporting works

Regression tests
- foundational plain definitions remain visible where required
- known bad cases like `unemployment` coverage failure are surfaced explicitly
- junk labels like `overview-segment-1` do not silently pass through to the final bundle

==================================================
PART 8: ACCEPTANCE CRITERIA
==================================================

1. Early semantic extraction is LLM-assisted and structured.
2. Junk anchors are caught before question generation.
3. Question generation quality improves without abandoning deterministic governance.
4. Answer generation remains separate and downstream.
5. The V6 ledger remains the authoritative question artifact.
6. Automatic inspection bundles are self-consistent and validated.
7. The pipeline is additive and test-covered.

==================================================
IMPLEMENTATION STYLE
==================================================

- Prefer small additive modules over sweeping rewrites
- Use typed schemas
- Preserve provenance everywhere
- Fail loudly on inconsistency
- Include docstrings / README notes for new CLI commands

Please implement:
- code
- schemas
- CLI wiring
- artifact outputs
- validation logic
- tests
- brief usage docs
