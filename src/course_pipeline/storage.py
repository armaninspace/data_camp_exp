from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from course_pipeline.config import Settings
from course_pipeline.schemas import ChapterOut, NormalizedCourse


DDL = """
create table if not exists extraction_runs (
  run_id text primary key,
  created_at timestamptz not null default now(),
  pipeline_version text not null,
  input_dir text not null,
  notes jsonb not null default '{}'::jsonb
);

create table if not exists source_files (
  source_file_id bigserial primary key,
  run_id text not null references extraction_runs(run_id),
  raw_yaml_path text not null,
  course_id text not null,
  parse_status text not null,
  error_text text,
  unique (run_id, raw_yaml_path)
);

create table if not exists courses (
  course_pk bigserial primary key,
  run_id text not null references extraction_runs(run_id),
  course_id text not null,
  source_url text not null,
  final_url text,
  provider text not null,
  title text not null,
  summary text,
  overview text,
  level text,
  duration_hours double precision,
  pricing text,
  language text,
  subjects jsonb not null default '[]'::jsonb,
  ratings jsonb not null default '{}'::jsonb,
  details jsonb not null default '{}'::jsonb,
  raw_yaml_path text not null,
  fetched_at timestamptz,
  unique (run_id, course_id)
);

create table if not exists chapters (
  chapter_pk bigserial primary key,
  run_id text not null references extraction_runs(run_id),
  course_id text not null,
  chapter_index integer not null,
  title text not null,
  summary text,
  source text not null,
  confidence double precision not null,
  unique (run_id, course_id, chapter_index)
);
"""


class Storage:
    def __init__(self, settings: Settings) -> None:
        self.engine: Engine = create_engine(settings.database_url, future=True)

    def init_db(self) -> None:
        with self.engine.begin() as conn:
            for statement in DDL.strip().split(";\n\n"):
                if statement.strip():
                    conn.execute(text(statement))

    def create_run(self, input_dir: str, notes: dict | None = None) -> str:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into extraction_runs (run_id, pipeline_version, input_dir, notes)
                    values (:run_id, :pipeline_version, :input_dir, cast(:notes as jsonb))
                    """
                ),
                {
                    "run_id": run_id,
                    "pipeline_version": "0.1.0",
                    "input_dir": input_dir,
                    "notes": json.dumps(notes or {}),
                },
            )
        return run_id

    def record_source_files(self, run_id: str, courses: Iterable[NormalizedCourse], errors: list[dict]) -> None:
        with self.engine.begin() as conn:
            for course in courses:
                conn.execute(
                    text(
                        """
                        insert into source_files (run_id, raw_yaml_path, course_id, parse_status, error_text)
                        values (:run_id, :raw_yaml_path, :course_id, 'ok', null)
                        on conflict (run_id, raw_yaml_path) do update
                        set parse_status = excluded.parse_status
                        """
                    ),
                    {
                        "run_id": run_id,
                        "raw_yaml_path": course.raw_yaml_path,
                        "course_id": course.course_id,
                    },
                )
            for error in errors:
                conn.execute(
                    text(
                        """
                        insert into source_files (run_id, raw_yaml_path, course_id, parse_status, error_text)
                        values (:run_id, :raw_yaml_path, :course_id, 'error', :error_text)
                        on conflict (run_id, raw_yaml_path) do update
                        set parse_status = excluded.parse_status,
                            error_text = excluded.error_text
                        """
                    ),
                    {
                        "run_id": run_id,
                        "raw_yaml_path": error["path"],
                        "course_id": slugify(error["path"]),
                        "error_text": error["error"],
                    },
                )

    def upsert_courses(self, run_id: str, courses: Iterable[NormalizedCourse]) -> None:
        with self.engine.begin() as conn:
            for course in courses:
                conn.execute(
                    text(
                        """
                        insert into courses (
                          run_id, course_id, source_url, final_url, provider, title, summary,
                          overview, level, duration_hours, pricing, language, subjects,
                          ratings, details, raw_yaml_path, fetched_at
                        )
                        values (
                          :run_id, :course_id, :source_url, :final_url, :provider, :title,
                          :summary, :overview, :level, :duration_hours, :pricing,
                          :language, cast(:subjects as jsonb), cast(:ratings as jsonb),
                          cast(:details as jsonb), :raw_yaml_path, :fetched_at
                        )
                        on conflict (run_id, course_id) do update set
                          source_url = excluded.source_url,
                          final_url = excluded.final_url,
                          provider = excluded.provider,
                          title = excluded.title,
                          summary = excluded.summary,
                          overview = excluded.overview,
                          level = excluded.level,
                          duration_hours = excluded.duration_hours,
                          pricing = excluded.pricing,
                          language = excluded.language,
                          subjects = excluded.subjects,
                          ratings = excluded.ratings,
                          details = excluded.details,
                          raw_yaml_path = excluded.raw_yaml_path,
                          fetched_at = excluded.fetched_at
                        """
                    ),
                    {
                        "run_id": run_id,
                        "course_id": course.course_id,
                        "source_url": course.source_url,
                        "final_url": course.final_url,
                        "provider": course.provider,
                        "title": course.title,
                        "summary": course.summary,
                        "overview": course.overview,
                        "level": course.level,
                        "duration_hours": course.duration_hours,
                        "pricing": course.pricing,
                        "language": course.language,
                        "subjects": json.dumps(course.subjects),
                        "ratings": json.dumps(course.ratings),
                        "details": json.dumps(course.details),
                        "raw_yaml_path": course.raw_yaml_path,
                        "fetched_at": course.fetched_at,
                    },
                )
                for chapter in course.chapters:
                    self.upsert_chapter(conn, run_id, course.course_id, chapter)

    def upsert_chapter(self, conn, run_id: str, course_id: str, chapter: ChapterOut) -> None:
        conn.execute(
            text(
                """
                insert into chapters (run_id, course_id, chapter_index, title, summary, source, confidence)
                values (:run_id, :course_id, :chapter_index, :title, :summary, :source, :confidence)
                on conflict (run_id, course_id, chapter_index) do update set
                  title = excluded.title,
                  summary = excluded.summary,
                  source = excluded.source,
                  confidence = excluded.confidence
                """
            ),
            {
                "run_id": run_id,
                "course_id": course_id,
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "summary": chapter.summary,
                "source": chapter.source,
                "confidence": chapter.confidence,
            },
        )
