# ── Build Stage ───────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install compiler dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a wheels directory
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Runtime Stage ─────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN groupadd -g 10001 examshield && \
    useradd -u 10000 -g examshield -s /bin/bash -m examshield && \
    chown -R examshield:examshield /app

USER examshield

# Copy application files
COPY --chown=examshield:examshield alembic.ini alembic.ini
COPY --chown=examshield:examshield alembic/ alembic/
COPY --chown=examshield:examshield app/ app/

# Environment configurations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
