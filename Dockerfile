# ============================================================
# saham-indonesia — Docker image
# ============================================================
# Multi-stage build: slim Python image with only runtime deps.
#
# Usage:
#   docker build -t saham-indonesia .
#   docker run -p 8501:8501 --env-file .env saham-indonesia
# ============================================================

FROM python:3.11-slim AS base

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (for lxml, httpx, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libxml2-dev \
        libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependencies stage ----
FROM base AS deps

COPY pyproject.toml ./

# Install Python dependencies (including dashboard extras)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        pandas>=2.1 \
        numpy>=1.26 \
        pydantic>=2.5 \
        pydantic-settings>=2.1 \
        yfinance>=0.2.40 \
        httpx>=0.27 \
        beautifulsoup4>=4.12 \
        lxml>=5.0 \
        typer>=0.12 \
        rich>=13.7 \
        python-dateutil>=2.9 \
        tenacity>=8.2 \
        cachetools>=5.3 \
        streamlit>=1.35 \
        plotly>=5.22 \
        websockets>=12.0

# ---- Final stage ----
FROM deps AS final

# Copy source code
COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY .env.example ./.env.example

# Install the package itself
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --no-deps -e .

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import saham_id; print('ok')" || exit 1

# Default: run dashboard
CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
