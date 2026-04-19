You are updating an existing course-question pipeline.

Goal:
Add an LLM-assisted post-generation refinement stage that:
1. repairs awkward or weak candidate questions
2. derives a small number of additional grounded learner questions
3. keeps answer generation separate from question generation
4. preserves the current ledger-first architecture and inspection model

Important architectural constraints:
- Do NOT replace the existing heuristic/topic/friction/candidate generation path.
- Do NOT merge question generation and answer generation into one prompt.
- Do NOT make the V6 ledger answer-first.
- Keep the V6 ledger as the authoritative question artifact.
- Preserve protected foundational beginner-definition questions.
- Preserve non-destructive inspection: every original candidate must remain traceable.
- New LLM stages must be bounded, inspectable, and artifact-producing.

What exists now:
- Current question path is:
  normalized course
  -> V3 candidate generation
  -> V4 / V4.1 policy classification
  -> V6 ledger
- Current pain points:
  - some procedural / transfer questions are awkward
  - alias clustering is sparse
  - cache-servable output is underproduced
- Separate answer-capable path exists via question-cache / canonical answers, but it is not the primary authoritative path.

What to build:

A. Insert two new stages into the question pipeline:
   raw course YAML
   -> normalized course
   -> topic extraction
   -> edge extraction
   -> pedagogy extraction
   -> friction mining
   -> candidate generation
   -> LLM candidate repair
   -> LLM grounded expansion
   -> candidate filtering
   -> candidate scoring
   -> dedupe
   -> policy classification
   -> foundational-entry coverage enforcement
   -> ledger normalization
   -> derived views

B. Keep answer generation separate:
   validated questions
   -> answer generation
   -> answer-fit / grounding validation
   -> question-cache style artifacts

New stages to implement:

1) LLM candidate repair
Input:
- normalized course
- extracted topics / edges / pedagogy / frictions
- raw candidate questions
- foundational anchors / required-entry questions

Task:
- keep good questions unchanged
- rewrite awkward / underspecified / unnatural questions
- drop irreparable questions with explicit reasons
- preserve source lineage

Hard rules:
- do not invent unsupported content
- do not remove required foundational entry questions
- do not replace canonical plain definitions with richer variants
- every original candidate must end in one explicit state:
  kept | rewritten | dropped

Suggested output schema:
CandidateRepairRecord:
- course_id
- source_question_id
- action: keep|rewrite|drop
- original_question
- repaired_question (nullable)
- repair_reason
- grounding_rationale
- confidence
- derived_by_llm = false

2) LLM grounded expansion
Input:
- normalized course
- extracted topics / edges / pedagogy / frictions
- repaired candidate set
- foundational anchors

Task:
- derive a small number of additional grounded learner questions
- prioritize missing high-value questions in:
  procedural
  diagnostic
  transfer
  misconception
  comparison
- avoid near-duplicates
- preserve boundedness

Hard rules:
- do not invent unsupported techniques, workflows, or datasets
- do not add weak paraphrases
- do not replace foundational entry questions
- mark all newly added questions as derived_by_llm = true

Suggested output schema:
DerivedCandidateRecord:
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

3) Merge + traceability stage
Merge:
- original candidates
- repaired candidates
- derived candidates

Requirements:
- preserve source lineage
- preserve original candidate ids where possible
- assign new ids for derived questions
- attach provenance fields:
  source_kind = original|repaired|derived
  source_question_id (nullable)
  llm_stage = repair|expand|null
  provenance_note

4) Keep filtering / scoring / policy / ledger downstream
Do not rewrite the whole policy layer.
Instead:
- feed merged candidates into existing filtering/scoring
- optionally add new score signals:
  llm_grounding_confidence
  llm_repair_confidence
  llm_derivation_confidence
- preserve current delivery classes and ledger model

Implementation guidance:

A. Multi-prompt design
Do NOT use one giant prompt.

Create at least:
- prompt_repair_candidates()
- prompt_expand_candidates()
- optional prompt_consolidate_aliases()
- optional prompt_validate_question_quality()

Prompt 1: repair
System goal:
You are a bounded question editor for learner-facing course questions.
Improve wording without inventing unsupported content.

Behavior:
- keep natural, grounded questions unchanged
- rewrite awkward or unnatural questions
- drop irreparable questions
- preserve beginner plain definitions for foundational anchors

Prompt 2: expand
System goal:
You are a bounded pedagogical question generator.
Add only grounded learner questions supported by the course.

Behavior:
- fill important coverage gaps
- prefer realistic learner questions
- favor procedural / diagnostic / transfer / misconception / comparison gaps
- avoid duplicates and unsupported creativity

B. New files / modules to add
Suggested module layout:
- src/course_pipeline/question_refine_llm.py
- src/course_pipeline/question_expand_llm.py
- src/course_pipeline/question_llm_schemas.py
- src/course_pipeline/question_llm_merge.py
- src/course_pipeline/inspect_question_refine.py

Suggested artifact outputs:
- candidate_repairs.jsonl
- candidate_expansions.jsonl
- candidate_merge_report.jsonl
- question_refine_yaml/<course_id>.yaml
- question_expand_yaml/<course_id>.yaml

C. CLI additions
Add commands like:
- run-question-refine-llm
- run-question-expand-llm
- inspect-question-refine-run
- inspect-question-expand-run

Also support an integrated path:
- run-question-gen-v3
- run-question-refine-llm
- run-question-expand-llm
- run-question-gen-v4-1-policy
- run-question-ledger-v6

D. Suggested orchestration
Pseudocode:

for each normalized course:
    topics = extract_topics(course)
    edges = extract_edges(course, topics)
    pedagogy = extract_pedagogy(course, topics, edges)
    frictions = mine_friction(topics, edges, pedagogy)

    raw_candidates = generate_candidates(course, topics, edges, pedagogy, frictions)

    repaired = llm_repair_candidates(
        course=course,
        topics=topics,
        edges=edges,
        pedagogy=pedagogy,
        frictions=frictions,
        candidates=raw_candidates,
    )

    expanded = llm_expand_candidates(
        course=course,
        topics=topics,
        edges=edges,
        pedagogy=pedagogy,
        frictions=frictions,
        candidates=repaired,
    )

    merged = merge_candidates(raw_candidates, repaired, expanded)

    kept, rejected = filter_candidates(merged)
    scored = score_candidates(kept)
    deduped = canonicalize(scored)
    policy = assign_policy(deduped)
    policy = promote_required_entries(policy)
    coverage = audit_coverage(policy)

    if strict_mode and coverage fails:
        fail run

    ledger = build_v6_ledger(policy, rejected)

E. Separate answer generation
Do NOT generate answers during repair/expansion.

Instead, implement a later stage:
validated_questions -> generate_answers -> validate_answer_fit -> export answer artifacts

Recommended gating:
- only answer-generate for validated questions
- probably only for curated_visible and strong cache_servable candidates
- keep answer artifacts outside the authoritative ledger row model

Suggested answer generation inputs:
- normalized course
- validated question
- source refs / grounding evidence
- anchor metadata
- family/type/mastery metadata

Suggested answer generation outputs:
AnswerGenerationRecord:
- question_id
- answer_text
- answer_style
- grounding_rationale
- evidence_refs
- answer_fit_score
- groundedness_score
- validation_state

Acceptance criteria:

1. No regression on foundational coverage
- required_entry questions remain present and protected
- no required_entry question is removed by the LLM stages

2. Full traceability
- every original candidate appears in repair outputs as keep/rewrite/drop
- every derived candidate is explicitly marked derived

3. Better candidate quality
- procedural and diagnostic questions become more natural
- fewer awkward transfer questions survive

4. Bounded expansion
- expansion adds a small, useful number of questions
- duplicate rate stays controlled

5. Ledger invariants preserved
- V6 ledger remains the source of truth
- hidden/rejected questions remain inspectable
- derived views remain reproducible from ledger + run artifacts

6. Answer generation stays separate
- no answer text is required in the ledger path
- answer generation is a later linked stage

Tests to add:

Unit tests
- required entry questions are never dropped in repair
- rewrite preserves anchor identity
- expansion does not emit unsupported topics
- merge preserves provenance
- derived candidates get stable ids

Regression tests
- ARIMA-style foundational question remains visible
- acronym companion does not replace plain definition
- awkward procedural prompts are rewritten more naturally
- expansion fills at least one missing richer family on known sparse fixtures
- ledger still builds successfully in strict mode

Review artifacts
For each course, inspection output should show:
- original candidates
- repaired versions
- dropped reasons
- derived additions
- final merged candidates
- downstream visible/hidden outcomes

Non-goals
- do not build an unrestricted chatbot
- do not let the LLM invent course content
- do not collapse the question path into the answer path
- do not make policy decisions opaque
- do not hide uncertainty when evidence is weak

Please implement the feature with minimal disruption to the existing architecture.
Prefer additive modules and clean lineage fields over large rewrites.
