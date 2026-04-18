from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median


ROOT = Path("/code/docs/bundle_data_products")
MANIFEST_PATH = ROOT / "manifest.json"
OUT_PATH = ROOT / "scale_summary.json"


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def manifest_count(run_name: str, suffix: str) -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for item in manifest[run_name]["files"]:
        if item["path"].endswith(suffix):
            return int(item["records"] or 0)
    raise KeyError(f"missing {suffix} in manifest for {run_name}")


def learning_outcome_stats(run_name: str) -> dict:
    rows = load_jsonl(ROOT / run_name / "learning_outcomes.jsonl")
    nested_counts = [len(row.get("learning_outcomes") or []) for row in rows]
    return {
        "payload_rows": len(rows),
        "nested_learning_outcomes": sum(nested_counts),
        "nested_min": min(nested_counts) if nested_counts else 0,
        "nested_median": median(nested_counts) if nested_counts else 0,
        "nested_mean": round(mean(nested_counts), 2) if nested_counts else 0,
        "nested_max": max(nested_counts) if nested_counts else 0,
        "nested_zero_count": sum(1 for value in nested_counts if value == 0),
        "nested_gt10_count": sum(1 for value in nested_counts if value > 10),
    }


def question_cache_stats(run_name: str) -> dict:
    root = ROOT / run_name
    groups = load_jsonl(root / "claim_question_groups.jsonl")
    variations = load_jsonl(root / "question_group_variations.jsonl")
    answers = load_jsonl(root / "canonical_answers.jsonl")
    validation_logs = load_jsonl(root / "question_cache_validation_logs.jsonl")
    coverage_audit = load_jsonl(root / "claim_coverage_audit.jsonl")
    accepted_answers = [
        row for row in answers
        if row.get("answer_fit_status") == "pass" and row.get("grounding_status") == "pass"
    ]
    return {
        "question_groups": len(groups),
        "validated_groups": sum(1 for row in groups if row.get("validator_status") == "validated"),
        "variations": len(variations),
        "accepted_variations": sum(1 for row in variations if row.get("accepted_for_runtime")),
        "canonical_answers": len(answers),
        "accepted_answers": len(accepted_answers),
        "validation_logs": len(validation_logs),
        "coverage_audits": len(coverage_audit),
        "claims_with_groups": sum(1 for row in coverage_audit if row.get("produced_question_groups")),
    }


def legacy_stats(run_name: str) -> dict:
    return {
        "course_rows": manifest_count(run_name, "courses.jsonl"),
        "chapter_rows": manifest_count(run_name, "chapters.jsonl"),
        "topic_rows": manifest_count(run_name, "topics.jsonl"),
        "edge_rows": manifest_count(run_name, "edges.jsonl"),
        "pedagogical_profile_rows": manifest_count(run_name, "pedagogical_profiles.jsonl"),
        "predicted_question_rows": manifest_count(run_name, "predicted_questions.jsonl"),
        "error_rows": manifest_count(run_name, "errors.jsonl"),
    }


def main() -> None:
    summary = {
        "source_manifest": str(MANIFEST_PATH),
        "runs": {
            "legacy_semantic_run_20260413T215831Z": {
                "run_type": "bounded_sample_legacy_semantic",
                **legacy_stats("legacy_semantic_run_20260413T215831Z"),
            },
            "learning_outcomes_sample_run_20260414T025608Z": {
                "run_type": "bounded_sample_learning_outcomes",
                "course_rows": manifest_count("learning_outcomes_sample_run_20260414T025608Z", "courses.jsonl"),
                "chapter_rows": manifest_count("learning_outcomes_sample_run_20260414T025608Z", "chapters.jsonl"),
                "error_rows": manifest_count("learning_outcomes_sample_run_20260414T025608Z", "learning_outcome_errors.jsonl"),
                **learning_outcome_stats("learning_outcomes_sample_run_20260414T025608Z"),
            },
            "question_cache_sample_run_20260414T044551Z": {
                "run_type": "bounded_sample_question_cache",
                "error_rows": manifest_count("question_cache_sample_run_20260414T044551Z", "question_cache_errors.jsonl"),
                **question_cache_stats("question_cache_sample_run_20260414T044551Z"),
            },
            "learning_outcomes_full_corpus_run_20260414T052429Z": {
                "run_type": "full_corpus_learning_outcomes",
                "course_rows": manifest_count("learning_outcomes_full_corpus_run_20260414T052429Z", "courses.jsonl"),
                "chapter_rows": manifest_count("learning_outcomes_full_corpus_run_20260414T052429Z", "chapters.jsonl"),
                "error_rows": manifest_count("learning_outcomes_full_corpus_run_20260414T052429Z", "learning_outcome_errors.jsonl"),
                **learning_outcome_stats("learning_outcomes_full_corpus_run_20260414T052429Z"),
            },
        },
    }
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(OUT_PATH)  # noqa: T201


if __name__ == "__main__":
    main()
