"""Demucs (htdemucs) vocal separation.

NOTE: the model call path is not exercised in CI (torch/demucs are not installed in the
typecheck/test env). Heavy imports are lazy so the fakes path never pulls torch. Validate
on a first real run. The orchestration around the model IS unit-tested via a stub module."""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from lrcforge.adapters.audio.soundfile_loader import SoundfileAudioLoader
from lrcforge.domain.audio import AudioRef, VocalStem
from lrcforge.domain.errors import SeparationError


class _DemucsSeparator(Protocol):
    """The exact demucs.api.Separator surface we use (avoids a leaked Any)."""

    samplerate: int

    def separate_audio_file(self, path: str) -> tuple[object, Mapping[str, object]]: ...


class DemucsSeparator:
    def __init__(self, model_name: str = "htdemucs", device: str = "auto") -> None:
        self._model_name = model_name
        self._device = None if device == "auto" else device
        self._separator: _DemucsSeparator | None = None
        self._workdir: Path | None = None
        self._loader = SoundfileAudioLoader()

    def _ensure_separator(self) -> _DemucsSeparator:
        if self._separator is None:
            from demucs.api import Separator  # lazy: keeps torch out of the fakes path

            self._separator = Separator(model=self._model_name, device=self._device)
        separator = self._separator
        assert separator is not None
        return separator

    def _ensure_workdir(self) -> Path:
        if self._workdir is None:
            self._workdir = Path(tempfile.mkdtemp(prefix="lrcforge-stems-"))
        return self._workdir

    def separate(self, audio: AudioRef) -> VocalStem:
        from demucs.api import save_audio  # lazy

        try:
            separator = self._ensure_separator()
            _origin, stems = separator.separate_audio_file(str(audio.path))
            vocals = stems["vocals"]
            out_path = self._ensure_workdir() / f"{audio.path.stem}.vocals.wav"
            save_audio(vocals, str(out_path), samplerate=separator.samplerate)
        except (RuntimeError, OSError, KeyError, ValueError, ImportError) as exc:
            raise SeparationError(f"demucs separation failed for {audio.path}: {exc}") from exc

        probed = self._loader.probe(out_path)
        return VocalStem(audio=probed, separated_by=f"demucs:{self._model_name}")
