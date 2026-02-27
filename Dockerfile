# ── Stage 1: Сборка React Mini App ───────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --frozen-lockfile || npm install
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python-бэкенд ───────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники бота
COPY backend/ backend/

# Копируем собранный фронтенд (раздаётся через FastAPI)
COPY --from=frontend-builder /frontend/dist ./static

CMD ["python", "-m", "backend.main"]
