from __future__ import annotations


def generate_prompt_from_recommendation(recommendation: dict) -> str:
    mode = recommendation.get("recommended_output_mode", "auto")
    if mode == "deck":
        return _deck_prompt(recommendation)
    return _slide_prompt(recommendation)


def _slide_prompt(recommendation: dict) -> str:
    slide = recommendation.get("recommended_slide_structure", {})
    return "\n".join(
        [
            "Create a board-ready consulting-style slide using the structure below.",
            "",
            f"Content diagnosis: {recommendation.get('content_diagnosis', '')}",
            f"Audience: {recommendation.get('recommended_audience_type', 'unknown')}",
            f"Recommended slide type: {slide.get('recommended_slide_type', '')}",
            f"Recommended storyline: {recommendation.get('recommended_storyline', '')}",
            f"Suggested action title: {slide.get('suggested_action_title', '')}",
            "",
            f"Layout instruction: {slide.get('layout_instruction', '')}",
            "",
            "Content blocks:",
            _bullets(slide.get("content_blocks", [])),
            "",
            "Data required:",
            _bullets(slide.get("data_required", [])),
            "",
            "Analysis required:",
            _bullets(slide.get("analysis_required", [])),
            "",
            "Missing data / research gaps:",
            _bullets(slide.get("missing_data_or_research_gaps", [])),
            "",
            "Design guidance:",
            slide.get("powerpoint_template_instruction", ""),
            "",
            "Quality checklist:",
            _bullets(slide.get("quality_checklist", [])),
        ]
    ).strip()


def _deck_prompt(recommendation: dict) -> str:
    deck = recommendation.get("recommended_deck_structure", {})
    lines = [
        "Create a board-ready consulting-style deck using the outline below.",
        "",
        f"Suggested deck title: {deck.get('suggested_deck_title', '')}",
        f"Audience: {recommendation.get('recommended_audience_type', 'unknown')}",
        f"Recommended storyline: {recommendation.get('recommended_storyline', '')}",
        f"Content diagnosis: {recommendation.get('content_diagnosis', '')}",
        "",
        "Deck outline:",
    ]

    for section in deck.get("sections", []):
        lines.append(f"\nSection: {section.get('section_name', '')}")
        lines.append(f"Purpose: {section.get('section_purpose', '')}")
        for slide in section.get("recommended_slides", []):
            lines.extend(
                [
                    f"- Slide: {slide.get('slide_title', '')}",
                    f"  Type: {slide.get('slide_type', '')}",
                    f"  Chart: {slide.get('chart_type', '')}",
                    f"  Storyline: {slide.get('storyline_type', '')}",
                    f"  Source content to use: {slide.get('content_to_use_from_source', '')}",
                    f"  Additional data needed: {slide.get('additional_data_needed', '')}",
                    f"  Template instruction: {slide.get('template_instruction', '')}",
                ]
            )

    slide = recommendation.get("recommended_slide_structure", {})
    lines.extend(["", "Quality checklist:", _bullets(slide.get("quality_checklist", []))])
    return "\n".join(lines).strip()


def _bullets(items: object) -> str:
    if not isinstance(items, list) or not items:
        return "- Not specified"
    return "\n".join(f"- {item}" for item in items)
