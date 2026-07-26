FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p output cache backups

# Expose port 5000 as used by the application
EXPOSE 5000

# Set environment variables
ENV FLASK_PORT=5000
ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1

# Initialize database and start app
CMD ["sh", "-c", "python main.py migrate-db && python -m flask run --host=0.0.0.0 --port=$FLASK_PORT"]