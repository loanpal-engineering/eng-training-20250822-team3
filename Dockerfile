FROM python:3.10-slim

# Install system dependencies for mysqlclient, git, and other tools
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    mariadb-client \
    coreutils \
    curl \
    git \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and set as working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

RUN pip install -r requirements.txt \
    && pip install bcrypt

# Copy startup.sh and init.sql; startup script will clone the code
COPY startup.sh .
COPY init.sql .

RUN useradd -m vulnleap

# Make the startup script executable
RUN chmod +x startup.sh

# Create code directory for repository cloning
RUN mkdir -p /app/team_code && chown -R vulnleap:vulnleap /app

# Switch to the vulnleap user
USER vulnleap

EXPOSE 5555

# Use the blue-green deployment startup script
CMD ["bash", "startup.sh"]