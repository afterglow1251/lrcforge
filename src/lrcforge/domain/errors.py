"""Domain exception hierarchy."""

from __future__ import annotations


class LrcforgeError(Exception):
    """Base class for all lrcforge errors."""


class AudioLoadError(LrcforgeError):
    """The input file could not be probed or decoded."""


class SeparationError(LrcforgeError):
    """Vocal separation failed."""


class LanguageDetectionError(LrcforgeError):
    """Language identification failed."""


class TranscriptionError(LrcforgeError):
    """Lyrics transcription failed."""


class AlignmentError(LrcforgeError):
    """Forced alignment failed."""
