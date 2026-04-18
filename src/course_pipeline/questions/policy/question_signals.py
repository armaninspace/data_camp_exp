from __future__ import annotations

import re


GENERIC_TEMPLATE_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "generic_course_matter",
        re.compile(r"^why does .+ matter in this course\?$"),
    ),
    (
        "generic_apply_here",
        re.compile(r"^how would i apply .+ to the kind of data used here\?$"),
    ),
    (
        "generic_fail_case",
        re.compile(r"^what would make .+ fail in a realistic case\?$"),
    ),
    (
        "generic_adapt_context",
        re.compile(r"^when would i need to adapt .+ instead of applying it the same way every time\?$"),
    ),
]

COURSE_CONTEXT_PHRASES = (
    "in this course",
    "used here",
    "the kind of data used here",
    "realistic case",
    "the same way every time",
)


def detect_question_signals(question_text: str) -> dict[str, object]:
    normalized = " ".join(question_text.lower().split())
    matched_template_codes = [
        code for code, pattern in GENERIC_TEMPLATE_RULES if pattern.match(normalized)
    ]
    has_course_context = any(phrase in normalized for phrase in COURSE_CONTEXT_PHRASES)
    return {
        "generic_template": bool(matched_template_codes),
        "generic_template_codes": matched_template_codes,
        "course_context_dependent": has_course_context,
    }
