#!/bin/sh
# Ежедневный бэкап PostgreSQL в S3-совместимое хранилище (MinIO / любой S3).
# Запускается cron'ом в контейнере backup (см. docker-compose.yml).
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILE="couple_bot_${TIMESTAMP}.sql.gz"

echo "[backup] dumping database..."
pg_dump -h postgres -U couple couple_bot | gzip > "/tmp/${FILE}"

echo "[backup] configuring S3 client..."
mc alias set backup "${S3_ENDPOINT}" "${S3_ACCESS_KEY}" "${S3_SECRET_KEY}" >/dev/null
mc mb -p "backup/${S3_BUCKET}" >/dev/null 2>&1 || true

echo "[backup] uploading ${FILE}..."
mc cp "/tmp/${FILE}" "backup/${S3_BUCKET}/${FILE}"

# Ротация: храним последние 14 дней
mc rm --recursive --force --older-than 14d "backup/${S3_BUCKET}/" >/dev/null 2>&1 || true

echo "[backup] done: ${FILE}"
