"""Runtime settings (env-overridable, prefix LRCFORGE_)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LRCFORGE_")

    device: str = "auto"  # auto | cpu | mps | cuda
    transcriber: str = "faster"  # faster (default, portable) | mlx (Apple GPU)
    faster_model: str = "large-v3"
    mlx_model: str = "mlx-community/whisper-large-v3"
    lid_model: str = "small"
    aligner: str = "mms"  # mms (default, multilingual) | whisperx (not yet implemented)
    default_lang: str = "auto"
