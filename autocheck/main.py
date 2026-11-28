import asyncio
import logging
import os
import random
from datetime import date, datetime, timedelta
from logging.handlers import RotatingFileHandler
from urllib.parse import urlsplit

from dotenv import load_dotenv
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import (
    async_playwright,
)

from repository import RedisDB

logger = logging.getLogger("autocheck")


def setup_logging() -> None:
    """Настраивает вывод логов в консоль и вращающийся файл."""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "autocheck.log")

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(
            RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        )

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=handlers,
        force=True,
    )


def _redis_target(url: str) -> str:
    """Возвращает REDIS_URL без учётных данных для логов."""

    parts = urlsplit(url)
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    db = parts.path.lstrip("/") or "0"
    return f"{parts.scheme}://{host}{port}/{db}"


BASE_URL = "https://lk.sut.ru/cabinet/?printin=yes"

TIME_SLOTS = {
    "1": ("09:00", "10:35"),
    "2": ("10:45", "12:20"),
    "3": ("13:00", "14:35"),
    "4": ("14:45", "16:20"),
    "5": ("16:30", "18:05"),
    "6": ("18:15", "19:50"),
}


# ====== AUTHENTICATION ======


async def login(page, email, password):
    logger.info("Начинаю логин...")

    if not email or not password:
        logger.error("Не заданы LOGIN и PASSWORD в .env")
        raise ValueError("LOGIN и PASSWORD должны быть заданы в .env")

    await page.locator("#users").fill(email)
    await page.locator("#parole").fill(password)
    await page.locator("#logButton").click()

    await page.locator("#heading1 > h5 > div").wait_for(
        state="visible",
        timeout=15000,
    )

    logger.info("Логин выполнен.")


# ====== NAVIGATION ======


async def go_to_url(page):
    logger.info("Переход на страницу занятий...")

    open_learn = page.locator("#heading1 > h5 > div")
    await open_learn.click()

    go_to_scheduler = page.locator("#menu_li_6118")
    await go_to_scheduler.click()

    logger.info("На странице расписания: %s", page.url)


async def open_schedule(page, email, password):
    """Открывает расписание, авторизуясь при необходимости."""

    await page.goto(BASE_URL, wait_until="domcontentloaded")
    logger.debug("Открыта страница: %s", page.url)

    login_form = page.locator("#users")

    if await login_form.count() > 0 and await login_form.is_visible():
        await login(page, email, password)

    await go_to_url(page)


# ====== ATTENDANCE ======


async def check_in_bonch(end_time, page, email, password):
    """
    Ищет кнопку 'Начать занятие' до окончания пары.
    Каждые 2-4 минуты перезагружает текущую страницу расписания.
    """

    logger.info("Проверяю кнопки 'Начать занятие'...")

    attempt = 0

    while datetime.now() < end_time:
        attempt += 1
        logger.info(
            "Попытка %d поиска кнопок. URL: %s",
            attempt,
            page.url,
        )

        # Локатор создаём заново после каждой перезагрузки: так он всегда
        # соответствует текущему DOM, как это было в старой версии на Selenium.
        start_buttons = page.locator("a", has_text="Начать занятие")

        try:
            # Раньше использовался presence_of_all_elements_located: важно
            # дождаться появления кнопок, а не только видимости первой из них.
            await start_buttons.first.wait_for(
                state="attached",
                timeout=10000,
            )

            buttons_count = await start_buttons.count()
            logger.info("Найдено кнопок 'Начать занятие': %d", buttons_count)

            for index in range(buttons_count):
                button = start_buttons.nth(index)

                try:
                    await button.scroll_into_view_if_needed()
                    await button.click(timeout=10000)

                    logger.info("Нажата кнопка %d/%d", index + 1, buttons_count)

                except Exception:
                    logger.exception(
                        "Не удалось нажать кнопку %d/%d",
                        index + 1,
                        buttons_count,
                    )

            logger.info("Кнопки занятия нажаты.")
            return True, None

        except PlaywrightTimeoutError:
            logger.warning("Кнопки пока не появились. URL: %s", page.url)

        except Exception:
            logger.exception("Ошибка поиска кнопки. URL: %s", page.url)

        remaining = (end_time - datetime.now()).total_seconds()

        if remaining <= 0:
            break

        sleep_time = min(random.uniform(120, 240), remaining)

        logger.info("Следующая проверка через %.0f сек.", sleep_time)
        await asyncio.sleep(sleep_time)

        if datetime.now() >= end_time:
            break

        # В старой версии здесь был driver.refresh(): остаёмся на странице
        # расписания и просто перечитываем её. Возврат на главную через
        # open_schedule() ломал повторный поиск кнопок.
        try:
            logger.debug("Перезагружаю страницу: %s", page.url)
            await page.reload(wait_until="domcontentloaded")
            logger.info("Страница перезагружена: %s", page.url)

        except Exception:
            logger.exception("Ошибка перезагрузки страницы. URL: %s", page.url)

            # Запасной путь, если reload не удался.
            try:
                await open_schedule(page, email, password)
                logger.info("Расписание открыто повторно: %s", page.url)

            except Exception:
                logger.exception("Ошибка повторного открытия расписания")

    logger.warning("Время пары закончилось. Кнопки не найдены.")
    return False, "Время истекло"


# ====== SCHEDULE PROCESSING ======


async def check(schedule, page, email, password):

    for lesson in schedule:
        pair = str(lesson["pair"])

        if pair not in TIME_SLOTS:
            logger.warning("Неизвестный номер пары: %s", pair)
            continue

        start_time_str, end_time_str = TIME_SLOTS[pair]

        today = datetime.now().date()

        start_time = datetime.combine(
            today,
            datetime.strptime(start_time_str, "%H:%M").time(),
        )

        end_time = datetime.combine(
            today,
            datetime.strptime(end_time_str, "%H:%M").time(),
        )

        current_time = datetime.now()

        logger.info(
            "Проверяю пару %s: %s - %s, сейчас %s",
            pair,
            start_time_str,
            end_time_str,
            current_time.strftime("%H:%M"),
        )

        if current_time >= end_time:
            logger.info("Пара %s уже прошла. Пропускаю...", pair)
            continue

        # Ожидание начала пары
        while current_time < start_time:
            delta = (start_time - current_time).total_seconds()

            logger.info(
                "До начала пары %s осталось %.1f минут.",
                pair,
                delta / 60,
            )

            await asyncio.sleep(delta)
            current_time = datetime.now()

        if datetime.now() >= end_time:
            logger.info("Время пары %s закончилось. Пропускаю...", pair)
            continue

        logger.info("Время пары %s, открываю сайт...", pair)

        try:
            await open_schedule(page, email, password)

            was_checked, error = await check_in_bonch(
                end_time,
                page,
                email,
                password,
            )

            if was_checked:
                logger.info("Кнопки занятия нажаты. Пара %s", pair)
            else:
                logger.error("Ошибка при отметке пары %s: %s", pair, error)

        except Exception:
            logger.exception("Ошибка при обработке пары %s", pair)

    logger.info("Все пары на сегодня обработаны.")
    return True


# ====== DATE HELPERS ======


def normalize_datetime(value):
    """Преобразует date/datetime в локальный datetime без timezone."""

    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone().replace(tzinfo=None)

        return value

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    raise TypeError(f"Неизвестный тип даты: {type(value)}")


# ====== MAIN ======


async def main():

    load_dotenv()
    setup_logging()

    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        logger.error("Не задан REDIS_URL в .env")
        raise ValueError("REDIS_URL не задан в .env")

    logger.info(
        "Конфигурация: LOGIN=%s, PASSWORD=%s, REDIS=%s, LOG_LEVEL=%s, LOG_FILE=%s",
        "задан" if email else "НЕ задан",
        "задан" if password else "НЕ задан",
        _redis_target(redis_url),
        os.getenv("LOG_LEVEL", "INFO").upper(),
        os.getenv("LOG_FILE", "autocheck.log") or "отключён",
    )

    logger.info("Создание экземпляра браузера...")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
        )
        logger.info("Браузер запущен: Chromium %s", browser.version)

        context = await browser.new_context()

        page = await context.new_page()
        page.set_default_timeout(10000)
        db = RedisDB(redis_url)

        try:
            logger.info("Инициализация базы данных...")

            while True:
                try:
                    current_date = datetime.now().date()

                    logger.info("Проверка расписания на %s", current_date)

                    schedule, today_has_lessons = await db.check_scheduler(
                        current_date
                    )

                    if today_has_lessons:
                        logger.info("Сегодня есть пары.")

                        await check(
                            schedule,
                            page,
                            email,
                            password,
                        )

                        now = datetime.now()

                        tomorrow = (now + timedelta(days=1)).replace(
                            hour=0,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )

                        sleep_seconds = (tomorrow - now).total_seconds()

                        logger.info(
                            "Жду до полуночи (%.2f часов)",
                            sleep_seconds / 3600,
                        )

                        await asyncio.sleep(sleep_seconds)

                        continue

                    # Сегодня занятий нет
                    if not schedule:
                        logger.info(
                            "Расписание пустое. Повторная проверка через час."
                        )
                        await asyncio.sleep(3600)
                        continue

                    next_date_row = schedule[0]
                    next_date = normalize_datetime(next_date_row[1])

                    current_datetime = datetime.now()

                    sleep_seconds = (next_date - current_datetime).total_seconds()

                    if sleep_seconds <= 0:
                        logger.warning("Дата следующего расписания уже наступила.")
                        await asyncio.sleep(60)
                        continue

                    logger.info(
                        "Сегодня пар нет. Жду до %s (%.1f минут)",
                        next_date,
                        sleep_seconds / 60,
                    )

                    await asyncio.sleep(sleep_seconds)

                except asyncio.CancelledError:
                    raise

                except Exception:
                    logger.exception(
                        "Ошибка в главном цикле. Повторная проверка через 60 сек."
                    )
                    await asyncio.sleep(60)

        finally:
            logger.info("Закрываю браузер...")

            await db.close()
            await context.close()
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем.")
