# 🧩 Планы модулей и ключевые сценарии

Ниже — полная карта каждого модуля: команды/колбэки, FSM-состояния, методы
репозитория, сценарии и генерируемые карточки. Ядро уже реализовано в коде;
звёздочкой ★ отмечено то, что можно углубить во вторую очередь.

---

## Ядро

### 1. Привязка пары (реализовано)
- Команды: `/start`, deep-link `/start {CODE}`.
- Колбэки: `bind:create`, `bind:enter`; FSM `BindStates.entering_code`.
- Репо: `CouplesRepository.create/join/get_by_invite/regenerate_invite`.
- QR генерится через `qrcode` (без внешних API).

### 2. Профиль пары (реализовано)
- `settings:profile` → PNG `profile_card.py`: имя, аватары, дни вместе,
  активные модули, код приглашения.

### 3. Настройки (реализовано)
- `settings:modules` + `settings:toggle:{module}` — вкл/выкл модулей (JSON).
- `settings:tz` (FSM `SettingsStates.timezone`), `settings:name` (FSM name).

### 4. Адаптивное главное меню (реализовано)
- `keyboards/main_menu.py` собирает Reply-меню из `couple.settings["modules"]`.

---

## Ежедневное

### 5. Напоминания (реализовано)
- FSM: `ReminderStates.text → datetime → repeat → notify → private`.
- Репо: `RemindersRepository.create/list_visible_for/mark_done/set_job_id/list_pending`.
- Сервис: `ReminderService.schedule/unschedule`, `fire_reminder`, `restore_reminders`.
- ★ Расширение: cron-правила (`weekdays`, `hourly`), отложенные уведомления.

### 6. Покупки (реализовано)
- Колбэки: `shop:add`, `shop:toggle:{id}`, `shop:del:{id}`.
- Репо: `ShoppingRepository.create/list_active/toggle/remove`.

### 7. Бюджет (реализовано)
- FSM: `BudgetStates.amount → comment(категория)`, `BudgetStates.limit`.
- Репо: `TransactionsRepository.create/total_since/totals_by_category/count_since`.
- Карточка: `budget_card.py` (итог месяца, лимит, топ категорий).
- ★ Расширение: бюджетные лимиты по категориям, CSV-импорт.

### 8. Настроение (реализовано)
- Колбэки `mood:1..5` / `mood:skip` / `mood:chart`; опрос `send_mood_poll` (cron каждый час).
- Алерт партнёру при 3 днях ≤ 2 подряд (`MoodService._low_streak`).
- График: `mood_chart.py` (matplotlib, тёмная тема).

### 9. Благодарности (реализовано)
- FSM: `GratitudeStates.text → visible`.
- Месячный отчёт: Jinja2 `gratitude_report.j2`.
- ★ Расширение: PNG-карточка месячного отчёта благодарностей.

---

## Календарь

### 10. События и даты (реализовано)
- FSM: `EventStates.title → date → notify`.
- Репо: `EventsRepository.create/list_for_couple`.

### 11. Календарь месяца (★ план)
- Генерировать PNG-календарь (Pillow) с подсветкой дат событий.
- Метод: `AnalyticsRepository.events_in_month(couple_id, year, month)`.

### 12. Капсулы времени (реализовано)
- FSM: `CapsuleStates.text → open_at` (добавить в `handlers/`).
- Репо: `CapsulesRepository.create/list_future/list_due/mark_opened`.
- Сервис: `CapsuleService.schedule_open`, `fire_capsule`, `restore_capsules`.

### 13. Обратный отсчёт (реализовано)
- `dates:countdown` — ближайшие события по числу дней.

---

## Романтика

### 14–18. Вопрос/челлендж дня, Правда-или-действие, сигналы (реализовано)
- Статические наборы в `handlers/romance.py`; челленджи хранятся в таблице `challenges`.
- ★ Расширение: привязка вопроса/челленджа к cron (выбор в 9:00, проверка 22:00).

### 19. Копилка воспоминаний (реализовано в `memories`)
- ★ Расширение: приём фото/видео/аудио, хранение media_url, карусель.

---

## Аналитика

### 20–23. Статистика, графики, отчёты (реализовано)
- `analytics:stats` → `stats_card.py`; `analytics:mood` → график;
  `analytics:wrapped` → `wrapped_card.py` + Jinja2-текст.
- ★ Расширение: видео-Wrapped (сборка кадров в mp4 через imageio/ffmpeg).

### 24. Экспорт (реализовано CSV, JSON)
- `AnalyticsService.export_transactions_csv/export_json`.
- ★ Расширение: PDF через ReportLab.

---

## Геймификация

### 25–27. Очки, уровни, дуэли (реализовано)
- `GamificationService.add_points/balance/level/check_achievements`.
- Дуэль КНБ vs бот (`games.py`); ★ двухсторонняя дуэль — через временное
  состояние в Redis (оба выбирают жест, потом сравнение).

### 28. Викторина «Как хорошо ты знаешь партнёра» (реализовано, статичная)
- ★ Персонализация: вопросы генерируются из ответов партнёра (его настроение,
  категории трат, воспоминания).

### 29. Совместные цели (реализовано, JSON в settings)
- ★ Вынести в отдельную таблицу `goals` с прогрессом и дедлайнами.

---

## Служебное

### 30–34. Админка, логи, бэкапы, миграции, health-check
- Админка: команда `/admin` для `settings.admins` (статистика пользователей, рассылка).
- Логи: structlog (stdout + JSON-файл). Бэкапы: `scripts/backup.sh` + профиль `backup`.
- Миграции: Alembic. Health-check: пинги в docker-compose.

---

## Ключевые сценарии (как реализованы)

1. **Привязка пары**: `/start` → «Создать пару» → код + QR + deep-link →
   партнёр шлёт код → `CouplesRepository.join`.
2. **Напоминание**: FSM → `RemindersRepository.create` → `ReminderService.schedule`
   (`job_id="reminder:{id}"`) → по таймеру `fire_reminder` → повтор или `done`.
3. **Опрос настроения 21:00**: cron каждый час → `send_mood_poll` фильтрует по
   TZ и часу → инлайн-опрос → запись в `moods`.
4. **Челлендж дня**: `romance:challenge` создаёт/читает `challenges` за сегодня,
   `challenge:done` отмечает выполнение, счёт пары.
5. **Карточка статистики**: `CardService.stats_card` собирает агрегаты и в потоке
   рендерит `stats_card.py`.
6. **Годовой Wrapped**: `CardService.wrapped_card` + `AnalyticsService.wrapped_text`
   (PNG + текст); ★ видео — отдельно.
7. **Капсула времени**: создание → `CapsuleService.schedule_open` → в дату
   `fire_capsule` шлёт текст обоим.
8. **Алерт партнёру**: `MoodService.save_mood` → если 3 дня ≤ 2 → `mood_alert_text`.
