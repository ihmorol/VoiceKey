"""Unit tests for deterministic snippet expansion engine (E06-S05)."""

from __future__ import annotations

from voicekey.commands.snippets import SnippetExpander


def test_snippet_expander_applies_exact_expansion_when_enabled() -> None:
    expander = SnippetExpander({"ty": "thank you"})

    assert expander.expand("ty") == "thank you"


def test_snippet_expander_is_deterministic_across_calls() -> None:
    expander = SnippetExpander({"brb": "be right back"})

    assert expander.expand("brb") == "be right back"
    assert expander.expand("brb") == "be right back"
    assert expander.expand("brb") == "be right back"


def test_snippet_expander_keeps_non_matching_text_unchanged() -> None:
    expander = SnippetExpander({"ty": "thank you"})

    assert expander.expand("hello world") == "hello world"


def test_snippet_expander_self_reference_is_guarded() -> None:
    expander = SnippetExpander({"loop": "loop"})

    assert expander.expand("loop") == "loop"


def test_snippet_expander_mutual_cycle_is_guarded() -> None:
    expander = SnippetExpander({"a": "b", "b": "a"})

    assert expander.expand("a") == "a"


def test_snippet_expander_respects_max_depth_limit() -> None:
    expander = SnippetExpander(
        {
            "a": "b",
            "b": "c",
            "c": "d",
        },
        max_depth=2,
    )

    assert expander.expand("a") == "c"
