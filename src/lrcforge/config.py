"""Runtime settings (env-overridable, prefix LRCFORGE_)."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Device = Literal["auto", "cpu", "mps", "cuda"]
Transcriber = Literal["faster", "mlx"]
Aligner = Literal["mms", "whisperx"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LRCFORGE_")

    device: Device = "auto"
    transcriber: Transcriber = "faster"  # faster (portable) | mlx (Apple GPU)
    faster_model: str = "large-v3"
    mlx_model: str = "mlx-community/whisper-large-v3"
    lid_model: str = "small"
    aligner: Aligner = "mms"  # mms (multilingual) | whisperx (not yet implemented)
    default_lang: str = "auto"
