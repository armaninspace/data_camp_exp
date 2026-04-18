import json

from course_pipeline.questions.ledger.models import AnchorSummary, LedgerRow, LedgerScores
from course_pipeline.questions.ledger.run import build_v6_review_bundle, write_v6_run_report
from course_pipeline.schemas import ChapterOut, NormalizedCourse


def _row(**overrides) -> LedgerRow:
    base = LedgerRow(
        question_id="q1",
        question_text="What is seasonality?",
        answer_text="",
        anchor_id="seasonality",
        anchor_label="Seasonality",
        tracked_topics=["seasonality"],
        anchor_type="foundational_vocabulary",
        question_family="entry",
        question_type="definition",
        mastery_band="novice",
        canonical=True,
        alias=False,
        canonical_target=None,
        required_entry=True,
        validated_correct=True,
        grounded=True,
        serviceable=True,
        delivery_class="curated_visible",
        visible=True,
        non_visible_reasons=[],
        reject_reasons=[],
        tags=["entry", "definition", "foundational", "protected"],
        scores=LedgerScores(
            groundedness=0.9,
            correctness=0.9,
            query_likelihood=0.9,
            pedagogical_value=0.8,
            serviceability=0.85,
            distinctiveness=0.4,
        ),
        source_refs=["src1"],
    )
    return base.model_copy(update=overrides)


def _course() -> NormalizedCourse:
    return NormalizedCourse(
        course_id="24491",
        source_url="https://example.com",
        final_url="https://example.com",
        provider="DataCamp",
        title="Forecasting in R",
        summary="Summary",
        overview="Overview",
        raw_yaml_path="/tmp/course.yaml",
        chapters=[
            ChapterOut(
                chapter_index=1,
                title="Intro",
                summary="Intro summary",
                source="syllabus",
                confidence=1.0,
            )
        ],
    )


def test_write_v6_run_report(tmp_path):
    per_course = {
        "24491": {
            "all_questions": [_row()],
            "visible_curated": [_row()],
            "cache_servable": [],
            "aliases": [],
            "anchor_summaries": [
                AnchorSummary(
                    anchor_id="seasonality",
                    anchor_label="Seasonality",
                    anchor_type="foundational_vocabulary",
                    coverage_status="PASS",
                    generated_count=1,
                    validated_correct_count=1,
                    visible_count=1,
                    cache_servable_count=0,
                    analysis_only_count=0,
                    hard_reject_count=0,
                    required_entry_exists=True,
                    required_entry_visible=True,
                )
            ],
        }
    }
    path = write_v6_run_report(tmp_path, per_course)
    text = path.read_text()
    assert "all questions: 1" in text
    assert "anchors with non-pass coverage: 0" in text


def test_build_v6_review_bundle_writes_course_file(tmp_path):
    course = _course()
    per_course = {
        "24491": {
            "all_questions": [_row()],
            "visible_curated": [_row()],
            "cache_servable": [],
            "aliases": [],
            "inspection_report": "# Report\n\nBody\n",
        }
    }
    outputs = build_v6_review_bundle(tmp_path, [course], per_course)
    bundle_dir = outputs["review_bundle"]
    files = list(bundle_dir.glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text()
    assert "Ledger Summary" in text
    assert "## All Questions" in text
    assert "### What is seasonality?" in text
    assert "- question_id: q1" in text
    assert '- tracked_topics: ["seasonality"]' in text
    assert "- delivery_class: curated_visible" in text
    assert "## Course Content" in text
    assert "### Summary" in text
    assert "Summary" in text
    assert "### Overview" in text
    assert "Overview" in text
    assert "### Syllabus" in text
    assert "Chapter 1: Intro" in text
    assert "summary: Intro summary" in text
    assert "# Report" in text
