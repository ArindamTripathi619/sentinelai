FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install runtime dependencies only.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the backend source tree so module imports resolve cleanly.
COPY backend /app/backend

WORKDIR /app/backend
ENV PYTHONPATH=/app

# Render injects PORT at runtime; default is safe for local container runs.
EXPOSE 10000
CMD ["sh", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]
