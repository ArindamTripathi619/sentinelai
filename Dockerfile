FROM node:20-alpine AS frontend-build
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN VITE_SUPABASE_URL=${VITE_SUPABASE_URL} VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY} npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend

# Install backend runtime dependencies.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source and built frontend assets.
COPY backend /app/backend
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

ENV PYTHONPATH=/app/backend
EXPOSE 10000
CMD ["sh", "-lc", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers"]