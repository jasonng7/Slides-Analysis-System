from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from config import PROJECT_ROOT
from database.db import get_connection
from database.schema import initialize_database
from pptx_generation.reference_slide_resolver import resolve_reference_slide_image


class SlideCloneError(RuntimeError):
    pass


def resolve_reference_slide_source(matched_template: dict[str, Any]) -> dict[str, Any]:
    deck_name = str(matched_template.get("deck_name") or "").strip()
    slide_number = _safe_int(matched_template.get("slide_number"))
    if not deck_name or slide_number is None:
        return {
            "found": False,
            "warning": "Matched template is missing deck_name or slide_number.",
        }

    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
              d.deck_name,
              d.source_file,
              d.source_type,
              s.slide_number,
              s.slide_title,
              s.slide_image_path
            FROM slides s
            JOIN decks d ON d.id = s.deck_id
            WHERE LOWER(d.deck_name) = LOWER(?) AND s.slide_number = ?
            LIMIT 1
            """,
            (deck_name, slide_number),
        ).fetchone()

    if not row:
        return {
            "found": False,
            "warning": f"Could not find source slide for {deck_name} slide {slide_number}.",
        }

    item = dict(row)
    source_path = _resolve_path(item.get("source_file"))
    if not source_path or not source_path.exists() or source_path.suffix.lower() != ".pptx":
        return {
            "found": False,
            **item,
            "warning": f"Source PPTX is unavailable for {deck_name} slide {slide_number}.",
        }

    item["source_file"] = str(source_path)
    item["found"] = True
    return item


def clone_reference_slide_into(
    target_prs,
    slide_plan: dict[str, Any],
    presentation_cache: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    from pptx import Presentation

    matched = slide_plan.get("matched_template") or {}
    reference = resolve_reference_slide_source(matched)
    if not reference.get("found"):
        raise SlideCloneError(str(reference.get("warning") or "Reference source slide not found."))

    source_file = str(reference["source_file"])
    cache = presentation_cache if presentation_cache is not None else {}
    source_prs = cache.get(source_file)
    if source_prs is None:
        source_prs = Presentation(source_file)
        cache[source_file] = source_prs

    slide_number = int(reference["slide_number"])
    if slide_number < 1 or slide_number > len(source_prs.slides):
        raise SlideCloneError(f"Slide {slide_number} is outside source deck range.")

    source_slide = source_prs.slides[slide_number - 1]
    target_slide = target_prs.slides.add_slide(target_prs.slide_layouts[6])
    _clear_slide(target_slide)
    _clone_slide_xml(source_slide, target_slide)
    _replace_title_text(target_slide, slide_plan)
    _add_editable_content_panel(target_slide, slide_plan)
    _add_clone_footer(target_slide, slide_plan, reference)
    return target_slide, reference


def add_image_fallback_slide(target_prs, slide_plan: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    from pptx_generation.reference_deck_generator import _add_reference_content_slide

    reference = resolve_reference_slide_image(slide_plan.get("matched_template") or {})
    _add_reference_content_slide(target_prs, slide_plan, int(slide_plan.get("slide_number") or 1), reference)
    return target_prs.slides[-1], reference


def _clone_slide_xml(source_slide, target_slide) -> None:
    rel_map = _copy_relationships(source_slide, target_slide)
    target_tree = target_slide.shapes._spTree

    # Copy the source slide background element when present. This preserves
    # simple theme/background fills while avoiding slide-master mutation.
    source_bg = getattr(source_slide.element.cSld, "bg", None)
    if source_bg is not None:
        target_bg = getattr(target_slide.element.cSld, "bg", None)
        if target_bg is not None:
            target_slide.element.cSld.remove(target_bg)
        target_slide.element.cSld.insert(0, deepcopy(source_bg))

    for shape in source_slide.shapes:
        element = deepcopy(shape.element)
        _remap_relationship_ids(element, rel_map)
        target_tree.insert_element_before(element, "p:extLst")


def _copy_relationships(source_slide, target_slide) -> dict[str, str]:
    rel_map: dict[str, str] = {}
    for old_rid, rel in source_slide.part.rels.items():
        if rel.reltype.endswith("/notesSlide") or rel.reltype.endswith("/slideLayout"):
            continue
        try:
            target = rel.target_ref if rel.is_external else rel.target_part
            new_rid = target_slide.part.relate_to(target, rel.reltype, rel.is_external)
            rel_map[old_rid] = new_rid
        except Exception as exc:
            raise SlideCloneError(f"Could not copy slide relationship {old_rid}: {exc}") from exc
    return rel_map


def _remap_relationship_ids(element, rel_map: dict[str, str]) -> None:
    if not rel_map:
        return
    for node in element.iter():
        for attr_name, attr_value in list(node.attrib.items()):
            if attr_value in rel_map:
                node.attrib[attr_name] = rel_map[attr_value]


def _replace_title_text(slide, slide_plan: dict[str, Any]) -> None:
    title = str(slide_plan.get("slide_title") or "").strip()
    if not title:
        return
    text_shapes = [
        shape
        for shape in slide.shapes
        if getattr(shape, "has_text_frame", False) and (shape.text or "").strip()
    ]
    if not text_shapes:
        _add_textbox(slide, 0.55, 0.25, 11.8, 0.65, title, 15, bold=True)
        return

    def score(shape) -> tuple[int, int, int]:
        top_score = 1 if shape.top < Inches(1.6) else 0
        width_score = 1 if shape.width > Inches(5.0) else 0
        area = int(shape.width * shape.height)
        return (top_score, width_score, area)

    title_shape = sorted(text_shapes, key=score, reverse=True)[0]
    text_frame = title_shape.text_frame
    _set_text_frame(text_frame, title, font_size=15, bold=True)


def _add_editable_content_panel(slide, slide_plan: dict[str, Any]) -> None:
    content = _panel_content(slide_plan)
    _add_box(slide, 8.62, 1.05, 3.62, 3.45, content, font_size=7, fill=RGBColor(255, 255, 255))
    notes = str(slide_plan.get("slide_objective") or slide_plan.get("storyline") or "")
    if notes:
        _add_box(
            slide,
            0.68,
            5.98,
            11.58,
            0.72,
            f"Editable build note: {notes[:300]}",
            font_size=6,
            fill=RGBColor(246, 248, 251),
        )


def _add_clone_footer(slide, slide_plan: dict[str, Any], reference: dict[str, Any]) -> None:
    footer = (
        f"Editable cloned reference: {reference.get('deck_name')} slide {reference.get('slide_number')} "
        f"| {slide_plan.get('slide_type', 'other')} | {slide_plan.get('matching_method', 'metadata_match')}"
    )
    _add_textbox(slide, 0.55, 7.05, 12.1, 0.22, footer, 6, color=RGBColor(88, 98, 110))


def _panel_content(slide_plan: dict[str, Any]) -> str:
    lines = [
        "Editable replacement content",
        f"Type: {slide_plan.get('slide_type', 'other')}",
        f"Chart: {slide_plan.get('chart_type', 'unknown')}",
    ]
    suggested = slide_plan.get("suggested_content")
    if isinstance(suggested, list) and suggested:
        lines.extend(["", *[f"- {item}" for item in suggested[:6]]])
    elif isinstance(suggested, str) and suggested.strip():
        lines.extend(["", suggested])
    else:
        lines.extend(["", "- Replace copied text/visuals with source-backed content."])
    return "\n".join(str(line) for line in lines)


def _clear_slide(slide) -> None:
    for shape in list(slide.shapes):
        shape.element.getparent().remove(shape.element)


def _add_box(slide, x: float, y: float, w: float, h: float, text: str, *, font_size: int, fill: RGBColor):
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = RGBColor(178, 188, 199)
    shape.line.width = Pt(0.5)
    _set_text_frame(shape.text_frame, text, font_size=font_size)
    return shape


def _add_textbox(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    font_size: int,
    *,
    color: RGBColor = RGBColor(24, 31, 42),
    bold: bool = False,
) -> None:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    _set_text_frame(shape.text_frame, text, font_size=font_size, color=color, bold=bold)


def _set_text_frame(
    text_frame,
    text: str,
    *,
    font_size: int,
    color: RGBColor = RGBColor(24, 31, 42),
    bold: bool = False,
) -> None:
    text_frame.clear()
    text_frame.word_wrap = True
    text_frame.margin_left = Inches(0.08)
    text_frame.margin_right = Inches(0.08)
    text_frame.margin_top = Inches(0.04)
    text_frame.margin_bottom = Inches(0.04)
    for index, line in enumerate(str(text).splitlines() or [""]):
        paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
        paragraph.text = line
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(font_size)
        paragraph.font.bold = bold if index == 0 else False
        paragraph.font.color.rgb = color
        paragraph.alignment = PP_ALIGN.LEFT


def _resolve_path(value: object) -> Path | None:
    if not value:
        return None
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
