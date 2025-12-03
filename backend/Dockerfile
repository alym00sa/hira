# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories
RUN mkdir -p data/vectorstore data/uploads

# Expose ports (FastAPI + WebSocket)
EXPOSE 8000 8765

# Run both FastAPI and WebSocket relay servers
CMD ["python", "run_servers.py"]
