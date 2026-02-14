# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-alpine

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for potential python packages
# (e.g., git, gcc, libmariadb-dev if needed for some mysql drivers)
RUN apk add --no-cache \
    gcc \
    mariadb-dev \
    ffmpeg \
    && rm -rf /var/lib/apk/cache

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install -q --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create a non-root user for security
RUN addgroup -S alya && adduser -S alya -G alya

# Set ownership of the application directory to the non-root user
RUN mkdir -p /app/logs /app/tmp && chown -R alya:alya /app && chmod 1777 /app/tmp

ENV TMPDIR=/app/tmp

# Switch to non-root user
USER alya

# Command to run the bot
CMD ["python", "run.py"]
