# ─────────────────────────────────────────────────────
# STAGE 1 — Install Python dependencies
# We use a full image here just to install packages.
# ─────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy only requirements first (Docker layer cache trick)
# If requirements.txt hasn't changed, this layer is reused
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────
# STAGE 2 — Lean runtime image
# Only copy what we need — no pip, no build tools
# ─────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from stage 1
COPY --from=builder /install /usr/local

# Copy our application code
COPY app.py .

# Run as non-root user (security best practice)
RUN useradd -m appuser
USER appuser

# Tell Docker which port our app uses
EXPOSE 5000

# Health check — Docker will mark container unhealthy if this fails
HEALTHCHECK --interval=20s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Start the app with gunicorn (production-ready server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
