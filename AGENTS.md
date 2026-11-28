# AGENTS.md — Bonch PT (project guide for AI agents)

## Purpose
This repository contains a set of Python services (Dockerized) related to schedule collection, schedule access (Telegram inline bot + CLI/TUI), and attendance automation for students/staff context around “Bonch” (SPbSUT). It also includes an experimental `src/` HTTP server stub and `depricated/` legacy code.

## Repo layout (high level)
- `docker-compose.yml` — orchestrates services: `autocollector`, `schedule`, and `redis` (service `autocheck` is commented out).
- Каждый сервис (`autocollector/`, `schedule/`, `autocheck/`) имеет свой `requirements.txt`; общего корневого файла нет.
- `autocollector/` — fetches schedules from SUT website and stores parsed entries into Redis.
  - `main.py` — `Bonch` scraper + scheduling/daemon loop.
  - `repository.py` — Redis repository (`RedisDB`) used by collector.
  - `Dockerfile` — builds collector image.
- `autocheck/` — Playwright-based automation to “start lesson” in LK SUT cabinet (attendance helper).
  - `main.py` — login, navigation, periodic checks, waits between pairs.
  - `repository.py` — Redis reads (`RedisDB`) for schedule windows.
  - `Dockerfile` — uses `mcr.microsoft.com/playwright/python:v1.56.0-noble`, installs from `autocheck/requirements.txt`, runs `python main.py`.
- `schedule/` — schedule access utilities:
  - `repository.py` — `Schedule` (data access from Redis), returns `Lesson` models.
  - `models.py` — dataclasses (`Lesson`).
  - `formatters.py` — Telegram HTML formatters: `format_schedule_group`, `format_schedule_teacher`, `format_schedule_protection` (placeholder).
  - `tui.py` — CLI/TUI entrypoint (`python tui.py`).
  - `telegram_bot.py` — aiogram inline bot (teacher search, uses formatters).
  - `Dockerfile` — runs `python telegram_bot.py`.
- `src/` — experimental FastAPI stub (`http_server.py`) + PostgreSQL repo (`repository.py`) + empty `schemas.py`. Not wired in `docker-compose.yml`.
- `depricated/` — legacy/unused code (ignored for active development unless asked).
- `.env` (not committed; see `.gitignore`) — expected for runtime config (secrets/URLs). Common vars used in code:
  - `REDIS_URL` (e.g. `redis://redis:6379/0` in Docker, `redis://localhost:6379/0` locally)
  - `BOT_TOKEN` (Telegram bot)
  - `LOGIN`, `PASSWORD` (LK SUT credentials for `autocheck`)
  - `DB_PASSWORD`/DB settings appear in `src/repository.py` defaults but `src` is not the main path today.

## Data flow (current)
1. `autocollector` scrapes SUT schedule pages (HTML via `httpx` + `BeautifulSoup`), parses groups and weekly lessons, writes to Redis via `autocollector.repository.RedisDB`.
2. Redis keys (observed):
   - `schedule:{sect}:{YYYY-MM-DD}:{pair}` → JSON payload (date, pair, subject, auditorium, teacher, lesson_type, sect)
   - `schedule:dates:{sect}` → sorted set of date ordinals (used for indexing)
3. `schedule` (CLI/TUI or Telegram inline bot) reads from Redis via `schedule/schedule.py` (`Schedule`), filtering/searching in-memory after scans.
4. `autocheck` reads from Redis via `autocheck.repository.RedisDB` to decide whether to act today or wait until next scheduled date; then uses Playwright to log into LK and click “Начать занятие” buttons.

## How to run (typical)
- Docker (recommended for integrated stack): from repo root
  - `docker compose up --build`
  - Notes: `autocheck` service is commented out in `docker-compose.yml`; enable it if you need attendance automation. `schedule` container runs the Telegram bot (`telegram_bot.py`). Redis is exposed on `127.0.0.1:6379` in compose.
- Local (examples):
  - Ensure Redis running and `REDIS_URL` set.
  - Collector: `python autocollector/main.py` (requires network access to SUT site).
  - Schedule CLI/TUI: `python schedule/tui.py`.
  - Telegram bot: `python schedule/telegram_bot.py` (requires `BOT_TOKEN`; uses a SOCKS5 proxy configured in code: `socks5://127.0.0.1:2080` — adjust if not needed).
  - Autocheck: `python autocheck/main.py` (requires Playwright browsers installed; Docker image already has them). Also needs `LOGIN`, `PASSWORD`, `REDIS_URL`.

## Important conventions for AI agents
- **Language in code/comments/UI**: Russian strings/comments appear throughout (logs, prompts, messages). Preserve meaning/style when editing.
- **Redis is the shared store** for schedule data between collector and readers (`autocollector` writes, `schedule`/`autocheck` read). Keep key formats consistent:
  - Key: `schedule:{sect}:{date}:{pair}`
  - Date format: `YYYY-MM-DD`; pair is string (`"1"`..`"7"` in collector context; `autocheck` expects pairs in `TIME_SLOTS` keys `"1".."6"`).
- **Time zones/naive datetimes**: code uses local/naive `datetime` in several places (`autocheck` normalizes datetimes). Be careful when changing time logic.
- **Network scraping fragility**: `autocollector` depends on SUT website HTML structure and classes (`vt256`, `rasp-day*`, `vt240`, etc.). Changes on the website may break parsing.
- **Telegram bot proxy**: `schedule/telegram_bot.py` hardcodes a SOCKS5 proxy (`127.0.0.1:2080`). If running in another environment, this may need to be made configurable.
- **Dockerfile differences**:
  - `autocheck/Dockerfile` copies `autocheck/requirements.txt` into `/app`, installs from it, then copies `autocheck/.` into `/app`.
  - `schedule/Dockerfile` copies `schedule/` into `/app` and runs `pip install -r requirements.txt` from that dir context in the Dockerfile as written (check build context in `docker-compose.yml`: build context is repo root for services; verify paths before editing Dockerfiles).
- **Do not commit secrets**: `.env` is gitignored. Never hardcode tokens/passwords.
- **`src/` is a stub**: FastAPI app endpoints return static `{"status":"live"}` placeholders; PostgreSQL code is present but not integrated into compose/services. Treat as WIP/experimental unless asked to implement.
- **`depricated/`**: ignore unless explicitly asked.

## Safe edit tips
- Prefer minimal, targeted changes consistent with existing style (async/await, `python-dotenv`, `redis.asyncio`).
- If changing schedule key schema or JSON shape, update all readers/writers: `autocollector/repository.py`, `schedule/repository.py`, `autocheck/repository.py`.
- When modifying scraping/parsing in `autocollector/main.py`, validate against current site structure carefully (selectors/classes).
- For Docker changes, keep `docker-compose.yml` build contexts and Dockerfile `COPY` paths consistent (compose sets context `.` with service-specific Dockerfile paths).
