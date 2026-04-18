from __future__ import annotations

import re


_ACRONYM_WITH_MODELS = re.compile(r"^(?P<acro>[A-Z]{2,})(?:\s+models?)?$")
_ARTICLED_LABELS = {
    "ljung-box test": "What is the Ljung-Box test?",
}
_SINGULAR_PHRASES = {
    "forecast accuracy",
    "white noise",
    "exponential smoothing",
    "seasonality",
    "trend",
    "univariate time series",
    "multivariate time series",
}
_INDEFINITE_ARTICLE_PHRASES = {
    "univariate time series",
    "multivariate time series",
}


def anchor_entry_label(label: str) -> str:
    stripped = " ".join(label.split())
    match = _ACRONYM_WITH_MODELS.fullmatch(stripped)
    if match:
        return match.group("acro")
    return stripped


def acronym_companion_question(label: str) -> str | None:
    match = _ACRONYM_WITH_MODELS.fullmatch(" ".join(label.split()))
    if not match:
        return None
    return f"What does {match.group('acro')} stand for?"


def plain_definition_question(label: str) -> str:
    base = anchor_entry_label(label)
    lowered = base.lower()
    if lowered in _ARTICLED_LABELS:
        return _ARTICLED_LABELS[lowered]
    if lowered in _INDEFINITE_ARTICLE_PHRASES:
        return f"What is a {lowered}?"
    if _is_plural_phrase(base):
        return f"What are {lowered}?"
    if _is_acronym(base):
        return f"What is {base}?"
    return f"What is {lowered}?"


def is_plain_definition_question(label: str, question_text: str) -> bool:
    return _normalize(question_text) == _normalize(plain_definition_question(label))


def _is_acronym(label: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{2,}", label))


def _is_plural_phrase(label: str) -> bool:
    lowered = label.lower()
    if lowered in _SINGULAR_PHRASES:
        return False
    if lowered.endswith("series"):
        return False
    last_word = lowered.split()[-1]
    return last_word in {"methods", "cycles"} or (last_word.endswith("s") and last_word not in {"analysis"})


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())
