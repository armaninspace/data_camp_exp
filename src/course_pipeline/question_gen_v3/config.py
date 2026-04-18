from __future__ import annotations

from pathlib import Path

import yaml


def load_default_config() -> dict:
    path = Path(__file__).with_name("question_gen_v3_config.yaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
