# Stage 1: build React frontend (Vite + TSX) — outputs to frontend/dist
# NOTE: for decoupled deploys (Vercel frontend + Render API) this stage is skipped;
# frontend is deployed separately to static host. This stage remains for single-image
# legacy/bundled mode only. Backend is pure JSON on 5000 (see decoupled docs).
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend (API only, 5000 pure JSON). Frontend not served from here in decoupled mode.
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies.
# gcc/g++: build a couple of ML wheels that don't ship manylinux binaries.
# curl: container HEALTHCHECK.
# libpango/libcairo/libgdk-pixbuf/shared-mime-info/fonts-liberation: WeasyPrint
#   (reports/pdf_generator.py) needs these at *runtime*, not just build time —
#   without them, PDF export 500s the first time anyone requests one.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (backend + frontend sources, but dist will be overwritten)
COPY . .

# Bring in built frontend artifact (only used if serving bundled legacy mode)
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

# Create cache directories
RUN mkdir -p cache/api_responses cache/fastf1_cache cache/model_cache frontend/dist backend/app/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend.main
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "backend/main.py"]
