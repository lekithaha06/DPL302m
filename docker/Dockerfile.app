# Service giao dien (Gradio). Build tu thu muc goc cua repo:
#   docker build -f docker/Dockerfile.app -t asr-vi-en-app .
#
# Service nay KHONG nap model: no goi service API qua HTTP (API_URL).
# Nho vay anh giao dien nhe (khong co torch) va hai service scale doc lap duoc.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CHE_DO=api

WORKDIR /app

# Chi cai thu vien giao dien, khong cai torch/transformers
COPY docker/requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY src/audio.py ./src/audio.py
COPY src/truc_tiep.py ./src/truc_tiep.py
COPY src/__init__.py ./src/__init__.py
COPY app/ ./app/

RUN useradd --create-home --uid 10002 ungdung && chown -R ungdung:ungdung /app
USER ungdung

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:7860/ || exit 1

CMD ["python", "app/gradio_app.py"]
