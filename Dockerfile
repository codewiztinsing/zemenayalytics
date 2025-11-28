FROM python:3.11-slim

WORKDIR /app

# Upgrade pip, setuptools, and wheel
RUN pip install --upgrade pip setuptools wheel

# Set pip timeout
ENV PIP_DEFAULT_TIMEOUT=300

# Copy requirements and install script first for better Docker layer caching
COPY requirements/ /app/requirements/
COPY scripts/install_requirements.sh /app/scripts/

# Make install script executable
RUN chmod +x /app/scripts/install_requirements.sh

# Install Python dependencies with retry logic
RUN /app/scripts/install_requirements.sh requirements/prod.txt

# Copy the rest of the application
COPY . /app

# Make scripts executable
RUN chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
