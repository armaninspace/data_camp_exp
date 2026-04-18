from __future__ import annotations

from pathlib import Path

import yaml

from course_pipeline.questions.policy.config import load_default_config as load_v4_default_config


def _deep_merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_default_config() -> dict:
    base = load_v4_default_config()
    patch_path = Path(__file__).with_name("policy_config_patch.yaml")
    patch = yaml.safe_load(patch_path.read_text(encoding="utf-8")) or {}
    merged = _deep_merge(base, patch)
    thresholds = patch.get("thresholds", {})
    if "alias_similarity_threshold" in thresholds:
        merged.setdefault("canonicalization", {})["alias_similarity_threshold"] = thresholds["alias_similarity_threshold"]
    return merged
