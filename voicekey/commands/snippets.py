"""Deterministic text expansion engine with recursion guards."""

from __future__ import annotations

from collections.abc import Mapping

from voicekey.commands.registry import normalize_phrase


class SnippetExpander:
    """Expand configured snippet triggers into deterministic replacement text."""

    def __init__(self, snippets: Mapping[str, str] | None = None, *, max_depth: int = 8) -> None:
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        self._max_depth = max_depth
        self._snippets = _normalize_snippets(snippets or {})

    def expand(self, text: str) -> str:
        """Expand snippet triggers in normalized text with bounded recursion."""
        normalized_text = normalize_phrase(text)
        if not normalized_text:
            return normalized_text

        expanded_tokens: list[str] = []
        for token in normalized_text.split(" "):
            expanded_tokens.extend(self._expand_token(token, trail=(), depth=0))
        return " ".join(expanded_tokens)

    def _expand_token(self, token: str, *, trail: tuple[str, ...], depth: int) -> tuple[str, ...]:
        replacement = self._snippets.get(token)
        if replacement is None:
            return (token,)

        if token in trail or depth >= self._max_depth:
            return (token,)

        replacement_tokens = replacement.split(" ")
        expanded: list[str] = []
        for replacement_token in replacement_tokens:
            expanded.extend(
                self._expand_token(
                    replacement_token,
                    trail=trail + (token,),
                    depth=depth + 1,
                )
            )
        return tuple(expanded)


def _normalize_snippets(raw_snippets: Mapping[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for raw_key, raw_value in raw_snippets.items():
        key = normalize_phrase(raw_key)
        value = normalize_phrase(raw_value)
        if not key or not value:
            continue
        normalized[key] = value
    return normalized


__all__ = ["SnippetExpander"]
