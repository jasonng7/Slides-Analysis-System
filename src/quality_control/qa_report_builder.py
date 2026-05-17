from __future__ import annotations

from pathlib import Path
from typing import Any


def build_terminal_qa_summary(qa_result: dict[str, Any]) -> str:
    reviewed = Path(str(qa_result.get("reviewed_path") or "unknown")).name
    summary = qa_result.get("summary") or {}
    issues = qa_result.get("issues") or []
    recommendations = qa_result.get("recommendations") or []
    lines = [
        f"QA Review: {reviewed}",
        f"Overall score: {qa_result.get('overall_score')} / 100",
        f"Rating: {qa_result.get('rating')}",
        "",
        "Key findings:",
    ]
    if qa_result.get("qa_type") == "generated_deck":
        lines.extend(
            [
                f"- {summary.get('total_slides', 'n/a')} total slides, {summary.get('content_slides', 'n/a')} content slides",
                f"- Cover: {_yes_no(summary.get('cover_found'))}, agenda: {_yes_no(summary.get('agenda_found'))}, appendix: {_yes_no(summary.get('appendix_found'))}",
                f"- Cloned slides: {summary.get('cloned_slide_count', 'n/a')}, image fallbacks: {summary.get('image_fallback_count', 'n/a')}",
                f"- Matching method: {summary.get('matching_method') or 'n/a'}",
            ]
        )
    else:
        lines.extend(
            [
                f"- Recommended mode: {summary.get('recommended_mode', 'n/a')}",
                f"- Recommended slides: {summary.get('recommended_slide_count', 'n/a')}",
                f"- Matched templates: {summary.get('matched_template_count', 'n/a')}",
                f"- Matching method: {summary.get('matching_method') or 'n/a'}",
            ]
        )

    lines.append("")
    lines.append("Top issues:")
    visible_issues = [item for item in issues if item.get("severity") != "info"]
    if visible_issues:
        for item in visible_issues[:8]:
            prefix = f"[{str(item.get('severity', '')).title()}] {item.get('category')}:"
            slide = f" Slide {item['slide_number']}." if item.get("slide_number") else ""
            lines.append(f"{prefix} {item.get('message')}{slide}")
    else:
        lines.append("- No blocking issues detected.")

    info_issues = [item for item in issues if item.get("severity") == "info"]
    if info_issues:
        lines.append("")
        lines.append("Positive checks:")
        for item in info_issues[:4]:
            lines.append(f"- {item.get('message')}")

    lines.append("")
    lines.append("Recommended next actions:")
    if recommendations:
        for index, recommendation in enumerate(recommendations[:6], start=1):
            lines.append(f"{index}. {recommendation}")
    else:
        lines.append("1. Manually review the deck before client or board use.")

    if qa_result.get("qa_json_path"):
        lines.append("")
        lines.append(f"QA JSON: {qa_result['qa_json_path']}")
    if qa_result.get("qa_markdown_path"):
        lines.append(f"QA Markdown: {qa_result['qa_markdown_path']}")
    return "\n".join(lines)


def build_markdown_qa_report(qa_result: dict[str, Any]) -> str:
    summary = qa_result.get("summary") or {}
    issues = qa_result.get("issues") or []
    findings = qa_result.get("slide_level_findings") or []
    recommendations = qa_result.get("recommendations") or []
    metadata = qa_result.get("metadata") or {}
    lines = [
        f"# QA Report: {Path(str(qa_result.get('reviewed_path') or 'unknown')).name}",
        "",
        f"**QA type:** {qa_result.get('qa_type')}",
        f"**Reviewed file:** `{qa_result.get('reviewed_path')}`",
        f"**Generated at:** {qa_result.get('generated_at')}",
        f"**Overall score:** {qa_result.get('overall_score')} / 100",
        f"**Rating:** {qa_result.get('rating')}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Issues", ""])
    if issues:
        lines.extend(["| Severity | Category | Slide | Message | Recommendation |", "| --- | --- | --- | --- | --- |"])
        for item in issues:
            lines.append(
                "| {severity} | {category} | {slide} | {message} | {recommendation} |".format(
                    severity=item.get("severity", ""),
                    category=item.get("category", ""),
                    slide=item.get("slide_number", ""),
                    message=_escape_table(str(item.get("message", ""))),
                    recommendation=_escape_table(str(item.get("recommendation", ""))),
                )
            )
    else:
        lines.append("No issues detected.")

    lines.extend(["", "## Slide-Level Findings", ""])
    if findings:
        lines.extend(["| Slide | Title | Issue | Word count | Text characters |", "| --- | --- | --- | --- | --- |"])
        for finding in findings[:80]:
            lines.append(
                "| {slide} | {title} | {issue} | {words} | {chars} |".format(
                    slide=finding.get("slide_number", ""),
                    title=_escape_table(str(finding.get("title") or finding.get("slide_title") or "")),
                    issue=finding.get("issue", ""),
                    words=finding.get("word_count", ""),
                    chars=finding.get("text_character_count", ""),
                )
            )
    else:
        lines.append("No slide-level findings.")

    lines.extend(["", "## Recommendations", ""])
    if recommendations:
        for index, recommendation in enumerate(recommendations, start=1):
            lines.append(f"{index}. {recommendation}")
    else:
        lines.append("1. Manually review the deck before client or board use.")

    if metadata:
        lines.extend(["", "## Metadata", ""])
        for key in [
            "generator_version",
            "matching_method",
            "reference_background_mode",
            "number_of_slides",
            "number_of_content_slides",
            "content_slides_cloned_from_source_pptx",
            "content_slides_with_image_fallback",
        ]:
            if key in metadata:
                lines.append(f"- **{key}:** {metadata[key]}")

    return "\n".join(lines).strip() + "\n"


def _yes_no(value: object) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "n/a"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
