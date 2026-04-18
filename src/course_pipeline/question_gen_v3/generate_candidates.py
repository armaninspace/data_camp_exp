from __future__ import annotations

from course_pipeline.question_gen_v3.models import (
    CanonicalDocument,
    FrictionPoint,
    PedagogicalProfile,
    QuestionCandidate,
    TopicEdge,
    TopicNode,
)
from course_pipeline.utils import slugify


def _candidate(
    topic: TopicNode,
    slot: str,
    mastery_band: str,
    question_type: str,
    question_text: str,
    rationale: str,
    source_support: list[str],
    linked_friction_ids: list[str],
) -> QuestionCandidate:
    return QuestionCandidate(
        candidate_id=slugify(f"{topic.topic_id}-{slot}-{question_text}")[:120],
        topic_id=topic.topic_id,
        slot=slot,  # type: ignore[arg-type]
        mastery_band=mastery_band,  # type: ignore[arg-type]
        question_type=question_type,  # type: ignore[arg-type]
        question_text=question_text,
        rationale=rationale,
        source_support=source_support,
        linked_friction_ids=linked_friction_ids,
        section_ids=topic.source_section_ids,
    )


def generate_candidates(
    doc: CanonicalDocument,
    topics: list[TopicNode],
    edges: list[TopicEdge],
    pedagogy: list[PedagogicalProfile],
    frictions: list[FrictionPoint],
    config: dict,
) -> list[QuestionCandidate]:
    edge_map: dict[str, list[TopicEdge]] = {}
    for edge in edges:
        edge_map.setdefault(edge.source_id, []).append(edge)
        edge_map.setdefault(edge.target_id, []).append(edge)
    frictions_by_topic: dict[str, list[FrictionPoint]] = {}
    for friction in frictions:
        frictions_by_topic.setdefault(friction.topic_id, []).append(friction)
    profiles = {profile.topic_id: profile for profile in pedagogy}

    candidates: list[QuestionCandidate] = []
    for topic in topics:
        label = topic.label
        lower = label.lower()
        support = [topic.description]
        linked = [friction.friction_id for friction in frictions_by_topic.get(topic.topic_id, [])]
        profile = profiles.get(topic.topic_id)

        custom_emitted = False
        if "benchmark methods" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", "What is a benchmark forecasting method?", "Definition question for a core forecasting baseline.", support, linked),
                    _candidate(topic, "developing_comparison", "developing", "comparison", "Why do we compare a forecasting model against benchmark methods?", "Comparison and evaluation question tied to model assessment.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "How do I know when a benchmark method is no longer enough on its own?", "Diagnostic question about adequacy and escalation.", support, linked),
                ]
            )
        elif "forecast accuracy" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", "What is forecast accuracy?", "Definition question for the evaluation concept.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", "How do I measure forecast accuracy?", "Procedural question tied to evaluation steps.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "What does forecast accuracy tell me about whether I should trust a forecasting method?", "Diagnostic interpretation question.", support, linked),
                ]
            )
        elif "exponential smoothing" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", "What is exponential smoothing?", "Core method definition.", support, linked),
                    _candidate(topic, "developing_misconception", "developing", "misconception", "Why do more recent observations get more weight in exponential smoothing?", "Conceptual misconception question around weighting.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "When is exponential smoothing a poor fit for the data?", "Diagnostic adequacy question for method choice.", support, linked),
                ]
            )
        elif "arima" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", "What does ARIMA stand for, and what is it trying to model?", "Definition with orientation to the model family.", support, linked),
                    _candidate(topic, "developing_comparison", "developing", "comparison", "How is ARIMA different from exponential smoothing?", "Comparison question tied to the explicit course contrast.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "When would ARIMA be a better choice than exponential smoothing?", "Method choice diagnostic question.", support, linked),
                ]
            )
        elif "ljung-box test" in lower or "white noise" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", f"What is {lower}?", "Definition of a diagnostic concept.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", f"How do I use {lower} to check whether a series looks random?", "Procedural diagnostic question.", support, linked),
                    _candidate(topic, "proficient_interpretation" if False else "proficient_diagnostic", "proficient", "diagnostic", f"What would {lower} tell me about whether I should keep using my current forecasting approach?", "Interpretive diagnostic question.", support, linked),
                ]
            )
        elif "univariate time series" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", "What is a univariate time series?", "Definition of the single-series case.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", "What can a univariate time series plot tell me about distribution, central tendency, and spread?", "Interpretive procedure question grounded in the section summary.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "How would I know when a univariate view is not enough for the question I want to answer?", "Diagnostic question about the limits of a single-series view.", support, linked),
                ]
            )
        elif "multivariate time series" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "developing_comparison", "developing", "comparison", "What is the difference between a univariate and a multivariate time series?", "Comparison question anchored in the section contrast.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", "What patterns should I look for when comparing multiple time series?", "Comparative procedure question.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "How would I know that I am missing an important relationship by only looking at one series at a time?", "Diagnostic comparison question.", support, linked),
                ]
            )
        elif "portfolio" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "developing_procedural", "developing", "procedure", "How do I decide whether a candidate stock improves my existing portfolio?", "Decision question grounded in the case study.", support, linked),
                    _candidate(topic, "developing_misconception", "developing", "misconception", "Why is looking at one stock by itself not enough in the portfolio case study?", "Misconception question about isolated analysis.", support, linked),
                    _candidate(topic, "proficient_transfer", "proficient", "transfer", "What would count as evidence that a stock complements my current portfolio rather than just looking strong on its own?", "Transfer question about applying the case-study reasoning to a decision.", support, linked),
                ]
            )
        elif lower == "xts" or lower == "zoo":
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_definition", "novice", "definition", f"What is {label} used for in this course?", "Tool-orientation question.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", f"When would I reach for {label} while working with these time series datasets?", "Procedural-use question.", support, linked),
                    _candidate(topic, "proficient_transfer", "proficient", "transfer", f"How would my use of {label} change with a different time series dataset?", "Transfer question for tool use across datasets.", support, linked),
                ]
            )
        elif "merging multiple xts objects" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "developing_procedural", "developing", "procedure", "How do I know when I need to merge multiple xts objects before analysis?", "Procedural sequencing question.", support, linked),
                    _candidate(topic, "developing_misconception", "developing", "misconception", "Why would it be a mistake to analyze the weather data before merging the relevant xts objects?", "Misconception question about preparation order.", support, linked),
                    _candidate(topic, "proficient_transfer", "proficient", "transfer", "How would this merging step change with a different time series dataset?", "Transfer question for data preparation.", support, linked),
                ]
            )
        elif "isolating certain periods" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "developing_procedural", "developing", "procedure", "Why would I isolate a specific period before analyzing time series data?", "Procedural scoping question.", support, linked),
                    _candidate(topic, "developing_misconception", "developing", "misconception", "What could go wrong if I analyze the full time range when I really need a specific period?", "Misconception question about analysis scope.", support, linked),
                    _candidate(topic, "proficient_transfer", "proficient", "transfer", "How would I decide which period to isolate in a new dataset?", "Transfer question for scope decisions.", support, linked),
                ]
            )
        elif "gdp per capita" in lower or "unemployment" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "developing_comparison", "developing", "comparison", "How could GDP per capita and unemployment affect tourism differently?", "Comparison question for economic indicators.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "What would make me doubt a tourism explanation based on only one economic indicator?", "Diagnostic interpretation question.", support, linked),
                ]
            )
        elif "time series visualization" in lower or "time series plots" in lower:
            custom_emitted = True
            candidates.extend(
                [
                    _candidate(topic, "novice_orientation", "novice", "orientation", "Why is plotting a time series the first step in analysis?", "Orientation question for the plotting-first workflow.", support, linked),
                    _candidate(topic, "developing_procedural", "developing", "procedure", "What should I look for in a time series plot before choosing a forecasting method?", "Procedural question about extracting signals from plots.", support, linked),
                    _candidate(topic, "proficient_diagnostic", "proficient", "diagnostic", "How do I know when a time series plot is revealing something my forecasting method needs to capture?", "Diagnostic question about connecting visualization to modeling.", support, linked),
                ]
            )

        if custom_emitted:
            continue

        # novice orientation
        candidates.append(
            _candidate(
                topic,
                "novice_orientation",
                "novice",
                "orientation",
                f"Why does {lower} matter in this course?",
                "Orientation question tied to the topic's role in the section.",
                support,
                linked,
            )
        )

        # novice definition
        if lower.isupper() and len(lower) <= 6:
            q = f"What does {label} stand for?"
        else:
            q = f"What is {lower}?"
        candidates.append(
            _candidate(
                topic,
                "novice_definition",
                "novice",
                "definition",
                q,
                "Definition question for initial orientation.",
                support,
                linked,
            )
        )

        # developing procedural
        if topic.topic_type in {"procedure", "tool", "diagnostic"}:
            q = f"How do I use {lower} in this course context?"
        elif any(term in lower for term in ["accuracy", "test", "portfolio"]):
            q = f"How do I use {lower} to make a decision?"
        else:
            q = f"How would I apply {lower} to the kind of data used here?"
        candidates.append(
            _candidate(
                topic,
                "developing_procedural",
                "developing",
                "procedure",
                q,
                "Application question for moving beyond recognition.",
                support,
                linked,
            )
        )

        # developing comparison
        contrast_edge = next((edge for edge in edge_map.get(topic.topic_id, []) if edge.relation in {"contrasts_with", "confused_with"}), None)
        if contrast_edge:
            other_id = contrast_edge.target_id if contrast_edge.source_id == topic.topic_id else contrast_edge.source_id
            other = next((item for item in topics if item.topic_id == other_id), None)
            if other:
                candidates.append(
                    _candidate(
                        topic,
                        "developing_comparison",
                        "developing",
                        "comparison",
                        f"How is {lower} different from {other.label.lower()}?",
                        "Comparison question driven by an extracted contrast or confusion edge.",
                        support,
                        linked,
                    )
                )
        elif topic.topic_type == "comparison_axis":
            candidates.append(
                _candidate(
                    topic,
                    "developing_comparison",
                    "developing",
                    "comparison",
                    f"What should I compare when I use {lower}?",
                    "Comparison question derived from a comparison-axis topic.",
                    support,
                    linked,
                )
            )

        # developing misconception
        misconception_text = profile.likely_misconceptions[0] if profile and profile.likely_misconceptions else None
        if misconception_text:
            q = f"What is a common mistake people make with {lower}?"
        elif topic.topic_type in {"metric", "diagnostic", "comparison_axis"}:
            q = f"What could I misunderstand about {lower} if I only memorize the term?"
        else:
            q = f"Why isn't {lower} enough on its own?"
        candidates.append(
            _candidate(
                topic,
                "developing_misconception",
                "developing",
                "misconception",
                q,
                "Misconception question tied to likely learner confusion or shallow use.",
                support,
                linked,
            )
        )

        # proficient diagnostic
        if any(friction.friction_type in {"choice", "interpretation_gap", "failure_mode"} for friction in frictions_by_topic.get(topic.topic_id, [])):
            q = f"How would I know when {lower} is not enough or not the right choice?"
        elif topic.topic_type in {"metric", "diagnostic"}:
            q = f"What would {lower} tell me about whether my approach is working?"
        else:
            q = f"What would make {lower} fail in a realistic case?"
        candidates.append(
            _candidate(
                topic,
                "proficient_diagnostic",
                "proficient",
                "diagnostic",
                q,
                "Diagnostic question aimed at failure detection, adequacy, or method choice.",
                support,
                linked,
            )
        )

        # proficient transfer
        if topic.topic_type == "decision_point":
            q = f"How would I transfer {lower} to a new but related situation?"
        elif any(term in lower for term in ["seasonality", "weather", "economic", "sports", "portfolio"]):
            q = f"How would my use of {lower} change in a different real-world context?"
        else:
            q = f"When would I need to adapt {lower} instead of applying it the same way every time?"
        candidates.append(
            _candidate(
                topic,
                "proficient_transfer",
                "proficient",
                "transfer",
                q,
                "Transfer question for adapting the idea to a new context.",
                support,
                linked,
            )
        )

    return candidates
