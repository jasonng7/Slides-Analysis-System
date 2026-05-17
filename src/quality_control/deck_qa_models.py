from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


SEVERITY_PENALTIES = {
    "critical": 35,
    "high": 18,
    "medium": 8,
    "low": 3,
    "info": 0,
}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "our",
    "should",
    "the",
    "to",
    "with",
}


@dataclass
class QAIssue:
    severity: str
    category: str
    message: str
    slide_number: int | None = None
    recommendation: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "recommendation": self.recommendation,
        }
        if self.slide_number is not None:
            payload["slide_number"] = self.slide_number
        return payload


@dataclass
class ScoreBreakdown:
    structure_quality: int = 25
    slide_quality: int = 25
    template_matching_quality: int = 25
    generation_quality: int = 25

    def as_dict(self) -> dict[str, int]:
        return {
            "structure_quality": self.structure_quality,
            "slide_quality": self.slide_quality,
            "template_matching_quality": self.template_matching_quality,
            "generation_quality": self.generation_quality,
        }

    @property
    def total(self) -> int:
        return max(
            0,
            min(
                100,
                self.structure_quality
                + self.slide_quality
                + self.template_matching_quality
                + self.generation_quality,
            ),
        )


def issue(
    severity: str,
    category: str,
    message: str,
    recommendation: str = "",
    slide_number: int | None = None,
) -> dict[str, Any]:
    return QAIssue(
        severity=severity,
        category=category,
        message=message,
        recommendation=recommendation,
        slide_number=slide_number,
    ).as_dict()


def rating_for_score(score: int | float) -> str:
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Usable with minor review"
    if score >= 50:
        return "Needs consultant refinement"
    return "Needs regeneration or major manual fixing"


def score_from_issues(base_score: int, issues: list[dict[str, Any]]) -> int:
    penalty = sum(SEVERITY_PENALTIES.get(str(item.get("severity")), 0) for item in issues)
    return max(0, min(100, base_score - penalty))


def clamp_category_score(score: int | float) -> int:
    return max(0, min(25, int(round(score))))


def normalize_title(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", title.lower())
    tokens = [token for token in cleaned.split() if token and token not in STOP_WORDS]
    return " ".join(tokens)


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def find_duplicate_titles(titles: list[str]) -> list[dict[str, Any]]:
    normalized = [normalize_title(title) for title in titles]
    counts = Counter(item for item in normalized if item)
    duplicates = [
        {"title": titles[index], "normalized_title": item}
        for index, item in enumerate(normalized)
        if item and counts[item] > 1
    ]
    return duplicates


def find_near_duplicate_titles(
    titles: list[str],
    threshold: float = 0.86,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    normalized = [normalize_title(title) for title in titles]
    for left_index, left in enumerate(normalized):
        if not left:
            continue
        for right_index in range(left_index + 1, len(normalized)):
            right = normalized[right_index]
            if not right or left == right:
                continue
            ratio = SequenceMatcher(None, left, right).ratio()
            if ratio > threshold:
                findings.append(
                    {
                        "left_slide_number": left_index + 1,
                        "right_slide_number": right_index + 1,
                        "left_title": titles[left_index],
                        "right_title": titles[right_index],
                        "similarity": round(ratio, 3),
                    }
                )
    return findings


def repeated_template_usage(
    references: list[dict[str, Any]],
) -> list[tuple[tuple[str, str], int]]:
    counts: Counter[tuple[str, str]] = Counter()
    for reference in references:
        deck_name = str(reference.get("deck_name") or "")
        slide_number = str(reference.get("slide_number") or "")
        if deck_name and slide_number:
            counts[(deck_name, slide_number)] += 1
    return counts.most_common()


def safe_path(path: str | Path | None) -> Path | None:
    if not path:
        return None
    return Path(path).expanduser().resolve()


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def add_recommendation_once(recommendations: list[str], text: str) -> None:
    if text and text not in recommendations:
        recommendations.append(text)
