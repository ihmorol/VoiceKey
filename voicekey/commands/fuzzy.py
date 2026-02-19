"""Optional deterministic fuzzy matching adapter for commands."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher

from voicekey.commands.registry import normalize_phrase


@dataclass(frozen=True)
class FuzzyMatchConfig:
    """Runtime controls for optional fuzzy command matching."""

    enabled: bool = False
    threshold: float = 0.85

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("fuzzy threshold must be between 0.0 and 1.0")


class FuzzyMatcher:
    """Score phrases deterministically and return best thresholded match."""

    def best_match(self, phrase: str, candidates: Iterable[str], threshold: float) -> str | None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("fuzzy threshold must be between 0.0 and 1.0")

        normalized_phrase = normalize_phrase(phrase)
        if not normalized_phrase:
            return None

        best_phrase: str | None = None
        best_score = threshold

        for candidate in sorted(candidates):
            score = SequenceMatcher(a=normalized_phrase, b=normalize_phrase(candidate)).ratio()
            if score > best_score:
                best_phrase = candidate
                best_score = score

        return best_phrase
