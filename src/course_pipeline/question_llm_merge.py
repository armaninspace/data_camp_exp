from __future__ import annotations

from course_pipeline.question_llm_schemas import CandidateMergeRecord, CandidateRepairRecord, DerivedCandidateRecord
from course_pipeline.questions.candidates.models import QuestionCandidate, TopicNode
from course_pipeline.utils import slugify


SLOT_BY_QUESTION_TYPE: dict[tuple[str, str], str] = {
    ("novice", "orientation"): "novice_orientation",
    ("novice", "definition"): "novice_definition",
    ("novice", "purpose"): "novice_orientation",
    ("developing", "procedure"): "developing_procedural",
    ("developing", "comparison"): "developing_comparison",
    ("developing", "misconception"): "developing_misconception",
    ("proficient", "diagnostic"): "proficient_diagnostic",
    ("proficient", "interpretation"): "proficient_diagnostic",
    ("proficient", "transfer"): "proficient_transfer",
    ("proficient", "comparison"): "developing_comparison",
    ("proficient", "when_to_use"): "proficient_transfer",
}


def _infer_slot(mastery_band: str, question_type: str) -> str:
    return SLOT_BY_QUESTION_TYPE.get((mastery_band, question_type), "developing_procedural")


def merge_llm_candidates(
    *,
    course_id: str,
    raw_candidates: list[QuestionCandidate],
    repair_records: list[CandidateRepairRecord],
    derived_candidates: list[DerivedCandidateRecord],
    topics: list[TopicNode],
) -> tuple[list[QuestionCandidate], list[CandidateMergeRecord]]:
    topic_by_id = {topic.topic_id: topic for topic in topics}
    topic_id_by_label = {topic.label.lower(): topic.topic_id for topic in topics}
    for topic in topics:
        for alias in topic.aliases:
            topic_id_by_label.setdefault(alias.lower(), topic.topic_id)

    repairs_by_source = {record.source_question_id: record for record in repair_records}
    merged: list[QuestionCandidate] = []
    merge_records: list[CandidateMergeRecord] = []

    for candidate in raw_candidates:
        repair = repairs_by_source.get(candidate.candidate_id)
        if repair is None or repair.action == "keep":
            merged.append(candidate.model_copy(update={"provenance_note": "original candidate preserved"}))
            merge_records.append(
                CandidateMergeRecord(
                    course_id=course_id,
                    candidate_id=candidate.candidate_id,
                    source_kind="original",
                    source_question_id=candidate.candidate_id,
                    llm_stage=None if repair is None else "repair",
                    provenance_note="kept original candidate",
                    original_question=candidate.question_text,
                    final_question=candidate.question_text,
                )
            )
            continue
        if repair.action == "rewrite":
            rewritten_question = repair.repaired_question or candidate.question_text
            merged.append(
                candidate.model_copy(
                    update={
                        "question_text": rewritten_question,
                        "source_kind": "repaired",
                        "source_question_id": candidate.candidate_id,
                        "llm_stage": "repair",
                        "provenance_note": repair.repair_reason,
                        "llm_repair_confidence": repair.confidence,
                        "llm_grounding_confidence": repair.confidence,
                    }
                )
            )
            merge_records.append(
                CandidateMergeRecord(
                    course_id=course_id,
                    candidate_id=candidate.candidate_id,
                    source_kind="repaired",
                    source_question_id=candidate.candidate_id,
                    llm_stage="repair",
                    provenance_note=repair.repair_reason,
                    original_question=candidate.question_text,
                    final_question=rewritten_question,
                )
            )
            continue
        merge_records.append(
            CandidateMergeRecord(
                course_id=course_id,
                candidate_id=candidate.candidate_id,
                source_kind="repaired",
                source_question_id=candidate.candidate_id,
                llm_stage="repair",
                provenance_note=repair.repair_reason,
                original_question=candidate.question_text,
                final_question="",
            )
        )

    for index, derived in enumerate(derived_candidates, start=1):
        topic_id = topic_id_by_label.get(derived.anchor_label.lower())
        if topic_id is None:
            continue
        topic = topic_by_id[topic_id]
        candidate_id = f"{topic_id}-llm-{slugify(derived.question_text)}-{index}"
        merged.append(
            QuestionCandidate(
                candidate_id=candidate_id,
                topic_id=topic_id,
                slot=_infer_slot(derived.mastery_band, derived.question_type),  # type: ignore[arg-type]
                mastery_band=derived.mastery_band,
                question_type=derived.question_type,
                question_text=derived.question_text,
                rationale=derived.derivation_reason,
                source_support=[derived.grounding_rationale or topic.description],
                linked_friction_ids=[],
                section_ids=list(topic.source_section_ids),
                source_kind="derived",
                source_question_id=None,
                llm_stage="expand",
                provenance_note=derived.derivation_reason,
                derived_by_llm=True,
                llm_derivation_confidence=derived.confidence,
                llm_grounding_confidence=derived.confidence,
            )
        )
        merge_records.append(
            CandidateMergeRecord(
                course_id=course_id,
                candidate_id=candidate_id,
                source_kind="derived",
                source_question_id=None,
                llm_stage="expand",
                provenance_note=derived.derivation_reason,
                original_question=None,
                final_question=derived.question_text,
            )
        )

    return merged, merge_records
