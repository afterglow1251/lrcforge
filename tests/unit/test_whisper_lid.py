from __future__ import annotations

import pytest

from lrcforge.adapters.language.whisper_lid import aggregate_votes, plan_windows
from lrcforge.domain.errors import LanguageDetectionError
from lrcforge.domain.language import WindowVote


def test_plan_windows_spreads_across_audio() -> None:
    # 60s @ 16k with 5 windows of 10s
    windows = plan_windows(60 * 16000, sample_rate=16000, n=5, window_s=10.0)
    assert len(windows) == 5
    starts = [s for _, _, s in windows]
    assert starts == sorted(starts)
    assert starts[0] == 0.0
    # last window ends at the end of the audio
    assert windows[-1][1] == 60 * 16000


def test_plan_windows_short_audio_single_window() -> None:
    windows = plan_windows(3 * 16000, sample_rate=16000, n=5, window_s=10.0)
    assert windows == ((0, 3 * 16000, 0.0),)


def test_plan_windows_empty() -> None:
    assert plan_windows(0) == ()


def test_aggregate_votes_picks_highest_summed_confidence() -> None:
    votes = (
        WindowVote(start_s=0.0, lang="uk", confidence=0.6),
        WindowVote(start_s=10.0, lang="ru", confidence=0.9),
        WindowVote(start_s=20.0, lang="uk", confidence=0.7),
    )
    result = aggregate_votes(votes)
    # uk: 1.3 summed over 2 -> wins over ru 0.9
    assert result.lang == "uk"
    assert result.confidence == pytest.approx(0.65)
    assert len(result.per_window) == 3


def test_aggregate_votes_empty_raises() -> None:
    with pytest.raises(LanguageDetectionError):
        aggregate_votes(())
