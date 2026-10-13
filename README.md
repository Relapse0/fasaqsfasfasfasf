# 💑 Couple Bot — личная операционная система для двоих

Премиальный Telegram-бот для пары: напоминания, покупки, бюджет, настроение,
даты, благодарности, романтика, воспоминания, статистика и геймификация —
всё с красивыми PNG-карточками и целостным визуальным стилем.

Стек: **Python 3.11+ · aiogram 3 · PostgreSQL + asyncpg · Redis · APScheduler ·
Pillow · matplotlib · Jinja2 · structlog · Alembic · Docker**.

---

## 1. Архитектура

```
Telegram UI  →  Middlewares (auth/throttling/i18n/logging)
            →  Handlers (роутер на модуль, FSM)
            →  Services (бизнес-логика)
            →  Repositories (SQL поверх SQLAlchemy async)
            →  PostgreSQL (asyncpg)  +  Redis (FSM/кэш/антиспам)

Дополнительно:
  Scheduler (APScheduler) — напоминания, опрос настроения, капсулы
  Presentation (cards/renderers) — PNG-карточки и тексты (Jinja2)
  Analytics / Gamification — агрегаты и очки/уровни/достижения
```

Ключевые решения:
- **Контекст пары** — всё привязано к `couple_id`; приватность через `visible_to_partner`.
- **Модульность** — каждый модуль включается/выключается (настройки в `couples.settings` JSON),
  меню собирается адаптивно.
- **Идемпотентный планировщик** — `job_id = "reminder:{id}"` в БД; после рестарта
  джобы восстанавливаются из БД (а не из памяти).
- **Edit-in-place** — один экран меняется через `edit_message_text`, без спама сообщениями.
- **SQLite для разработки, PostgreSQL для прода** — один и тот же код.

## 2. Структура проекта

```
couple_bot/
├── main.py                  # точка входа: собирает bot/dispatcher/мидлвари/роутеры
├── config.py                # pydantic-settings (env: COUPLE_BOT_*)
├── requirements.txt
├── .env.example             # шаблон переменных окружения
├── Dockerfile               # python:3.11-slim + шрифты
├── docker-compose.yml       # postgres + redis + bot (+ minio/backup в профиле backup)
├── alembic.ini
├── alembic/
│   ├── env.py               # async-движок, читает COUPLE_BOT_POSTGRES_DSN
│   ├── script.py.mako
│   └── versions/0001_initial.py   # полная схема
├── database/
│   ├── db.py                # init_db / get_session / create_all
│   ├── models.py            # 13 таблиц (SQLAlchemy 2.0)
│   ├── redis.py             # Redis-клиент + кэш-хелперы
│   └── repositories/        # base, users, couples, reminders, transactions,
│                            # shopping, moods, events, challenges, gratitude,
│                            # memories, capsules, achievements, analytics
├── handlers/                # роутер на модуль (start, menu, reminders, budget,
│   │                        # shopping, mood, dates, gratitude, romance, memories,
│   │                        # analytics, achievements, games, settings)
├── services/
│   ├── context.py           # ссылка на Bot для планировщика
│   ├── reminder_service.py  # планирование/повтор напоминаний
│   ├── mood_service.py      # настроение + алерт партнёру + опрос 21:00
│   ├── budget_service.py    # траты, лимиты, сводки
│   ├── analytics_service.py # отчёты, экспорт CSV/JSON
│   ├── gamification_service.py  # очки, уровни, достижения
│   ├── card_service.py      # фасад генерации PNG (в потоках)
│   └── capsule_service.py   # капсулы времени
├── presentation/
│   ├── cards/               # base (палитра/шрифты), stats_card, budget_card,
│   │                        # mood_chart (matplotlib), profile_card, wrapped_card
│   ├── renderers/jinja.py   # рендер текстов
│   └── templates/           # wrapped_text.j2, gratitude_report.j2
├── keyboards/
│   ├── main_menu.py         # адаптивное Reply-меню (2 кнопки в ряд)
│   ├── inline.py            # инлайн-клавиатуры со стилями
│   └── builders.py          # пагинация, сетки
├── middlewares/             # auth, throttling, i18n, logging
├── scheduler/
│   ├── scheduler.py         # единственный AsyncIOScheduler
│   └── jobs.py              # start/stop + восстановление задач
├── utils/                   # texts, emoji, validators, helpers, qr, logger
├── assets/fonts|icons|backgrounds/   # ресурсы (шрифты кладутся сюда)
└── scripts/backup.sh        # pg_dump -> S3 (MinIO)
```

## 3. Быстрый старт (локальная разработка)

```bash
cd couple_bot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # впишите BOT_TOKEN
# Для быстрой разработки без Redis/Postgres — SQLite:
#   в .env: COUPLE_BOT_POSTGRES_DSN=sqlite+aiosqlite:///./dev.db

python -m main              # long-polling; таблицы создадутся сами (SQLite)
```

## 4. Запуск через Docker (продакшн-стек)

```bash
cp .env.example .env        # впишите BOT_TOKEN (и пароли Postgres при желании)
docker compose up -d --build postgres redis
docker compose run --rm bot alembic upgrade head   # накатить миграции
docker compose up -d --build bot
docker compose logs -f bot
```

Бэкапы (опционально, MinIO + cron):
```bash
docker compose --profile backup up -d minio backup
```

## 5. Миграции (Alembic)

```bash
docker compose run --rm bot alembic upgrade head          # применить
docker compose run --rm bot alembic revision --autogenerate -m "описание"  # новая
docker compose run --rm bot alembic downgrade -1           # откат
```

## 6. Деплой на VPS

1. Установите Docker + docker compose.
2. `git clone <репозиторий> && cd couple_bot`.
3. `cp .env.example .env`, заполните `BOT_TOKEN`, смените пароли БД.
4. `docker compose up -d --build`, затем `docker compose run --rm bot alembic upgrade head`.
5. Для webhook (за nginx/caddy): в `.env` поставьте
   `COUPLE_BOT_WEBHOOK_ENABLED=true` и `COUPLE_BOT_WEBHOOK_URL=https://your.domain`,
   пробросьте порт `8443`. Для двух пользователей long-polling тоже подходит.
6. Автозапуск: `docker compose up -d` уже использует `restart: unless-stopped`.

## 7. Бэкапы

- Профиль `backup` в docker-compose поднимает MinIO и cron, который в 03:00
  делает `pg_dump | gzip` и кладёт в S3-бакет с ротацией 14 дней.
- Восстановление:
  ```bash
  gunzip -c couple_bot_20250101_030000.sql.gz | docker compose exec -T postgres psql -U couple couple_bot
  ```

## 8. Мониторинг и логи

- Логи: `docker compose logs -f bot`; файл `logs/couple_bot.log` (JSON) — том `./logs`.
- Health-check: PostgreSQL и Redis пингуются в compose; бот отвечает на `/start`.
- structlog пишет человекочитаемо в stdout и JSON в файл.
- Для продвинутого мониторинга добавьте Prometheus/Grafana или Sentry (опционально).

## 9. Дизайн, модули, план развития

- 🎨 [Дизайн-гайд](docs/DESIGN_GUIDE.md) — палитра эмодзи, шрифты, цвета кнопок, примеры экранов.
- 🧩 [Планы модулей и сценарии](docs/MODULES_PLAN.md) — команды, FSM, репозитории, карточки.
- ✅ [Чек-лист развития](docs/CHECKLIST.md) — первая неделя / месяц / квартал.
