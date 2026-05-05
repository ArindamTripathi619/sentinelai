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
