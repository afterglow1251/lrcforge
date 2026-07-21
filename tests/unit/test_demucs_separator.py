"""Exercise the DemucsSeparator wrapper logic with a stub `demucs.api` (no torch)."""

from __future__ import annotations

import math
import struct
import sys
import types
import wave
from pathlib import Path

import pytest

from lrcforge.adapters.separation.demucs_separator import DemucsSeparator
from lrcforge.domain.audio import AudioRef


def _write_wav(path: Path, *, seconds: float = 0.5, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytes(
            b"".join(
                struct.pack("<h", int(1000 * math.sin(2 * math.pi * 200 * i / rate)))
                for i in range(int(seconds * rate))
            )
        )
        w.writeframes(frames)


@pytest.fixture
def stub_demucs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install a fake `demucs.api` that skips torch and writes a real wav for `vocals`."""

    class _Separator:
        samplerate = 16000

        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def separate_audio_file(self, _path: str) -> tuple[object, dict[str, object]]:
            return (object(), {"vocals": object(), "drums": object()})

    def _save_audio(_wav: object, path: str, samplerate: int = 16000) -> None:
        _write_wav(Path(path), rate=samplerate)

    module = types.ModuleType("demucs.api")
    module.Separator = _Separator  # type: ignore[attr-defined]
    module.save_audio = _save_audio  # type: ignore[attr-defined]
    pkg = types.ModuleType("demucs")
    monkeypatch.setitem(sys.modules, "demucs", pkg)
    monkeypatch.setitem(sys.modules, "demucs.api", module)


def test_separate_returns_probed_vocal_stem(stub_demucs: None, tmp_path: Path) -> None:
    src = tmp_path / "song.wav"
    _write_wav(src, seconds=1.0, rate=16000)

    sep = DemucsSeparator()
    stem = sep.separate(AudioRef(path=src, sample_rate=16000, channels=1, duration_s=1.0))

    assert stem.separated_by == "demucs:htdemucs"
    assert stem.audio.path.name == "song.vocals.wav"
    assert stem.audio.sample_rate == 16000
    assert stem.audio.duration_s > 0.0
