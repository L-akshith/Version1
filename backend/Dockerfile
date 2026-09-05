# ── Build Stage ───────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python packages into a location shared with the runtime user
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime Stage ─────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages and executables
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd -g 10001 examshield && \
    useradd -u 10000 -g examshield -s /bin/bash -m examshield && \
    chown -R examshield:examshield /app

USER examshield

# Copy application files
COPY --chown=examshield:examshield alembic.ini alembic.ini
COPY --chown=examshield:examshield alembic/ alembic/
COPY --chown=examshield:examshield app/ app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]