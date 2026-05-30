# Monolito: build Angular + runtime FastAPI/Uvicorn sirviendo el SPA en el mismo puerto.
# Build context: carpeta padre "ERP Educativo" (ver docker-compose.yml).
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build
COPY mi-cole-project/frontend/package.json mi-cole-project/frontend/package-lock.json ./
RUN npm ci
COPY mi-cole-project/frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY mi-cole-project/backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY mi-cole-project/backend/app /app/app
COPY mi-cole-docs/sql /app/sql
COPY --from=frontend-build /build/dist/mi-cole/browser /app/static/browser

ENV STATIC_ROOT=/app/static/browser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://127.0.0.1:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
