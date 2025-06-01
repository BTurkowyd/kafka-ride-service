FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole producers directory
COPY . .
