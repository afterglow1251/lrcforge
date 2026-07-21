# lrcforge web service (CPU). NB: this image installs the full torch + Demucs + Whisper
# + MMS stack and downloads multi-GB model weights at runtime — it needs a real instance
# (RAM + disk), NOT a free tier. See DEPLOY.md.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system -e ".[service,ml]"

# CPU + the small faster-whisper model keep memory sane on a modest instance.
ENV LRCFORGE_DEVICE=cpu \
    LRCFORGE_TRANSCRIBER=faster \
    LRCFORGE_FASTER_MODEL=small \
    LRCFORGE_LID_MODEL=small

EXPOSE 8000
CMD ["lrcforge", "serve", "--host", "0.0.0.0", "--port", "8000"]
