from __future__ import annotations

import re

from course_pipeline.questions.candidates.models import CanonicalDocument, TopicNode
from course_pipeline.utils import slugify


PHRASE_PATTERNS: list[tuple[str, str]] = [
    (r"\bexponential smoothing\b", "concept"),
    (r"\bARIMA(?: models?)?\b", "concept"),
    (r"\bforecast accuracy\b", "metric"),
    (r"\bbenchmark methods?\b", "comparison_axis"),
    (r"\bwhite noise\b", "diagnostic"),
    (r"\bLjung-Box test\b", "diagnostic"),
    (r"\btrend\b", "concept"),
    (r"\bseasonality\b", "concept"),
    (r"\brepeated cycles\b", "concept"),
    (r"\bunivariate time series\b", "concept"),
    (r"\bmultivariate time series\b", "comparison_axis"),
    (r"\bxts\b", "tool"),
    (r"\bzoo\b", "tool"),
    (r"\bGDP per capita\b", "metric"),
    (r"\bunemployment\b", "metric"),
    (r"\bportfolio\b", "decision_point"),
    (r"\bmerging multiple xts objects\b", "procedure"),
    (r"\bisolating certain periods\b", "procedure"),
]


def _guess_topic_type(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    if any(term in text for term in ["compare", "different", "difference", "vs", "multivariate", "benchmark"]):
        return "comparison_axis"
    if any(term in text for term in ["measure", "accuracy", "gdp", "unemployment"]):
        return "metric"
    if any(term in text for term in ["test", "diagnose", "diagnostic", "white noise", "ljung-box"]):
        return "diagnostic"
    if any(term in text for term in ["choose", "select", "decide", "portfolio"]):
        return "decision_point"
    if any(term in text for term in ["merge", "isolate", "assemble", "visualize", "explore", "plot", "create"]):
        return "procedure"
    return "concept"


def extract_topics(doc: CanonicalDocument) -> list[TopicNode]:
    topics: list[TopicNode] = []
    seen: set[str] = set()
    for section in doc.sections:
        split_parts_created = 0
        parts = [part.strip() for part in re.split(r"\band\b", section.title, flags=re.IGNORECASE) if part.strip()]
        if len(parts) > 1:
            for part in parts:
                part_id = slugify(part)
                if (
                    len(part.split()) < 2
                    or not part_id
                    or part_id in seen
                    or part.lower().startswith(("exploring ", "visualizing ", "forecasting ", "analyzing "))
                ):
                    continue
                seen.add(part_id)
                split_parts_created += 1
                topics.append(
                    TopicNode(
                        topic_id=part_id,
                        label=part,
                        aliases=[],
                        topic_type=_guess_topic_type(part, section.summary),
                        description=section.summary or section.title,
                        source_section_ids=[section.section_index],
                        confidence=0.72,
                    )
                )
        base_label = section.title
        if section.title.lower().startswith("exploring and visualizing time series"):
            base_label = "time series visualization"
        elif section.title.lower().startswith("forecasting with arima"):
            base_label = "ARIMA models"
        base_type = _guess_topic_type(base_label, section.summary)
        base_id = slugify(base_label) or f"section-{section.section_index}"
        if base_id not in seen and split_parts_created < 2:
            seen.add(base_id)
            topics.append(
                TopicNode(
                    topic_id=base_id,
                    label=base_label,
                    aliases=[],
                    topic_type=base_type,
                    description=section.summary or section.title,
                    source_section_ids=[section.section_index],
                    confidence=0.82 if section.source == "explicit" else 0.68,
                )
            )
        text = f"{section.title}. {section.summary}"
        for pattern, topic_type in PHRASE_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                label = match.group(0)
                topic_id = slugify(label)
                if not topic_id or topic_id in seen:
                    continue
                seen.add(topic_id)
                topics.append(
                    TopicNode(
                        topic_id=topic_id,
                        label=label,
                        aliases=[],
                        topic_type=topic_type,  # type: ignore[arg-type]
                        description=section.summary or section.title,
                        source_section_ids=[section.section_index],
                        confidence=0.78,
                    )
                )
    if doc.overview and doc.sections:
        anchor_section = doc.sections[0].section_index
        for pattern, topic_type in PHRASE_PATTERNS:
            for match in re.finditer(pattern, doc.overview, flags=re.IGNORECASE):
                label = match.group(0)
                topic_id = slugify(label)
                if not topic_id or topic_id in seen:
                    continue
                seen.add(topic_id)
                topics.append(
                    TopicNode(
                        topic_id=topic_id,
                        label=label,
                        aliases=[],
                        topic_type=topic_type,  # type: ignore[arg-type]
                        description=doc.overview,
                        source_section_ids=[anchor_section],
                        confidence=0.74,
                    )
                )
    return topics
