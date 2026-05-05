FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install runtime deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY backend /app/backend
COPY api /app/api

WORKDIR /app/backend
ENV PYTHONPATH=/app

# Expose a default port; Render will provide $PORT at runtime
EXPOSE 10000

# Use shell form so $PORT can be honored when provided by Render
CMD ["sh", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
FROM python:3.12-slim

WORKDIR /app

# system deps for compiled wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE ${PORT}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
