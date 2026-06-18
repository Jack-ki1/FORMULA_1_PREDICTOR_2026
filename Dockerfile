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
RUN mkdir -p output cache .fastf1_cache backups

# Expose port (Hugging Face uses 7860)
EXPOSE 7860

# Set environment variables
ENV FLASK_PORT=7860
ENV FLASK_DEBUG=false
ENV PYTHONUNBUFFERED=1

# Initialize database and start app
CMD ["sh", "-c", "python main.py migrate-db && python dashboard/app.py"]
