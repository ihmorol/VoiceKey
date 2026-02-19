"""Unit tests for confidence threshold filtering module.

Tests for the ConfidenceFilter class that filters out low-confidence transcripts.
"""

from __future__ import annotations

import pytest

from voicekey.audio.asr_faster_whisper import TranscriptEvent
from voicekey.audio.threshold import ConfidenceFilter


class TestConfidenceFilter:
    """Tests for ConfidenceFilter class."""

    def test_filter_passes_high_confidence(self):
        """Test that transcripts above threshold pass through."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        event = TranscriptEvent(
            text="Hello world",
            is_final=True,
            confidence=0.95,
            language="en",
        )
        
        result = filter_obj.filter(event)
        
        assert result is not None
        assert result.text == "Hello world"
        assert result.confidence == 0.95

    def test_filter_drops_low_confidence(self):
        """Test that transcripts below threshold are dropped."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        event = TranscriptEvent(
            text="Hello world",
            is_final=True,
            confidence=0.3,
            language="en",
        )
        
        result = filter_obj.filter(event)
        
        assert result is None

    def test_filter_at_exact_threshold(self):
        """Test that transcripts at exactly threshold pass through."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        event = TranscriptEvent(
            text="Hello world",
            is_final=True,
            confidence=0.5,
            language="en",
        )
        
        result = filter_obj.filter(event)
        
        assert result is not None

    def test_filter_partial_transcripts(self):
        """Test that partial transcripts bypass final-confidence threshold."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        # High confidence partial should pass
        partial_high = TranscriptEvent(
            text="Hello",
            is_final=False,
            confidence=0.8,
        )
        result_high = filter_obj.filter(partial_high)
        assert result_high is not None
        
        # Low confidence partial should still pass (threshold applies to finals)
        partial_low = TranscriptEvent(
            text="Hello",
            is_final=False,
            confidence=0.25,
        )
        result_low = filter_obj.filter(partial_low)
        assert result_low is not None

        assert filter_obj.get_dropped_count() == 0

    def test_get_dropped_count(self):
        """Test that dropped count is tracked correctly."""
        filter_obj = ConfidenceFilter(threshold=0.7, log_dropped=False)
        
        # Drop some transcripts
        filter_obj.filter(TranscriptEvent(text="one", is_final=True, confidence=0.3))
        filter_obj.filter(TranscriptEvent(text="two", is_final=True, confidence=0.5))
        filter_obj.filter(TranscriptEvent(text="three", is_final=True, confidence=0.9))
        
        assert filter_obj.get_dropped_count() == 2

    def test_reset_stats(self):
        """Test that reset_stats clears the dropped count."""
        filter_obj = ConfidenceFilter(threshold=0.7, log_dropped=False)
        
        # Drop some transcripts
        filter_obj.filter(TranscriptEvent(text="one", is_final=True, confidence=0.3))
        filter_obj.filter(TranscriptEvent(text="two", is_final=True, confidence=0.5))
        
        assert filter_obj.get_dropped_count() == 2
        
        filter_obj.reset_stats()
        
        assert filter_obj.get_dropped_count() == 0

    def test_default_threshold(self):
        """Test that default threshold is 0.5."""
        filter_obj = ConfidenceFilter(log_dropped=False)
        
        # 0.5 should pass (>=)
        event = TranscriptEvent(text="test", is_final=True, confidence=0.5)
        assert filter_obj.filter(event) is not None
        
        # Below 0.5 should fail
        event = TranscriptEvent(text="test", is_final=True, confidence=0.49)
        assert filter_obj.filter(event) is None

    def test_custom_threshold(self):
        """Test that custom threshold works correctly."""
        filter_obj = ConfidenceFilter(threshold=0.8, log_dropped=False)
        
        # Below 0.8 should fail
        event = TranscriptEvent(text="test", is_final=True, confidence=0.75)
        assert filter_obj.filter(event) is None
        
        # 0.8 and above should pass
        event = TranscriptEvent(text="test", is_final=True, confidence=0.8)
        assert filter_obj.filter(event) is not None
        
        event = TranscriptEvent(text="test", is_final=True, confidence=0.95)
        assert filter_obj.filter(event) is not None

    def test_none_transcript(self):
        """Test that None input returns None."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        result = filter_obj.filter(None)
        
        assert result is None

    def test_empty_text_still_filtered(self):
        """Test that empty text is handled based on confidence."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        # High confidence empty text passes
        event = TranscriptEvent(
            text="",
            is_final=True,
            confidence=0.9,
        )
        result = filter_obj.filter(event)
        assert result is not None
        
        # Low confidence empty text fails
        event = TranscriptEvent(
            text="",
            is_final=True,
            confidence=0.3,
        )
        result = filter_obj.filter(event)
        assert result is None


class TestConfidenceFilterIntegration:
    """Integration tests for confidence filter with real workflow."""

    def test_multiple_transcripts_filtering(self):
        """Test filtering multiple transcripts in sequence."""
        filter_obj = ConfidenceFilter(threshold=0.6, log_dropped=False)
        
        transcripts = [
            TranscriptEvent(text="hello", is_final=True, confidence=0.95),
            TranscriptEvent(text="this is a test", is_final=True, confidence=0.45),
            TranscriptEvent(text="another one", is_final=True, confidence=0.75),
            TranscriptEvent(text="low confidence", is_final=True, confidence=0.3),
            TranscriptEvent(text="final test", is_final=True, confidence=0.85),
        ]
        
        passed = [t for t in transcripts if filter_obj.filter(t) is not None]
        
        assert len(passed) == 3
        assert filter_obj.get_dropped_count() == 2
        assert passed[0].text == "hello"
        assert passed[1].text == "another one"
        assert passed[2].text == "final test"

    def test_mixed_final_and_partial(self):
        """Test filtering with mix of final and partial transcripts."""
        filter_obj = ConfidenceFilter(threshold=0.5, log_dropped=False)
        
        transcripts = [
            TranscriptEvent(text="hello", is_final=False, confidence=0.9),
            TranscriptEvent(text="hello world", is_final=True, confidence=0.4),
            TranscriptEvent(text="testing", is_final=False, confidence=0.3),
            TranscriptEvent(text="complete sentence", is_final=True, confidence=0.8),
        ]
        
        results = [filter_obj.filter(t) for t in transcripts]
        
        # First passes (high confidence partial)
        assert results[0] is not None
        # Second fails (low confidence final)
        assert results[1] is None
        # Third passes (low confidence partial bypasses threshold)
        assert results[2] is not None
        # Fourth passes (high confidence final)
        assert results[3] is not None

        assert filter_obj.get_dropped_count() == 1
