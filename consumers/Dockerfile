FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY consumers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole consumers directory
COPY . .

# Optional: set environment variables here or use Docker Compose
# ENV POSTGRES_USER=kafka_user ...
# CMD ["python", "-m", "modules.consumers.consumer_ride_requested"]
