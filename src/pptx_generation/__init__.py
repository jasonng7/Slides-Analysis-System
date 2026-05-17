"""PowerPoint placeholder generation for Stage 7."""

from pptx_generation.placeholder_deck_generator import (
    generate_placeholder_deck_from_file,
    generate_placeholder_deck_from_recommendation,
    generate_placeholder_deck_from_text,
    normalize_recommendation_to_slide_plans,
)
from pptx_generation.editable_reference_deck_generator import (
    generate_editable_reference_deck_from_file,
    generate_editable_reference_deck_from_recommendation,
    generate_editable_reference_deck_from_text,
)
from pptx_generation.reference_deck_generator import (
    generate_reference_deck_from_file,
    generate_reference_deck_from_recommendation,
    generate_reference_deck_from_text,
)

__all__ = [
    "generate_placeholder_deck_from_file",
    "generate_placeholder_deck_from_recommendation",
    "generate_placeholder_deck_from_text",
    "generate_editable_reference_deck_from_file",
    "generate_editable_reference_deck_from_recommendation",
    "generate_editable_reference_deck_from_text",
    "generate_reference_deck_from_file",
    "generate_reference_deck_from_recommendation",
    "generate_reference_deck_from_text",
    "normalize_recommendation_to_slide_plans",
]
