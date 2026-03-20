FROM python:3.12-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /build/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && pip install --upgrade pip \
    && pip install --prefix=/install -r /build/requirements.txt \
    && apt-get purge -y --auto-remove build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system app \
    && adduser --system --ingroup app --home /app app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        nodejs \
        npm \
        libcairo2 \
        libffi8 \
        libharfbuzz0b \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libfribidi0 \
        fonts-dejavu-core \
        fonts-noto-color-emoji \
        fonts-symbola \
    && (apt-get install -y --no-install-recommends libgdk-pixbuf2.0-0 \
        || apt-get install -y --no-install-recommends libgdk-pixbuf-xlib-2.0-0) \
    && npm install -g @google/gemini-cli @openai/codex \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app

COPY --from=builder /install /usr/local
COPY backend /app/backend
COPY stellium_engine.py /app/stellium_engine.py

RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
