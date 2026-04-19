from __future__ import annotations

from course_pipeline.foundational_entry_questions import is_plain_definition_question, plain_definition_question
from course_pipeline.questions.candidates.generate_candidates import generate_candidates
from course_pipeline.questions.candidates.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    QuestionCandidate,
    SeedGenerationInvariantReport,
    TopicEdge,
    TopicNode,
)
from course_pipeline.semantic_schemas import AnchorCandidate
from course_pipeline.utils import slugify


def generate_seed_candidates(
    doc: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    config: dict,
    anchors: list[AnchorCandidate] | None = None,
) -> dict:
    candidates = generate_candidates(doc, topics, edges, pedagogy, frictions, config)
    return _enforce_required_entry_invariant(
        doc=doc,
        topics=topics,
        frictions=frictions,
        candidates=candidates,
        anchors=anchors,
    )


def _enforce_required_entry_invariant(
    *,
    doc: CanonicalDocument,
    topics: list[TopicNode],
    frictions: list[FrictionPoint],
    candidates: list[QuestionCandidate],
    anchors: list[AnchorCandidate] | None,
) -> dict:
    topics_by_id = {topic.topic_id: topic for topic in topics}
    topics_by_label = {topic.label.strip().lower(): topic for topic in topics}
    anchors_requiring_entry = [anchor for anchor in anchors or [] if anchor.requires_entry_question]
    protected_seeds_found: list[str] = []
    protected_seeds_synthesized: list[str] = []
    missing_protected_seeds: list[str] = []
    warnings: list[str] = []
    synthesized: list[QuestionCandidate] = []

    for anchor in anchors_requiring_entry:
        topic = topics_by_id.get(anchor.anchor_id) or topics_by_label.get(anchor.label.strip().lower())
        label = topic.label if topic is not None else anchor.label
        topic_id = topic.topic_id if topic is not None else anchor.anchor_id
        has_plain_definition = any(
            candidate.topic_id == topic_id
            and candidate.question_type == "definition"
            and is_plain_definition_question(label, candidate.question_text)
            for candidate in candidates
        )
        if has_plain_definition:
            protected_seeds_found.append(anchor.anchor_id)
            continue
        if topic is None:
            missing_protected_seeds.append(anchor.anchor_id)
            warnings.append(f"missing topic for required-entry anchor `{anchor.anchor_id}`")
            continue
        synthesized.append(_synthesized_definition_candidate(topic, frictions))
        protected_seeds_synthesized.append(anchor.anchor_id)

    return {
        "candidates": synthesized + candidates,
        "invariant_report": SeedGenerationInvariantReport(
            course_id=doc.doc_id,
            anchors_requiring_entry=[anchor.anchor_id for anchor in anchors_requiring_entry],
            protected_seeds_found=protected_seeds_found,
            protected_seeds_synthesized=protected_seeds_synthesized,
            missing_protected_seeds=missing_protected_seeds,
            warnings=warnings,
        ),
    }


def _synthesized_definition_candidate(topic: TopicNode, frictions: list[FrictionPoint]) -> QuestionCandidate:
    question_text = plain_definition_question(topic.label)
    return QuestionCandidate(
        candidate_id=slugify(f"{topic.topic_id}-novice-definition-{question_text}")[:120],
        topic_id=topic.topic_id,
        slot="novice_definition",
        mastery_band="novice",
        question_type="definition",
        question_text=question_text,
        rationale="Deterministically synthesized to satisfy the required-entry seed invariant.",
        source_support=[topic.description],
        linked_friction_ids=[friction.friction_id for friction in frictions if friction.topic_id == topic.topic_id],
        section_ids=topic.source_section_ids,
    )
