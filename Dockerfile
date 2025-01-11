# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Avoid __pycache__
ENV PYTHONDONTWRITEBYTECODE=1
ENV REDIS_URL=redis://localhost:6379/0

# Install system dependencies, Redis and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    redis-server && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the ports for FastHTML and Redis
EXPOSE 8000 6379

# Create a startup script
RUN echo '#!/bin/bash\nservice redis-server start\nuvicorn main:app --host 0.0.0.0 --port 8000' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the startup script when the container launches
CMD ["/app/start.sh"]