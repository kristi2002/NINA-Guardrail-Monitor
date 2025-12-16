FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY Guardrail-Strategy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory (needed for imports)
COPY shared /app/shared

# Copy application code
COPY Guardrail-Strategy /app

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Health check - verify HTTP status code and exit with proper code
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests, sys; r = requests.get('http://localhost:5001/health', timeout=5); sys.exit(0 if r.status_code == 200 else 1)" || exit 1

# Run the application
# Use Gunicorn for production, Flask dev server for development
# Set USE_GUNICORN=true in environment to use Gunicorn
CMD ["sh", "-c", "if [ \"$USE_GUNICORN\" = \"true\" ]; then gunicorn -c gunicorn_config.py 'app:app'; else python app.py; fi"]

