# ── Stage 1: Build React frontend ─────────────────────────────────────────
FROM node:22-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python backend + compiled frontend ────────────────────────────
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY --from=frontend-build /frontend/dist ./frontend/dist

EXPOSE 8080

# Run migrations then start the server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]