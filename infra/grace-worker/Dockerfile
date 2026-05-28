FROM python:3.12-slim

ARG ASTRO_UID=1001
ARG ASTRO_GID=1003

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/opt/astro-project \
    HOME=/home/astro \
    CODEX_HOME=/home/astro/.codex

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        jq \
        libcairo2 \
        libffi8 \
        libfribidi0 \
        libgdk-pixbuf-2.0-0 \
        libharfbuzz0b \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        nodejs \
        npm \
        openssh-client \
        tini \
    && npm install -g @openai/codex @google/gemini-cli \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${ASTRO_GID}" astro \
    && useradd --uid "${ASTRO_UID}" --gid "${ASTRO_GID}" --home-dir /home/astro --create-home --shell /bin/bash astro

WORKDIR /opt/astro-project

COPY infra/grace-worker/requirements.txt /tmp/grace-worker-requirements.txt
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r /tmp/grace-worker-requirements.txt

COPY infra/grace-worker/entrypoint.sh /usr/local/bin/grace-worker-entrypoint
RUN chmod +x /usr/local/bin/grace-worker-entrypoint \
    && chown -R astro:astro /home/astro

USER astro

ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/usr/local/bin/grace-worker-entrypoint"]
CMD ["worker"]
