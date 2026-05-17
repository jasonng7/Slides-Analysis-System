from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pptx_generation.placeholder_deck_generator import (
    _extract_patterns,
    load_recommendation_json,
    normalize_recommendation_to_slide_plans,
)
from quality_control.deck_qa_models import (
    ScoreBreakdown,
    add_recommendation_once,
    clamp_category_score,
    find_duplicate_titles,
    find_near_duplicate_titles,
    issue,
    now_iso,
    rating_for_score,
    repeated_template_usage,
    word_count,
)


GENERIC_TITLE_TERMS = {
    "overview",
    "summary",
    "introduction",
    "market overview",
    "competitor landscape",
    "financial analysis",
    "risk assessment",
    "next steps",
}


def review_recommendation(recommendation_path: str | Path) -> dict[str, Any]:
    path = Path(recommendation_path)
    recommendation = load_recommendation_json(path)
    slide_plans = normalize_recommendation_to_slide_plans(recommendation)
    patterns = _extract_patterns(recommendation)
    issues: list[dict[str, Any]] = []
    recommendations: list[str] = []
    slide_level_findings: list[dict[str, Any]] = []

    if not slide_plans:
        issues.append(
            issue(
                "critical",
                "structure",
                "No recommendation slides found.",
                "Regenerate the recommendation before generating a deck.",
            )
        )

    mode = str(recommendation.get("recommended_output_mode") or recommendation.get("requested_mode") or "auto")
    slide_count = len(slide_plans)
    _check_deck_length(mode, slide_count, recommendation, issues, recommendations)
    _check_titles(slide_plans, issues, recommendations, slide_level_findings)
    _check_slide_type_distribution(slide_plans, issues, recommendations)
    _check_template_matching(slide_plans, patterns, recommendation, issues, recommendations)

    score_breakdown = _score_recommendation(slide_plans, patterns, recommendation, issues)
    overall_score = score_breakdown.total

    return {
        "qa_type": "recommendation",
        "reviewed_path": str(path),
        "generated_at": now_iso(),
        "overall_score": overall_score,
        "rating": rating_for_score(overall_score),
        "score_breakdown": score_breakdown.as_dict(),
        "summary": {
            "recommended_mode": mode,
            "recommended_slide_count": slide_count,
            "slide_types": dict(Counter(plan.get("slide_type", "other") for plan in slide_plans)),
            "matching_method": recommendation.get("matching_method", "metadata_match"),
            "matched_template_count": len(patterns),
            "duplicate_title_count": len(find_duplicate_titles([plan.get("slide_title", "") for plan in slide_plans])),
            "near_duplicate_title_count": len(find_near_duplicate_titles([plan.get("slide_title", "") for plan in slide_plans])),
        },
        "issues": issues,
        "recommendations": recommendations,
        "slide_level_findings": slide_level_findings,
    }


def _check_deck_length(
    mode: str,
    slide_count: int,
    recommendation: dict[str, Any],
    issues: list[dict[str, Any]],
    recommendations: list[str],
) -> None:
    title = str(recommendation.get("recommended_slide_or_deck_title") or "").lower()
    is_board_or_strategy = "board" in title or "strategy" in title or "recommendation" in title
    if mode == "slide" and slide_count > 3:
        issues.append(
            issue(
                "high",
                "structure",
                f"Slide-mode recommendation contains {slide_count} slides.",
                "Condense to 1–3 slides or switch mode to deck.",
            )
        )
    if mode == "deck":
        if slide_count > 25:
            issues.append(
                issue(
                    "high",
                    "structure",
                    f"Deck recommendation contains {slide_count} content slides.",
                    "Condense the core storyline and move backup detail to appendix.",
                )
            )
        elif slide_count > 20:
            issues.append(
                issue(
                    "medium" if is_board_or_strategy else "high",
                    "structure",
                    f"Deck recommendation contains {slide_count} content slides, which may be too long for a board-ready first draft.",
                    "Condense to 10–15 core slides plus appendix.",
                )
            )
            add_recommendation_once(
                recommendations,
                "Condense the main deck to 10–15 core slides and move supporting pages to appendix.",
            )


def _check_titles(
    slide_plans: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    recommendations: list[str],
    slide_level_findings: list[dict[str, Any]],
) -> None:
    titles = [str(plan.get("slide_title") or "").strip() for plan in slide_plans]
    for index, title in enumerate(titles, start=1):
        count = word_count(title)
        finding = {
            "slide_number": index,
            "slide_title": title,
            "word_count": count,
            "slide_type": slide_plans[index - 1].get("slide_type"),
        }
        if count > 25:
            issues.append(
                issue(
                    "high",
                    "slide_quality",
                    f"Slide title is very long ({count} words).",
                    "Rewrite as a shorter action title.",
                    slide_number=index,
                )
            )
            finding["issue"] = "very_long_title"
        elif count > 18:
            issues.append(
                issue(
                    "medium",
                    "slide_quality",
                    f"Slide title is long ({count} words).",
                    "Tighten the action title to under 18 words.",
                    slide_number=index,
                )
            )
            finding["issue"] = "long_title"
        if title.lower() in GENERIC_TITLE_TERMS:
            issues.append(
                issue(
                    "medium",
                    "slide_quality",
                    f"Slide title is generic: '{title}'.",
                    "Use an insight-led title rather than a topic label.",
                    slide_number=index,
                )
            )
            finding["issue"] = "generic_title"
        slide_level_findings.append(finding)

    duplicates = find_duplicate_titles(titles)
    if duplicates:
        issues.append(
            issue(
                "medium",
                "slide_quality",
                f"{len(duplicates)} duplicate slide title occurrence(s) detected.",
                "Merge duplicate slides or rewrite titles to make each role distinct.",
            )
        )
        add_recommendation_once(recommendations, "Remove duplicate slide titles or combine repetitive slides.")

    near_duplicates = find_near_duplicate_titles(titles)
    if near_duplicates:
        issues.append(
            issue(
                "medium",
                "slide_quality",
                f"{len(near_duplicates)} near-duplicate slide title pair(s) detected.",
                "Review sequence for repetitive messages.",
            )
        )


def _check_slide_type_distribution(
    slide_plans: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    recommendations: list[str],
) -> None:
    counts = Counter(plan.get("slide_type") or "other" for plan in slide_plans)
    if counts.get("other", 0) > max(2, len(slide_plans) * 0.25):
        issues.append(
            issue(
                "medium",
                "structure",
                "Many slides have slide_type='other'.",
                "Refine the recommendation or classifier output so slide structures are more specific.",
            )
        )
    if len(counts) <= 2 and len(slide_plans) >= 8:
        issues.append(
            issue(
                "low",
                "structure",
                "Slide type distribution is narrow.",
                "Check whether the deck needs more varied evidence pages, options analysis, risks, or implementation slides.",
            )
        )
        add_recommendation_once(recommendations, "Review slide type mix for storyline variety and evidence coverage.")


def _check_template_matching(
    slide_plans: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    recommendation: dict[str, Any],
    issues: list[dict[str, Any]],
    recommendations: list[str],
) -> None:
    matching_method = recommendation.get("matching_method", "metadata_match")
    if matching_method == "vector_search":
        issues.append(
            issue(
                "info",
                "template_matching",
                "vector_search used successfully for slide pattern matching.",
                "Keep using embeddings for semantic template retrieval.",
            )
        )
    else:
        issues.append(
            issue(
                "low",
                "template_matching",
                f"Matching method is {matching_method}; vector_search was not detected.",
                "Ensure embeddings are available when semantic matching is desired.",
            )
        )

    if not patterns and not any(plan.get("matched_template") for plan in slide_plans):
        issues.append(
            issue(
                "high",
                "template_matching",
                "No matched template patterns found.",
                "Embed/classify template slides or rerun recommendation with slide library available.",
            )
        )

    references = [plan.get("matched_template") or {} for plan in slide_plans]
    for (deck_name, slide_number), count in repeated_template_usage(references):
        if count > 6:
            severity = "high"
        elif count > 3:
            severity = "medium"
        else:
            continue
        issues.append(
            issue(
                severity,
                "template_matching",
                f"Matched source slide reused {count} times: {deck_name} slide {slide_number}.",
                "Diversify template matches or split repeated pages into appendix/supporting content.",
            )
        )
        add_recommendation_once(recommendations, "Diversify matched templates so the generated deck does not overuse one source slide.")

    for index, plan in enumerate(slide_plans, start=1):
        matched = plan.get("matched_template") or {}
        score = matched.get("similarity_score") or matched.get("match_score")
        if score is None:
            issues.append(
                issue(
                    "low",
                    "template_matching",
                    "Matched template is missing similarity score.",
                    "Keep similarity scores in metadata to help QA match quality.",
                    slide_number=index,
                )
            )
            continue
        try:
            score_float = float(score)
        except (TypeError, ValueError):
            continue
        if score_float < 0.35:
            issues.append(
                issue(
                    "high",
                    "template_matching",
                    f"Low template similarity score: {score_float:.2f}.",
                    "Review or manually choose a better template pattern.",
                    slide_number=index,
                )
            )
        elif score_float < 0.45:
            issues.append(
                issue(
                    "medium",
                    "template_matching",
                    f"Template similarity score is weak: {score_float:.2f}.",
                    "Review whether the matched template is structurally relevant.",
                    slide_number=index,
                )
            )


def _score_recommendation(
    slide_plans: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    recommendation: dict[str, Any],
    issues: list[dict[str, Any]],
) -> ScoreBreakdown:
    structure_penalty = sum(1 for item in issues if item.get("category") == "structure") * 4
    slide_penalty = sum(1 for item in issues if item.get("category") == "slide_quality") * 2
    match_penalty = sum(1 for item in issues if item.get("category") == "template_matching" and item.get("severity") != "info") * 3
    generation_penalty = 0
    if not slide_plans:
        structure_penalty += 25
    if not patterns:
        match_penalty += 8
    if recommendation.get("matching_method") != "vector_search":
        match_penalty += 2
    return ScoreBreakdown(
        structure_quality=clamp_category_score(25 - structure_penalty),
        slide_quality=clamp_category_score(25 - slide_penalty),
        template_matching_quality=clamp_category_score(25 - match_penalty),
        generation_quality=clamp_category_score(25 - generation_penalty),
    )
