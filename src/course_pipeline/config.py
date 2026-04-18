from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_ENV_PATHS = [Path("/code/data/.env"), Path("/code/.env")]


def load_env() -> None:
    for path in DEFAULT_ENV_PATHS:
        if path.exists():
            load_dotenv(path, override=False)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    openai_timeout: int
    database_url: str
    output_root: Path


def get_settings() -> Settings:
    load_env()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        openai_timeout=int(os.getenv("OPENAI_TIMEOUT", "180")),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://agent@127.0.0.1:55432/course_pipeline",
        ),
        output_root=Path(os.getenv("PIPELINE_OUTPUT_ROOT", "/code/data/pipeline_runs")),
    )
