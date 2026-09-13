# Stage 1: build React frontend (Vite + TSX) — outputs to frontend/dist
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + serving built frontend on same port (5000)
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

# Bring in built frontend (served by Flask at /app on same port 5000)
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

# Create cache directories
RUN mkdir -p cache/api_responses cache/fastf1_cache cache/model_cache frontend/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "main.py"]
