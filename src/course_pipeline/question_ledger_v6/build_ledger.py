from __future__ import annotations

from course_pipeline.question_ledger_v6.models import AnchorSummary, LedgerRow


def build_ledger_rows(*args, **kwargs) -> list[LedgerRow]:
    raise NotImplementedError


def derive_views(rows: list[LedgerRow]) -> dict[str, list[LedgerRow]]:
    raise NotImplementedError


def build_anchor_summaries(rows: list[LedgerRow]) -> list[AnchorSummary]:
    raise NotImplementedError


def build_inspection_report(rows: list[LedgerRow], anchor_summaries: list[AnchorSummary]) -> str:
    raise NotImplementedError
