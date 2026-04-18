from course_pipeline.question_gen_v4.policy_models import PolicyScores
from course_pipeline.question_gen_v4_1.policy_models import CandidateRecord
from course_pipeline.question_ledger_v6.config import load_default_config
from course_pipeline.question_ledger_v6.normalize import (
    ledger_tags,
    normalize_question_text,
    normalize_question_type,
    select_question_family,
)


def _record(**overrides) -> CandidateRecord:
    base = CandidateRecord(
        candidate_id="c1",
        question="What is repeated cycles?",
        answer="",
        topic_ids=["seasonality"],
        canonical_id="c1",
        is_correct=True,
        is_grounded=True,
        delivery_class="analysis_only",
        visible=False,
        non_visible_reasons=["analysis_only_low_distinctiveness"],
        scores=PolicyScores(
            correctness=0.9,
            groundedness=0.9,
            contradiction_risk=0.1,
            coherence=0.9,
            query_likelihood=0.9,
            pedagogical_value=0.8,
            answer_richness=0.7,
            mastery_fit=0.9,
            distinctiveness=0.4,
            serviceability=0.8,
            context_dependence=0.3,
            answer_stability=0.8,
        ),
        source_refs=["source"],
        is_foundational_anchor=True,
        is_required_entry_candidate=True,
        is_canonical=True,
        is_alias=False,
        question_type="definition",
        mastery_band="novice",
        family_tags=["entry"],
    )
    return base.model_copy(update=overrides)


def test_load_default_config_contains_required_outputs():
    cfg = load_default_config()
    assert cfg["outputs"]["authoritative_ledger"] == "all_questions.jsonl"
    assert "delivery_classes" in cfg
    assert "curated_visible" in cfg["delivery_classes"]


def test_normalize_question_type_maps_transfer_to_application():
    assert normalize_question_type("transfer") == "application"
    assert normalize_question_type("orientation") == "purpose"


def test_select_question_family_prefers_explicit_tag():
    assert select_question_family(["diagnostic", "friction"], "diagnostic") == "friction"
    assert select_question_family([], "comparison") == "bridge"


def test_normalize_question_text_fixes_known_awkward_forms():
    assert normalize_question_text("What is repeated cycles?") == "What are repeated cycles?"
    assert normalize_question_text("What is ljung-box test?") == "What is the Ljung-Box test?"


def test_ledger_tags_include_foundational_and_protected():
    record = _record()
    tags = ledger_tags(record, family="entry", question_type="definition")
    assert "foundational" in tags
    assert "protected" in tags
    assert "hidden" in tags
