# 🚀 Полный гайд по запуску Couple Bot

Пошагово от нуля до работающего бота — двумя способами:
**Вариант А** (быстро, локально, SQLite) и **Вариант Б** (полный стек Docker).

---

## 0. Что нужно

| Что | Зачем |
|---|---|
| Аккаунт Telegram | создать бота и тестировать |
| Токен бота от @BotFather | обязателен |
| Python 3.11+ (вариант А) | локальный запуск |
| Docker + Docker Compose (вариант Б) | полный стек |

---

## 1. Получаем токен бота

1. В Telegram откройте **@BotFather**.
2. Отправьте команду `/newbot`.
3. Введите **имя** бота (например, `Наша Пара`) и **username** (например, `our_couple_bot` — должен заканчиваться на `bot`).
4. BotFather пришлёт сообщение со строкой вида:
   ```
   123456789:AAH...длинная строка...
   ```
   Это и есть токен. Сохраните его.

---

## 2. Вариант А — быстрый локальный запуск (SQLite, без Docker)

Самый простой способ проверить бота. Не нужны PostgreSQL и Redis — бот создаст
локальную БД `dev.db` сам.

### Windows (PowerShell)
```powershell
cd couple_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

### Linux / macOS
```bash
cd couple_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
```

### Что вписать в `.env`
```ini
COUPLE_BOT_BOT_TOKEN=123456789:AAH...ваш_токен
# ВАЖНО: переключить на SQLite, иначе бот полезет в PostgreSQL
COUPLE_BOT_POSTGRES_DSN=sqlite+aiosqlite:///./dev.db
```

### Запуск
```bash
python -m main
```
Увидите логи, бот начнёт слушать обновления. Таблицы создадутся автоматически
(в режиме SQLite).

> ⚠️ Миграции Alembic для SQLite **не запускайте** — они написаны под PostgreSQL
> (тип JSONB). Для SQLite используется автогенерация таблиц в `main.py`.

---

## 3. Вариант Б — полный стек (Docker: PostgreSQL + Redis + бот)

Это «продакшн»-режим. Работает и локально, и на VPS.

```bash
cd couple_bot
cp .env.example .env
# отредактируйте .env: BOT_TOKEN обязателен, остальное можно оставить
```

```bash
# 1) Базы данных
docker compose up -d postgres redis

# 2) Миграции (создать таблицы в PostgreSQL)
docker compose run --rm bot alembic upgrade head

# 3) Сам бот
docker compose up -d --build bot

# 4) Смотрим логи
docker compose logs -f bot
```

Остановка:
```bash
docker compose down          # остановить
docker compose down -v       # остановить и удалить данные БД (осторожно!)
```

---

## 4. Проверяем, что всё работает

1. Откройте бота в Telegram → `/start`.
2. Нажмите **«Создать пару»** → бот пришлёт код + QR + ссылку.
3. Со второго аккаунта (или телефона партнёра) откройте бота → `/start` →
   **«Ввести код»** → вставьте код.
4. Проверьте модули из меню:
   - `🔔 Напоминания` → создать напоминание (например, через 1 минуту) — придёт уведомление;
   - `🌤️ Настроение` → отметить настроение 1–5;
   - `💳 Бюджет` → добавить трату → «Отчёт месяца» покажет карточку PNG;
   - `📊 Статистика` → «Карточка пары» сгенерирует красивую картинку.

---

## 5. Частые ошибки

| Симптом | Причина / решение |
|---|---|
| `Unauthorized` / `401` в логах | Неверный токен. Проверьте `.env`. |
| `Connection refused ... 5432` | Бот в режиме PostgreSQL, а PostgreSQL не запущен. Либо поднимите `docker compose up -d postgres`, либо переключите `.env` на SQLite. |
| `No module named aiogram` | Зависимости не установлены: `pip install -r requirements.txt`. |
| Не приходят напоминания | Планировщик работает только пока запущен процесс бота — держите `python -m main` / контейнер запущенным. Для 24/7 нужен VPS (см. ниже). |
| `alembic` падает на SQLite | Так и должно быть — для SQLite не нужен alembic, таблицы создаёт `main.py`. |
| Кнопки без цветов | Нужен `aiogram>=3.20` и свежая версия Telegram-клиента. |

---

## 6. Запуск на VPS (чтобы работало 24/7)

Чтобы бот работал даже при выключенном вашем компьютере — перенесите его на сервер.

```bash
# на сервере (Ubuntu/Debian):
curl -fsSL https://get.docker.com | sh

# загрузить проект (один из способов):
git clone <ваш_репозиторий> /opt/couple_bot      # или
scp -r couple_bot root@IP:/opt/couple_bot

cd /opt/couple_bot
cp .env.example .env && nano .env                 # BOT_TOKEN

docker compose up -d postgres redis
docker compose run --rm bot alembic upgrade head
docker compose up -d --build bot
```

Контейнеры настроены с `restart: unless-stopped` — переживут перезагрузку сервера.
Бэкапы включаются отдельно:
```bash
docker compose --profile backup up -d minio backup
```
