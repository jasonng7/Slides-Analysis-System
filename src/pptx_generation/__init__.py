"""PowerPoint placeholder generation for Stage 7."""

from pptx_generation.placeholder_deck_generator import (
    generate_placeholder_deck_from_file,
    generate_placeholder_deck_from_recommendation,
    generate_placeholder_deck_from_text,
    normalize_recommendation_to_slide_plans,
)

__all__ = [
    "generate_placeholder_deck_from_file",
    "generate_placeholder_deck_from_recommendation",
    "generate_placeholder_deck_from_text",
    "normalize_recommendation_to_slide_plans",
]
