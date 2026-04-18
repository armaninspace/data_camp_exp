from __future__ import annotations

from pathlib import Path

try:
    from prefect.artifacts import create_markdown_artifact
except Exception:  # noqa: BLE001
    create_markdown_artifact = None


def normalize_artifact_key(value: str) -> str:
    normalized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


def publish_markdown(key: str, markdown: str) -> None:
    if create_markdown_artifact is None:
        return
    create_markdown_artifact(key=normalize_artifact_key(key), markdown=markdown)


def build_artifact_index_entries(stage: str, paths: list[Path], run_root: Path) -> list[dict[str, str | int | None]]:
    entries: list[dict[str, str | int | None]] = []
    for path in paths:
        try:
            relative_path = str(path.relative_to(run_root))
        except ValueError:
            relative_path = str(path)
        entries.append(
            {
                "artifact_type": path.suffix.lstrip(".") or "directory",
                "relative_path": relative_path,
                "stage": stage,
                "row_count": None,
                "content_type": "directory" if path.is_dir() else "file",
            }
        )
    return entries
