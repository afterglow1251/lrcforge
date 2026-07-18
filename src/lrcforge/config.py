"""Runtime settings (env-overridable, prefix LRCFORGE_)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LRCFORGE_")

    device: str = "auto"  # auto | cpu | mps
    whisper_model: str = "mlx-community/whisper-large-v3"
    aligner: str = "mms"  # mms | whisperx
    default_lang: str = "auto"
    # M0: bind fakes for the ML stages so the pipeline runs with zero models.
    use_fakes: bool = True
