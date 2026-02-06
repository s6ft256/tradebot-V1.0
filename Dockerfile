# Dockerfile for 24/7 Trading Bot
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic httpx ccxt sqlalchemy asyncpg \
    cryptography python-dotenv orjson numpy

# Copy source code
COPY src/ ./src/

# Create data directories
RUN mkdir -p data logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PAPER_TRADING=true
ENV LOG_LEVEL=INFO

# Run the bot
WORKDIR /app/src
CMD ["python", "main.py"]
