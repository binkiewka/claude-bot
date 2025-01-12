FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/opt/claude-bot:${PYTHONPATH}"

# Set work directory
WORKDIR /opt/claude-bot

# Copy entire project
COPY . /opt/claude-bot

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint executable
RUN chmod +x /opt/claude-bot/entrypoint.sh

# Use non-root user
RUN useradd -m botuser && \
    chown -R botuser:botuser /opt/claude-bot
USER botuser

# Entrypoint
ENTRYPOINT ["/opt/claude-bot/entrypoint.sh"]
