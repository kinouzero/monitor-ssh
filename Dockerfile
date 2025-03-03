# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install required dependencies
RUN apt-get update && apt-get install -y \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make the script executable
RUN chmod +x /app/main.py

# Set environment variables directly
# These will be the defaults if not overridden
ENV NTFY_TOPIC="https://ntfy.sh/topic"
ENV NTFY_TOKEN=""
ENV MONITOR_EVENTS="all"

# Command to run the script when the container starts
CMD ["python", "/app/main.py"]
