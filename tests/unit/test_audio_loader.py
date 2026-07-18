from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest

from lrcforge.adapters.audio.soundfile_loader import SoundfileAudioLoader
from lrcforge.domain.errors import AudioLoadError


def _write_wav(path: Path, *, seconds: float, rate: int, channels: int) -> None:
    frame_count = int(seconds * rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        buf = bytearray()
        for i in range(frame_count):
            sample = int(3000 * math.sin(2 * math.pi * 220 * i / rate))
            packed = struct.pack("<h", sample)
            buf += packed * channels
        w.writeframes(bytes(buf))


def test_probe_returns_real_metadata(tmp_path: Path) -> None:
    wav = tmp_path / "tone.wav"
    _write_wav(wav, seconds=1.5, rate=22050, channels=2)

    ref = SoundfileAudioLoader().probe(wav)

    assert ref.path == wav
    assert ref.sample_rate == 22050
    assert ref.channels == 2
    assert 1.4 < ref.duration_s < 1.6


def test_probe_missing_file_raises_domain_error(tmp_path: Path) -> None:
    with pytest.raises(AudioLoadError):
        SoundfileAudioLoader().probe(tmp_path / "does-not-exist.wav")
