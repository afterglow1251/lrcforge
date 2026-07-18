"""Real audio probe via libsndfile (soundfile). Metadata only — no decoding into
memory here; downstream ML adapters decode/resample from the path as they need."""

from __future__ import annotations

from pathlib import Path

import soundfile as sf

from lrcforge.domain.audio import AudioRef
from lrcforge.domain.errors import AudioLoadError


class SoundfileAudioLoader:
    def probe(self, path: Path) -> AudioRef:
        try:
            info = sf.info(str(path))
        except (RuntimeError, OSError) as exc:
            raise AudioLoadError(f"cannot probe {path}: {exc}") from exc
        return AudioRef(
            path=path,
            sample_rate=int(info.samplerate),
            channels=int(info.channels),
            duration_s=float(info.duration),
        )
