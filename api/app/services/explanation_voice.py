"""Explanation voice linter & style warnings (§VII.8.2).

Enforced as non-blocking warnings in the editor and scored by the read-only
`scripts/explanation-voice-report.py` packet generator. Never rejects human
writing outright.
"""
from __future__ import annotations

import re

VOICE_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        'reader-address',
        'Avoid addressing the reader ("Let\'s", "we can see", "you should note", "remember that").',
        re.compile(r"\b(let['’]s|we can see|we know that|you should note|you can see|remember that|keep in mind)\b", re.I),
    ),
    (
        'meta-commentary',
        'Avoid meta-commentary ("This question tests...", "The key here is...", "It is important to note...").',
        re.compile(r"\b(this question (tests|asks|checks)|the key here is|it is important to note|note that|crucially|essentially)\b", re.I),
    ),
    (
        'answer-restatement',
        'Do not restate the answer option as a conclusion ("Therefore, the correct answer is (B)"). Start with the fact.',
        re.compile(r"\b(therefore|thus|hence|so),?\s+(the\s+)?(correct\s+)?(answer|option)\s+(is|will be)\b", re.I),
    ),
    (
        'hedging-padding',
        'Avoid hedging or closing revision advice ("generally speaking", "it can be said that", "for exam preparation").',
        re.compile(r"\b(generally speaking|it can be said that|in conclusion|for exam preparation|make sure to revise)\b", re.I),
    ),
    (
        'em-dash-cascade',
        'Keep at most one em-dash per sentence.',
        re.compile(r"—[^.!?]*—"),
    ),
]


def check_explanation_voice(text: str | None) -> list[dict[str, str]]:
    """Return a list of structured voice warnings for an explanation."""
    raw = (text or '').strip()
    if not raw:
        return []
    warnings: list[dict[str, str]] = []
    for code, guidance, pattern in VOICE_RULES:
        match = pattern.search(raw)
        if match:
            warnings.append({
                'code': code,
                'match': match.group(0),
                'guidance': guidance,
            })
    return warnings


def voice_score(text: str | None) -> int:
    """Higher score = worse AI-wording offender for packet ranking."""
    warnings = check_explanation_voice(text)
    raw = (text or '').strip()
    score = len(warnings) * 10
    if len(raw) > 650:
        score += 5
    return score
