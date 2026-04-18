from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import yaml

from course_pipeline.config import Settings, load_env
from course_pipeline.normalize import iter_courses
from course_pipeline.question_cache import (
    QuestionCacheFallback,
    QuestionCacheIndex,
)
from course_pipeline.schemas import LearningOutcomeExtractionOut
from course_pipeline.storage import Storage


STATIC_DIR = Path(__file__).with_name("webapp_static")


def latest_run_with_artifact(output_root: Path, artifact_name: str) -> Path | None:
    candidates = sorted(
        [path for path in output_root.iterdir() if path.is_dir() and (path / artifact_name).exists()],
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_learning_outcomes_by_course(run_dir: Path | None) -> dict[str, dict]:
    if run_dir is None:
        return {}
    path = run_dir / "learning_outcomes.jsonl"
    if not path.exists():
        return {}
    results: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = LearningOutcomeExtractionOut.model_validate_json(line).model_dump(mode="json")
            results[payload["course_id"]] = payload
    return results


def load_question_cache_by_course(run_dir: Path | None) -> dict[str, dict]:
    if run_dir is None:
        return {}
    groups_path = run_dir / "claim_question_groups.jsonl"
    variations_path = run_dir / "question_group_variations.jsonl"
    answers_path = run_dir / "canonical_answers.jsonl"
    if not groups_path.exists():
        return {}

    groups = [json.loads(line) for line in groups_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    variations = [json.loads(line) for line in variations_path.read_text(encoding="utf-8").splitlines() if line.strip()] if variations_path.exists() else []
    answers = [json.loads(line) for line in answers_path.read_text(encoding="utf-8").splitlines() if line.strip()] if answers_path.exists() else []

    variations_by_group: dict[str, list[dict]] = {}
    answers_by_group: dict[str, list[dict]] = {}
    for row in variations:
        variations_by_group.setdefault(row["question_group_id"], []).append(row)
    for row in answers:
        answers_by_group.setdefault(row["question_group_id"], []).append(row)

    by_course: dict[str, dict] = {}
    for group in groups:
        course_payload = by_course.setdefault(group["course_id"], {"question_groups": []})
        course_payload["question_groups"].append(
            {
                **group,
                "variations": variations_by_group.get(group["question_group_id"], []),
                "answers": answers_by_group.get(group["question_group_id"], []),
            }
        )
    return by_course


def load_raw_yaml_preview(raw_yaml_path: str) -> str | None:
    path = Path(raw_yaml_path)
    if not path.exists():
        return None
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return yaml.safe_dump(
        payload,
        allow_unicode=False,
        sort_keys=False,
        width=80,
    )


@dataclass
class WebAppState:
    settings: Settings
    input_dir: Path
    learning_run_dir: Path | None
    question_cache_run_dir: Path | None
    courses: dict[str, dict]
    learning_outcomes: dict[str, dict]
    question_cache: dict[str, dict]

    @cached_property
    def question_cache_index(self) -> QuestionCacheIndex | None:
        if self.question_cache_run_dir is None:
            return None
        if not (self.question_cache_run_dir / "claim_question_groups.jsonl").exists():
            return None
        return QuestionCacheIndex.from_run_dir(self.question_cache_run_dir)


def build_state(
    settings: Settings,
    input_dir: Path,
    learning_run_id: str | None = None,
    question_cache_run_id: str | None = None,
) -> WebAppState:
    learning_run_dir = settings.output_root / learning_run_id if learning_run_id else latest_run_with_artifact(settings.output_root, "learning_outcomes.jsonl")
    question_cache_run_dir = settings.output_root / question_cache_run_id if question_cache_run_id else latest_run_with_artifact(settings.output_root, "claim_question_groups.jsonl")
    courses, errors = iter_courses(input_dir)
    if errors:
        # keep server startup resilient; invalid files are already part of batch behavior
        pass
    course_map = {course.course_id: course.model_dump(mode="json") for course in courses}
    return WebAppState(
        settings=settings,
        input_dir=input_dir,
        learning_run_dir=learning_run_dir,
        question_cache_run_dir=question_cache_run_dir,
        courses=course_map,
        learning_outcomes=load_learning_outcomes_by_course(learning_run_dir),
        question_cache=load_question_cache_by_course(question_cache_run_dir),
    )


class WebAppHandler(BaseHTTPRequestHandler):
    server: "WebAppServer"

    def _json_response(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text_response(self, content: str, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self._serve_static("index.html", "text/html; charset=utf-8")
        if parsed.path == "/styles.css":
            return self._serve_static("styles.css", "text/css; charset=utf-8")
        if parsed.path == "/app.js":
            return self._serve_static("app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/api/courses":
            return self._handle_course_list()
        if parsed.path.startswith("/api/courses/"):
            course_id = parsed.path.rsplit("/", 1)[-1]
            return self._handle_course_detail(course_id)
        self._json_response({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            return self._handle_chat()
        self._json_response({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def _serve_static(self, filename: str, content_type: str) -> None:
        path = STATIC_DIR / filename
        if not path.exists():
            self._json_response({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)
            return
        self._text_response(path.read_text(encoding="utf-8"), content_type=content_type)

    def _handle_course_list(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        q = (qs.get("q", [""])[0] or "").lower().strip()
        items = []
        for course_id, course in sorted(self.server.state.courses.items(), key=lambda item: (item[1]["title"], item[0])):
            label = f"{course['title']} ({course_id})"
            if q and q not in label.lower():
                continue
            items.append(
                {
                    "course_id": course_id,
                    "title": course["title"],
                    "provider": course.get("provider"),
                    "subjects": course.get("subjects") or [],
                    "level": course.get("level"),
                    "chapter_count": len(course.get("chapters") or []),
                    "label": label,
                }
            )
        self._json_response(
            {
                "courses": items,
                "run_context": {
                    "learning_run_id": self.server.state.learning_run_dir.name if self.server.state.learning_run_dir else None,
                    "question_cache_run_id": self.server.state.question_cache_run_dir.name if self.server.state.question_cache_run_dir else None,
                },
            }
        )

    def _handle_course_detail(self, course_id: str) -> None:
        course = self.server.state.courses.get(course_id)
        if course is None:
            self._json_response({"error": "course_not_found"}, status=HTTPStatus.NOT_FOUND)
            return
        learning_outcomes = self.server.state.learning_outcomes.get(course_id)
        question_cache = self.server.state.question_cache.get(course_id)
        raw_yaml = load_raw_yaml_preview(course["raw_yaml_path"])
        payload = {
            "course": course,
            "learning_outcomes": learning_outcomes,
            "question_cache": question_cache,
            "raw_yaml": raw_yaml,
            "stats": {
                "chapter_count": len(course.get("chapters") or []),
                "learning_outcome_count": len((learning_outcomes or {}).get("learning_outcomes") or []),
                "question_group_count": len((question_cache or {}).get("question_groups") or []),
            },
            "run_context": {
                "learning_run_id": self.server.state.learning_run_dir.name if self.server.state.learning_run_dir else None,
                "question_cache_run_id": self.server.state.question_cache_run_dir.name if self.server.state.question_cache_run_dir else None,
            },
        }
        self._json_response(payload)

    def _handle_chat(self) -> None:
        body = self._read_json()
        course_id = str(body.get("course_id") or "").strip()
        question = str(body.get("question") or "").strip()
        if not course_id or not question:
            self._json_response({"error": "course_id_and_question_required"}, status=HTTPStatus.BAD_REQUEST)
            return
        if course_id not in self.server.state.courses:
            self._json_response({"error": "course_not_found"}, status=HTTPStatus.NOT_FOUND)
            return

        storage = Storage(self.server.state.settings)
        index = self.server.state.question_cache_index
        if index is None:
            result = None
        else:
            result = index.match(question, course_id=course_id)

        if result is not None and result.resolved_as_hit:
            storage.log_question_cache_match(result)
            self._json_response(
                {
                    "status": "cache_hit",
                    "answer_markdown": result.answer_markdown,
                    "course_id": result.course_id,
                    "claim_id": result.claim_id,
                    "question_group_id": result.question_group_id,
                    "canonical_answer_id": result.canonical_answer_id,
                    "match_score": result.match_score,
                    "match_method": result.match_method,
                }
            )
            return

        fallback = QuestionCacheFallback(self.server.state.settings)
        nearest_group = None
        nearest_answer = None
        if result is not None and index is not None:
            nearest_group = index.groups.get(result.question_group_id or "") if result.question_group_id else None
            nearest_answer = index.answers.get(result.canonical_answer_id or "") if result.canonical_answer_id else None
        else:
            from course_pipeline.schemas import QuestionCacheMatchResult

            result = QuestionCacheMatchResult(
                course_id=course_id,
                incoming_question=question,
                normalized_question=question.lower().strip(),
                match_method="fallback",
                match_score=0.0,
                resolved_as_hit=False,
                fallback_reason="cache_unavailable",
                candidate_for_cache_warming=True,
            )
        answer = fallback.answer(
            question=question,
            match_result=result,
            nearest_group=nearest_group,
            nearest_answer=nearest_answer,
        )
        result.answer_markdown = answer
        storage.log_question_cache_match(result)
        storage.log_question_cache_fallback(result)
        self._json_response(
            {
                "status": "cache_miss",
                "answer_markdown": answer,
                "course_id": course_id,
                "claim_id": result.claim_id,
                "question_group_id": result.question_group_id,
                "canonical_answer_id": result.canonical_answer_id,
                "match_score": result.match_score,
                "fallback_reason": result.fallback_reason,
                "match_method": result.match_method,
            }
        )


class WebAppServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], state: WebAppState) -> None:
        super().__init__(server_address, WebAppHandler)
        self.state = state


def serve_web_app(
    settings: Settings,
    input_dir: Path,
    host: str,
    port: int,
    learning_run_id: str | None = None,
    question_cache_run_id: str | None = None,
) -> None:
    load_env()
    state = build_state(
        settings=settings,
        input_dir=input_dir,
        learning_run_id=learning_run_id,
        question_cache_run_id=question_cache_run_id,
    )
    server = WebAppServer((host, port), state)
    print(f"serving web app on http://{host}:{port}")  # noqa: T201
    server.serve_forever()
