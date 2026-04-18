from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from course_pipeline.config import Settings
from course_pipeline.schemas import (
    CanonicalAnswerOut,
    ChapterOut,
    ClaimCoverageAuditOut,
    ClaimQuestionGroupOut,
    LearningOutcomeExtractionOut,
    NormalizedCourse,
    QuestionCacheMatchResult,
    QuestionCacheValidationLogOut,
    QuestionGroupVariationOut,
)
from course_pipeline.utils import slugify


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

create table if not exists learning_outcome_extractions (
  learning_outcome_extraction_pk bigserial primary key,
  run_id text not null references extraction_runs(run_id),
  course_id text not null,
  course_title text not null,
  payload jsonb not null,
  unique (run_id, course_id)
);

create table if not exists claim_question_groups (
  question_group_id text primary key,
  course_id text not null,
  claim_id text not null,
  intent_slug text not null,
  canonical_question text not null,
  pedagogical_move text not null,
  canonical_answer_id text not null,
  confidence double precision not null,
  citations jsonb not null default '[]'::jsonb,
  source_run_id text not null,
  prompt_version text not null,
  generation_stage text not null default 'atomized',
  validator_status text not null default 'pending',
  coverage_status text not null default 'accounted_for',
  created_at timestamptz not null default now(),
  unique (course_id, claim_id, intent_slug)
);

create index if not exists idx_claim_question_groups_course_id on claim_question_groups (course_id);
create index if not exists idx_claim_question_groups_claim_id on claim_question_groups (claim_id);

create table if not exists question_group_variations (
  variation_id text primary key,
  question_group_id text not null references claim_question_groups(question_group_id),
  text text not null,
  normalized_text text not null,
  equivalence_notes text not null,
  source text not null,
  candidate_source text not null default 'variation_generation',
  validation_decision text not null default 'pending',
  validation_reason text,
  accepted_for_runtime boolean not null default false,
  created_at timestamptz not null default now(),
  unique (question_group_id, normalized_text)
);

create index if not exists idx_question_group_variations_group_id on question_group_variations (question_group_id);
create index if not exists idx_question_group_variations_normalized_text on question_group_variations (normalized_text);

create table if not exists canonical_answers (
  canonical_answer_id text primary key,
  question_group_id text not null references claim_question_groups(question_group_id),
  answer_markdown text not null,
  answer_style text not null,
  answer_version integer not null,
  reviewer_state text not null,
  citations jsonb not null default '[]'::jsonb,
  source_run_id text not null,
  prompt_version text not null,
  answer_fit_status text not null default 'pending',
  grounding_status text not null default 'pending',
  grounding_reason text,
  answer_scope_notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_canonical_answers_group_id on canonical_answers (question_group_id);

create table if not exists question_cache_match_logs (
  match_log_id bigserial primary key,
  course_id text,
  claim_id text,
  question_group_id text,
  variation_id text,
  canonical_answer_id text,
  incoming_question text not null,
  normalized_question text not null,
  match_method text not null,
  match_score double precision not null,
  resolved_as_hit boolean not null,
  created_at timestamptz not null default now()
);

create table if not exists question_cache_fallback_logs (
  fallback_log_id bigserial primary key,
  course_id text,
  claim_id text,
  incoming_question text not null,
  normalized_question text not null,
  fallback_reason text not null,
  llm_response_id text,
  response_markdown text,
  candidate_for_cache_warming boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists question_cache_validation_logs (
  validation_log_id bigserial primary key,
  entity_type text not null,
  entity_id text not null,
  validator_type text not null,
  decision text not null,
  reason text,
  model_version text,
  created_at timestamptz not null default now()
);

create table if not exists claim_coverage_audit (
  audit_id bigserial primary key,
  course_id text not null,
  claim_id text not null,
  produced_question_groups boolean not null,
  question_group_count integer not null default 0,
  no_groups_reason text,
  source_run_id text not null,
  created_at timestamptz not null default now(),
  unique (source_run_id, course_id, claim_id)
);

alter table if exists claim_question_groups add column if not exists generation_stage text not null default 'atomized';
alter table if exists claim_question_groups add column if not exists validator_status text not null default 'pending';
alter table if exists claim_question_groups add column if not exists coverage_status text not null default 'accounted_for';
alter table if exists question_group_variations add column if not exists candidate_source text not null default 'variation_generation';
alter table if exists question_group_variations add column if not exists validation_decision text not null default 'pending';
alter table if exists question_group_variations add column if not exists validation_reason text;
alter table if exists question_group_variations add column if not exists accepted_for_runtime boolean not null default false;
alter table if exists canonical_answers add column if not exists answer_fit_status text not null default 'pending';
alter table if exists canonical_answers add column if not exists grounding_status text not null default 'pending';
alter table if exists canonical_answers add column if not exists grounding_reason text;
alter table if exists canonical_answers add column if not exists answer_scope_notes text;
alter table if exists question_cache_fallback_logs add column if not exists response_markdown text;
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

    def upsert_learning_outcome_extraction(
        self,
        run_id: str,
        extraction: LearningOutcomeExtractionOut,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into learning_outcome_extractions (run_id, course_id, course_title, payload)
                    values (:run_id, :course_id, :course_title, cast(:payload as jsonb))
                    on conflict (run_id, course_id) do update set
                      course_title = excluded.course_title,
                      payload = excluded.payload
                    """
                ),
                {
                    "run_id": run_id,
                    "course_id": extraction.course_id,
                    "course_title": extraction.course_title,
                    "payload": extraction.model_dump_json(),
                },
            )

    def upsert_question_group(self, group: ClaimQuestionGroupOut) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into claim_question_groups (
                      question_group_id, course_id, claim_id, intent_slug, canonical_question,
                      pedagogical_move, canonical_answer_id, confidence, citations,
                      source_run_id, prompt_version, generation_stage, validator_status, coverage_status
                    )
                    values (
                      :question_group_id, :course_id, :claim_id, :intent_slug, :canonical_question,
                      :pedagogical_move, :canonical_answer_id, :confidence, cast(:citations as jsonb),
                      :source_run_id, :prompt_version, :generation_stage, :validator_status, :coverage_status
                    )
                    on conflict (question_group_id) do update set
                      canonical_question = excluded.canonical_question,
                      pedagogical_move = excluded.pedagogical_move,
                      canonical_answer_id = excluded.canonical_answer_id,
                      confidence = excluded.confidence,
                      citations = excluded.citations,
                      source_run_id = excluded.source_run_id,
                      prompt_version = excluded.prompt_version,
                      generation_stage = excluded.generation_stage,
                      validator_status = excluded.validator_status,
                      coverage_status = excluded.coverage_status
                    """
                ),
                {
                    **group.model_dump(mode="json"),
                    "citations": json.dumps([c.model_dump(mode="json") for c in group.citations]),
                },
            )

    def upsert_question_variation(self, variation: QuestionGroupVariationOut) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into question_group_variations (
                      variation_id, question_group_id, text, normalized_text, equivalence_notes, source,
                      candidate_source, validation_decision, validation_reason, accepted_for_runtime
                    )
                    values (
                      :variation_id, :question_group_id, :text, :normalized_text, :equivalence_notes, :source,
                      :candidate_source, :validation_decision, :validation_reason, :accepted_for_runtime
                    )
                    on conflict (variation_id) do update set
                      text = excluded.text,
                      normalized_text = excluded.normalized_text,
                      equivalence_notes = excluded.equivalence_notes,
                      source = excluded.source,
                      candidate_source = excluded.candidate_source,
                      validation_decision = excluded.validation_decision,
                      validation_reason = excluded.validation_reason,
                      accepted_for_runtime = excluded.accepted_for_runtime
                    """
                ),
                variation.model_dump(mode="json"),
            )

    def upsert_canonical_answer(self, answer: CanonicalAnswerOut) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into canonical_answers (
                      canonical_answer_id, question_group_id, answer_markdown, answer_style,
                      answer_version, reviewer_state, citations, source_run_id, prompt_version,
                      answer_fit_status, grounding_status, grounding_reason, answer_scope_notes
                    )
                    values (
                      :canonical_answer_id, :question_group_id, :answer_markdown, :answer_style,
                      :answer_version, :reviewer_state, cast(:citations as jsonb), :source_run_id, :prompt_version,
                      :answer_fit_status, :grounding_status, :grounding_reason, :answer_scope_notes
                    )
                    on conflict (canonical_answer_id) do update set
                      answer_markdown = excluded.answer_markdown,
                      answer_style = excluded.answer_style,
                      answer_version = excluded.answer_version,
                      reviewer_state = excluded.reviewer_state,
                      citations = excluded.citations,
                      source_run_id = excluded.source_run_id,
                      prompt_version = excluded.prompt_version,
                      answer_fit_status = excluded.answer_fit_status,
                      grounding_status = excluded.grounding_status,
                      grounding_reason = excluded.grounding_reason,
                      answer_scope_notes = excluded.answer_scope_notes
                    """
                ),
                {
                    **answer.model_dump(mode="json"),
                    "citations": json.dumps([c.model_dump(mode="json") for c in answer.citations]),
                },
            )

    def log_question_cache_match(self, result: QuestionCacheMatchResult) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into question_cache_match_logs (
                      course_id, claim_id, question_group_id, variation_id, canonical_answer_id,
                      incoming_question, normalized_question, match_method, match_score, resolved_as_hit
                    )
                    values (
                      :course_id, :claim_id, :question_group_id, :variation_id, :canonical_answer_id,
                      :incoming_question, :normalized_question, :match_method, :match_score, :resolved_as_hit
                    )
                    """
                ),
                result.model_dump(mode="json", exclude={"answer_markdown", "fallback_reason", "candidate_for_cache_warming"}),
            )

    def log_question_cache_fallback(self, result: QuestionCacheMatchResult) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into question_cache_fallback_logs (
                      course_id, claim_id, incoming_question, normalized_question, fallback_reason,
                      llm_response_id, response_markdown, candidate_for_cache_warming
                    )
                    values (
                      :course_id, :claim_id, :incoming_question, :normalized_question, :fallback_reason,
                      null, :response_markdown, :candidate_for_cache_warming
                    )
                    """
                ),
                {
                    "course_id": result.course_id,
                    "claim_id": result.claim_id,
                    "incoming_question": result.incoming_question,
                    "normalized_question": result.normalized_question,
                    "fallback_reason": result.fallback_reason or "unknown",
                    "response_markdown": result.answer_markdown,
                    "candidate_for_cache_warming": result.candidate_for_cache_warming,
                },
            )

    def log_question_cache_validation(self, log: QuestionCacheValidationLogOut) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into question_cache_validation_logs (
                      entity_type, entity_id, validator_type, decision, reason, model_version
                    )
                    values (
                      :entity_type, :entity_id, :validator_type, :decision, :reason, :model_version
                    )
                    """
                ),
                log.model_dump(mode="json"),
            )

    def upsert_claim_coverage_audit(self, audit: ClaimCoverageAuditOut) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    """
                    insert into claim_coverage_audit (
                      course_id, claim_id, produced_question_groups, question_group_count,
                      no_groups_reason, source_run_id
                    )
                    values (
                      :course_id, :claim_id, :produced_question_groups, :question_group_count,
                      :no_groups_reason, :source_run_id
                    )
                    on conflict (source_run_id, course_id, claim_id) do update set
                      produced_question_groups = excluded.produced_question_groups,
                      question_group_count = excluded.question_group_count,
                      no_groups_reason = excluded.no_groups_reason
                    """
                ),
                audit.model_dump(mode="json"),
            )
