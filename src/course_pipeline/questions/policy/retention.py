from __future__ import annotations

from course_pipeline.questions.policy.models import PolicyDecision, RetentionRecord


def build_retention_records(decisions: list[PolicyDecision], config: dict) -> list[RetentionRecord]:
    policy = config["retention"]
    records: list[RetentionRecord] = []
    for decision in decisions:
        retention_mode = policy[decision.policy_bucket]
        records.append(
            RetentionRecord(
                candidate_id=decision.candidate_id,
                policy_bucket=decision.policy_bucket,
                store_full_record=retention_mode == "full",
                store_answer_text=retention_mode == "full" and decision.policy_bucket in {"curated_core", "cache_servable"},
                store_audit_only=retention_mode == "audit_only",
            )
        )
    return records
