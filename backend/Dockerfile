# ==========================================
# Stage 1: Builder (Build dependencies)
# ==========================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Base Runtime (Clean & Secure)
# ==========================================
FROM python:3.11-slim AS runner-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -M appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup ./app ./app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Native Python Healthcheck (no curl required)
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# ==========================================
# Stage 3: Development Target
# ==========================================
FROM runner-base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==========================================
# Stage 4: Production Target (Default)
# ==========================================
FROM runner-base AS production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
