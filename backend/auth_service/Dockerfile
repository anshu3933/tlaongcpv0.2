FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy common package first
COPY backend/common /app/common

# Copy service code and requirements
COPY backend/auth_service/requirements.txt .
COPY backend/auth_service/src /app/src
COPY backend/auth_service/scripts /app/scripts
COPY backend/auth_service/alembic.ini /app/alembic.ini
COPY backend/auth_service/src/migrations/script.py.mako /app/src/migrations/script.py.mako

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p src/migrations/versions

# Set PYTHONPATH to include both common and src directories
ENV PYTHONPATH=/app:/app/common/src

# Run migrations and start the application
CMD python scripts/run_migrations.py && uvicorn src.main:app --host 0.0.0.0 --port 8003
