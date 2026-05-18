from __future__ import annotations

from typing import Any

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.util import Inches, Pt


SLIDE_W = 13.333
SLIDE_H = 7.5
NAVY = RGBColor(18, 39, 76)
BLUE = RGBColor(20, 88, 140)
TEAL = RGBColor(22, 124, 128)
GREEN = RGBColor(35, 130, 88)
GOLD = RGBColor(202, 149, 48)
DARK = RGBColor(26, 32, 44)
MID = RGBColor(84, 96, 112)
LIGHT_BG = RGBColor(247, 249, 252)
PANEL = RGBColor(255, 255, 255)
BORDER = RGBColor(202, 211, 222)
PALE_BLUE = RGBColor(231, 240, 249)
PALE_GREEN = RGBColor(232, 244, 239)
PALE_GOLD = RGBColor(252, 244, 225)
PALE_RED = RGBColor(250, 235, 235)


def add_consultant_cover(prs, deck_plan: dict[str, Any]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _background(slide)
    _shape(slide, 0, 0, 13.333, 0.28, NAVY, NAVY)
    _textbox(slide, 0.7, 1.1, 10.9, 1.25, deck_plan.get("deck_title") or "Board-ready recommendation deck", 31, bold=True)
    _textbox(slide, 0.72, 2.55, 9.0, 0.55, "Client-ready draft generated from source-grounded content", 16, color=BLUE, bold=True)
    _textbox(slide, 0.72, 3.25, 9.6, 0.9, deck_plan.get("strategy_summary") or "Generated using content-first slide planning and local template intelligence.", 13, color=MID)
    facts = [
        f"Audience: {deck_plan.get('audience') or 'board / executive'}",
        f"Content sufficiency: {deck_plan.get('content_sufficiency_level', 'unknown')} ({deck_plan.get('content_sufficiency_score', 0)}/100)",
        f"Template strategy: {deck_plan.get('template_strategy') or 'Use templates only when relevant'}",
    ]
    _callout(slide, 0.75, 5.0, 5.8, 1.15, "\n".join(facts), PALE_BLUE, BLUE)
    _textbox(slide, 0.75, 6.78, 4.5, 0.22, "Strictly source-grounded; missing evidence is flagged.", 7, color=MID)


def add_consultant_agenda(prs, slides: list[dict[str, Any]]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _background(slide)
    _title(slide, "Agenda: recommended storyline")
    rows = []
    for item in slides[:14]:
        rows.append(
            [
                str(item.get("slide_number") or len(rows) + 1),
                _fit_words(_fit(item.get("slide_title") or "", 90), 14),
                item.get("slide_type") or "other",
                _fit(item.get("slide_objective") or item.get("key_message") or "", 135),
            ]
        )
    _table(slide, 0.65, 1.25, 12.1, 5.45, ["#", "Slide", "Type", "Purpose"], rows, col_widths=[0.55, 4.5, 2.0, 5.05])
    _footer(slide, "Content-first plan generated before template execution")


def add_planned_content_slide(prs, slide_plan: dict[str, Any], index: int) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _background(slide)
    _title(slide, _fit_words(_fit(slide_plan.get("slide_title") or f"Slide {index}", 120), 16))
    family = _layout_family(slide_plan)
    if family == "summary":
        _summary_layout(slide, slide_plan)
    elif family == "matrix":
        _matrix_layout(slide, slide_plan)
    elif family == "chart":
        _chart_layout(slide, slide_plan)
    elif family == "roadmap":
        _roadmap_layout(slide, slide_plan)
    elif family == "risk":
        _risk_layout(slide, slide_plan)
    elif family == "landscape":
        _landscape_layout(slide, slide_plan)
    else:
        _evidence_layout(slide, slide_plan)
    _footer(slide, _reference_footer(slide_plan))


def add_source_grounding_appendix(prs, deck_plan: dict[str, Any], slides: list[dict[str, Any]]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _background(slide)
    _title(slide, "Appendix: source grounding and template use")
    lines = [
        deck_plan.get("source_grounding_policy") or "Slides are grounded in source content.",
        f"Generation strategy: {deck_plan.get('generation_mode') or 'content_first'}",
        f"Custom layouts: {deck_plan.get('custom_layout_count', 0)} | Template shells: {deck_plan.get('template_shell_count', 0)}",
    ]
    _callout(slide, 0.65, 1.15, 12.0, 0.9, "\n".join(lines), PALE_BLUE, BLUE)
    rows = []
    for item in slides[:10]:
        matched = item.get("matched_template") or {}
        rows.append(
            [
                str(item.get("slide_number") or ""),
                item.get("slide_title") or "",
                item.get("generation_strategy") or "custom_layout",
                f"{matched.get('deck_name', '')} {matched.get('slide_number', '')}".strip(),
            ]
        )
    _table(slide, 0.65, 2.35, 12.0, 4.2, ["#", "Slide", "Execution", "Reference"], rows, col_widths=[0.55, 5.25, 2.2, 4.0])
    _footer(slide, "Source grounding appendix")


def _summary_layout(slide, plan: dict[str, Any]) -> None:
    _callout(slide, 0.65, 1.12, 12.0, 0.75, _fit(plan.get("key_message") or plan.get("slide_objective") or "Key message", 190), PALE_BLUE, BLUE)
    blocks = _blocks(plan, 5)
    for i, block in enumerate(blocks[:5]):
        x = 0.75 + i * 2.42
        _card(slide, x, 2.25, 2.12, 2.45, block["heading"], block["body"], [BLUE, TEAL, GREEN, GOLD, NAVY][i % 5])
    _evidence_bar(slide, plan)


def _matrix_layout(slide, plan: dict[str, Any]) -> None:
    blocks = _blocks(plan, 4)
    headers = ["Dimension", "Evidence / implication", "Decision relevance"]
    rows = [[b["heading"], b["body"], b.get("evidence") or _fit(plan.get("key_message", ""), 120)] for b in blocks[:5]]
    _table(slide, 0.65, 1.25, 12.0, 4.6, headers, rows, col_widths=[2.65, 5.2, 4.15])
    _callout(slide, 0.65, 6.1, 12.0, 0.62, _fit(plan.get("key_message") or "Implication to validate", 175), PALE_GOLD, GOLD)


def _chart_layout(slide, plan: dict[str, Any]) -> None:
    blocks = _blocks(plan, 4)
    _callout(slide, 0.65, 1.15, 4.0, 4.75, "Source-backed drivers\n\n" + "\n".join(f"- {b['heading']}" for b in blocks[:5]), PALE_BLUE, BLUE)
    x0, y0 = 5.25, 2.0
    values = [0.55, 0.82, 0.68, 0.95]
    labels = [b["heading"][:18] for b in blocks[:4]] or ["Driver 1", "Driver 2", "Driver 3", "Driver 4"]
    _textbox(slide, 5.25, 1.2, 6.5, 0.35, plan.get("visual_approach") or "Indicative evidence chart", 12, bold=True)
    for i, value in enumerate(values[: len(labels)]):
        bar_h = 3.1 * value
        _shape(slide, x0 + i * 1.45, y0 + 3.2 - bar_h, 0.72, bar_h, [BLUE, TEAL, GREEN, GOLD][i % 4], [BLUE, TEAL, GREEN, GOLD][i % 4])
        _textbox(slide, x0 + i * 1.2, 5.35, 1.3, 0.45, labels[i], 7, color=MID)
    _evidence_bar(slide, plan)


def _roadmap_layout(slide, plan: dict[str, Any]) -> None:
    blocks = _blocks(plan, 4)
    _textbox(slide, 0.7, 1.2, 11.8, 0.35, _fit(plan.get("key_message") or "Phased path to decision and execution", 150), 12, bold=True)
    for i, block in enumerate(blocks[:4]):
        x = 0.75 + i * 3.05
        _shape(slide, x, 2.05, 2.55, 0.38, [BLUE, TEAL, GREEN, GOLD][i % 4], [BLUE, TEAL, GREEN, GOLD][i % 4])
        _card(slide, x, 2.5, 2.55, 2.3, block["heading"] or f"Phase {i + 1}", block["body"], [BLUE, TEAL, GREEN, GOLD][i % 4])
        if i < 3:
            _shape(slide, x + 2.62, 3.45, 0.38, 0.18, BORDER, BORDER)
    _evidence_bar(slide, plan)


def _risk_layout(slide, plan: dict[str, Any]) -> None:
    blocks = _blocks(plan, 5)
    rows = [[b["heading"], b["body"], b.get("evidence") or "Mitigation / owner to confirm"] for b in blocks[:6]]
    _table(slide, 0.65, 1.25, 12.0, 4.75, ["Risk / issue", "Why it matters", "Mitigation / next step"], rows, col_widths=[3.2, 4.35, 4.45])
    _callout(slide, 0.65, 6.2, 12.0, 0.5, _fit(plan.get("key_message") or "Risks should be converted into decision gates.", 160), PALE_RED, RGBColor(178, 72, 65))


def _landscape_layout(slide, plan: dict[str, Any]) -> None:
    blocks = _blocks(plan, 4)
    _shape(slide, 0.65, 1.25, 8.0, 4.75, RGBColor(250, 252, 255), BORDER)
    _textbox(slide, 0.9, 1.48, 7.35, 0.32, plan.get("visual_approach") or "Landscape / segmentation view", 12, bold=True)
    for i, block in enumerate(blocks[:4]):
        x = 1.0 + (i % 2) * 3.65
        y = 2.05 + (i // 2) * 1.65
        _card(slide, x, y, 3.25, 1.22, block["heading"], block["body"], [BLUE, TEAL, GREEN, GOLD][i % 4], font_size=8)
    _callout(slide, 9.0, 1.25, 3.25, 4.75, "Key observations\n\n" + _bullet_text([b["heading"] for b in blocks[:5]]), PALE_GREEN, GREEN)
    _evidence_bar(slide, plan)


def _evidence_layout(slide, plan: dict[str, Any]) -> None:
    _callout(slide, 0.65, 1.15, 12.0, 0.8, _fit(plan.get("key_message") or plan.get("slide_objective") or "Source-backed finding", 190), PALE_BLUE, BLUE)
    blocks = _blocks(plan, 4)
    for i, block in enumerate(blocks[:4]):
        x = 0.7 + (i % 2) * 6.05
        y = 2.25 + (i // 2) * 1.85
        _card(slide, x, y, 5.55, 1.45, block["heading"], block["body"], [BLUE, TEAL, GREEN, GOLD][i % 4])
    _evidence_bar(slide, plan)


def _evidence_bar(slide, plan: dict[str, Any]) -> None:
    evidence = _list(plan.get("source_evidence"))[:3]
    missing = _list(plan.get("missing_data_or_assumptions"))[:2]
    text = "Source evidence: " + (_fit("; ".join(evidence), 220) if evidence else "Source basis to be confirmed")
    if missing:
        text += "\nMissing / assumption: " + _fit("; ".join(missing), 150)
    _callout(slide, 0.65, 6.12, 12.0, 0.62, text, RGBColor(249, 250, 252), MID, font_size=7)


def _layout_family(plan: dict[str, Any]) -> str:
    slide_type = str(plan.get("slide_type") or "").lower()
    chart_type = str(plan.get("chart_type") or "").lower()
    title = str(plan.get("slide_title") or "").lower()
    text = f"{slide_type} {chart_type} {title}"
    if any(term in text for term in ["executive_summary", "summary", "decision_paper", "recommendation"]):
        return "summary"
    if any(term in text for term in ["competitor", "benchmark", "options", "matrix", "table", "comparison", "build", "buy", "partner"]):
        return "matrix"
    if any(term in text for term in ["market_sizing", "financial", "valuation", "bar_chart", "line_chart", "waterfall"]):
        return "chart"
    if any(term in text for term in ["roadmap", "implementation", "timeline", "journey"]):
        return "roadmap"
    if any(term in text for term in ["risk", "challenge", "mitigation"]):
        return "risk"
    if any(term in text for term in ["landscape", "market", "industry", "trend"]):
        return "landscape"
    return "evidence"


def _blocks(plan: dict[str, Any], minimum: int) -> list[dict[str, str]]:
    raw = plan.get("content_blocks")
    blocks: list[dict[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                blocks.append(
                    {
                        "heading": _fit(str(item.get("heading") or item.get("title") or "Finding").strip(), 55),
                        "body": _fit(str(item.get("body") or item.get("content") or "").strip(), 175),
                        "evidence": _fit(str(item.get("evidence") or "").strip(), 120),
                    }
                )
            elif str(item).strip():
                blocks.append({"heading": _fit(str(item).strip(), 55), "body": "", "evidence": ""})
    while len(blocks) < minimum:
        evidence = _list(plan.get("source_evidence"))
        missing = _list(plan.get("missing_data_or_assumptions"))
        idx = len(blocks)
        if idx < len(evidence):
            blocks.append({"heading": f"Evidence {idx + 1}", "body": _fit(evidence[idx], 175), "evidence": _fit(evidence[idx], 120)})
        elif idx - len(evidence) < len(missing):
            value = missing[idx - len(evidence)]
            blocks.append({"heading": "Research gap", "body": _fit(value, 175), "evidence": "Missing from source"})
        else:
            blocks.append({"heading": "Source-backed point", "body": _fit(plan.get("key_message") or plan.get("slide_objective") or "", 175), "evidence": ""})
    return blocks


def _reference_footer(plan: dict[str, Any]) -> str:
    matched = plan.get("matched_template") or {}
    bits = [plan.get("generation_strategy") or "custom_layout"]
    if matched:
        score = matched.get("template_fit_score") or matched.get("similarity_score") or matched.get("match_score")
        bits.append(f"Reference: {matched.get('deck_name')} slide {matched.get('slide_number')}")
        if score is not None:
            bits.append(f"fit {score}")
    return " | ".join(str(bit) for bit in bits if bit)


def _background(slide) -> None:
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = LIGHT_BG


def _title(slide, text: str) -> None:
    _textbox(slide, 0.55, 0.28, 12.25, 0.6, text, 19, bold=True)
    _shape(slide, 0.55, 0.96, 12.25, 0.025, BLUE, BLUE)


def _footer(slide, text: str) -> None:
    _textbox(slide, 0.55, 7.08, 12.2, 0.22, text, 6, color=MID)


def _card(slide, x: float, y: float, w: float, h: float, heading: str, body: str, accent: RGBColor, font_size: int = 8) -> None:
    _shape(slide, x, y, w, h, PANEL, BORDER)
    _shape(slide, x, y, 0.08, h, accent, accent)
    _textbox(slide, x + 0.18, y + 0.15, w - 0.3, 0.32, heading or "Finding", font_size + 1, bold=True, color=DARK)
    _textbox(slide, x + 0.18, y + 0.58, w - 0.3, h - 0.7, body or "Source-grounded detail to confirm.", font_size, color=MID)


def _callout(slide, x: float, y: float, w: float, h: float, text: str, fill: RGBColor, accent: RGBColor, font_size: int = 10) -> None:
    _shape(slide, x, y, w, h, fill, BORDER)
    _shape(slide, x, y, 0.08, h, accent, accent)
    _textbox(slide, x + 0.2, y + 0.12, w - 0.35, h - 0.18, text, font_size, color=DARK)


def _table(slide, x: float, y: float, w: float, h: float, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None):
    row_count = max(2, min(len(rows) + 1, 10))
    table_shape = slide.shapes.add_table(row_count, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    table = table_shape.table
    if col_widths and len(col_widths) == len(headers):
        for idx, width in enumerate(col_widths):
            table.columns[idx].width = Inches(width)
    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = header
        _format_cell(cell, NAVY, RGBColor(255, 255, 255), bold=True)
    for r, row in enumerate(rows[: row_count - 1], start=1):
        for c in range(len(headers)):
            cell = table.cell(r, c)
            cell.text = row[c] if c < len(row) else ""
            _format_cell(cell, RGBColor(255, 255, 255), DARK)
    return table_shape


def _format_cell(cell, fill: RGBColor, color: RGBColor, bold: bool = False) -> None:
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.margin_left = Inches(0.06)
    cell.margin_right = Inches(0.06)
    cell.margin_top = Inches(0.04)
    cell.margin_bottom = Inches(0.04)
    for paragraph in cell.text_frame.paragraphs:
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(7.5 if not bold else 8.5)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = color


def _shape(slide, x: float, y: float, w: float, h: float, fill: RGBColor, line: RGBColor):
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(0.5)
    return shape


def _textbox(slide, x: float, y: float, w: float, h: float, text: str, font_size: int, *, color: RGBColor = DARK, bold: bool = False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    frame.margin_left = Inches(0.03)
    frame.margin_right = Inches(0.03)
    frame.margin_top = Inches(0.01)
    frame.margin_bottom = Inches(0.01)
    for i, line in enumerate(str(text).splitlines() or [""]):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(font_size)
        paragraph.font.bold = bold if i == 0 else False
        paragraph.font.color.rgb = color
        paragraph.alignment = PP_ALIGN.LEFT
    return shape


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _bullet_text(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


def _fit(value: object, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    trimmed = text[: max_chars - 3].rsplit(" ", 1)[0]
    return (trimmed or text[: max_chars - 3]).rstrip() + "..."


def _fit_words(value: object, max_words: int) -> str:
    words = str(value or "").split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(" ,;:") + "..."
