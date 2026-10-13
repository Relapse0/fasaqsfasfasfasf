# ── Сборка образа бота ─────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Системные зависимости: шрифты (для Pillow/matplotlib) и libgomp (matplotlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-dejavu-core \
        libgomp1 \
        libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала зависимости — так слой кэшируется
COPY requirements.txt .
RUN pip install -r requirements.txt

# Код приложения
COPY . .

# Каталоги для логов и сгенерированных файлов
RUN mkdir -p logs generated

EXPOSE 8443

# Точка входа
CMD ["python", "-m", "main"]
