FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Copy specific requirements for the bot
COPY bot/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ffmpeg libgomp1 && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy backend for shared models
COPY backend/app /app/backend/app
COPY backend/app/base.py /app/backend/app/base.py

# Copy bot code

COPY bot/app /app/app



CMD ["python", "-m", "app.main"]
