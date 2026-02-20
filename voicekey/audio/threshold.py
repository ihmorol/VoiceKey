"""Confidence threshold filtering for voice transcripts.

This module provides filtering of transcript events based on confidence scores,
ensuring only high-confidence transcriptions are passed through for processing.

Requirements: FR-A05
"""

from __future__ import annotations

import logging
from typing import Optional

from voicekey.audio.asr_faster_whisper import TranscriptEvent

logger = logging.getLogger(__name__)


class ConfidenceFilter:
    """Filters transcript events based on confidence threshold.

    This filter ensures that only transcripts with confidence scores at or above
    the configured threshold are passed through. Transcripts below the threshold
    are dropped and never typed.

    Attributes:
        threshold: Minimum confidence score (0.0 to 1.0) required to pass.
                  Defaults to 0.5.
        log_dropped: Whether to log dropped transcripts for debugging.
                     Defaults to False (privacy-by-default).

    Example:
        >>> filter_obj = ConfidenceFilter(threshold=0.7)
        >>> event = TranscriptEvent(text="Hello", is_final=True, confidence=0.8)
        >>> result = filter_obj.filter(event)
        >>> print(result.text)  # "Hello"
    """

    def __init__(self, threshold: float = 0.5, log_dropped: bool = False) -> None:
        """Initialize the confidence filter.

        Args:
            threshold: Minimum confidence score from 0.0 to 1.0.
                      Defaults to 0.5.
            log_dropped: Whether to log transcripts that are dropped.
                        Defaults to False (privacy-by-default).

        Raises:
            ValueError: If threshold is not between 0.0 and 1.0.
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}")

        self._threshold = threshold
        self._log_dropped = log_dropped
        self._dropped_count = 0

    @property
    def threshold(self) -> float:
        """Get the current confidence threshold."""
        return self._threshold

    def filter(self, transcript: Optional[TranscriptEvent]) -> Optional[TranscriptEvent]:
        """Filter a transcript based on confidence threshold.

        Per FR-A05 and story E01-S04 behavior rules, the threshold is enforced
        only for final transcript events (the events that can be typed).
        Partial transcripts are passed through unchanged.

        Args:
            transcript: The transcript event to filter, or None.

        Returns:
            The original transcript if it passes the threshold, None otherwise.
        """
        # Handle None input
        if transcript is None:
            return None

        if not transcript.is_final:
            return transcript

        # Check confidence against threshold for final transcript events
        if transcript.confidence >= self._threshold:
            return transcript

        # Transcript below threshold - drop it
        self._dropped_count += 1

        if self._log_dropped:
            logger.debug(
                "Dropped transcript due to low confidence: "
                "text=%r, confidence=%.2f, threshold=%.2f",
                transcript.text,
                transcript.confidence,
                self._threshold,
            )

        return None

    def get_dropped_count(self) -> int:
        """Get the number of transcripts that have been dropped.

        Returns:
            The count of transcripts filtered out due to low confidence.
        """
        return self._dropped_count

    def reset_stats(self) -> None:
        """Reset the dropped transcript counter to zero.

        This is useful for starting fresh statistics, for example when
        beginning a new transcription session.
        """
        self._dropped_count = 0
