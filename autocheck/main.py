import asyncio
import os
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import (
    async_playwright,
)

from repository import RedisDB

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
    print("Начинаю логин...")

    if not email or not password:
        raise ValueError("LOGIN и PASSWORD должны быть заданы в .env")

    await page.locator("#users").fill(email)
    await page.locator("#parole").fill(password)
    await page.locator("#logButton").click()

    await page.locator("#heading1 > h5 > div").wait_for(
        state="visible",
        timeout=15000,
    )

    print("Логин выполнен.")


# ====== NAVIGATION ======


async def go_to_url(page):
    print("Переход на страницу занятий...")

    open_learn = page.locator("#heading1 > h5 > div")
    await open_learn.click()

    go_to_scheduler = page.locator("#menu_li_6118")
    await go_to_scheduler.click()

    print("На странице расписания.")


async def open_schedule(page, email, password):
    """Открывает расписание, авторизуясь при необходимости."""

    await page.goto(BASE_URL, wait_until="domcontentloaded")

    login_form = page.locator("#users")

    if await login_form.count() > 0 and await login_form.is_visible():
        await login(page, email, password)

    await go_to_url(page)


# ====== ATTENDANCE ======


async def check_in_bonch(end_time, page, email, password):
    """
    Ищет кнопку 'Начать занятие' до окончания пары.
    Каждую минуту заново открывает раздел расписания.
    """

    print("Проверяю кнопки 'Начать занятие'...")

    start_buttons = page.locator("xpath=//a[contains(text(), 'Начать занятие')]")

    while datetime.now() < end_time:
        try:
            await start_buttons.first.wait_for(
                state="visible",
                timeout=10000,
            )

            buttons_count = await start_buttons.count()

            for index in range(buttons_count):
                button = start_buttons.nth(index)

                try:
                    await button.scroll_into_view_if_needed()
                    await button.click(timeout=10000)

                    print(f"Нажата кнопка {index + 1}/{buttons_count}")

                except Exception as error:
                    print(f"Ошибка нажатия кнопки: {error}")

            print("Кнопки занятия нажаты.")
            return True, None

        except PlaywrightTimeoutError:
            print("Кнопки пока не появились.")

        except Exception as error:
            print(f"Ошибка поиска кнопки: {error}")

        remaining = (end_time - datetime.now()).total_seconds()

        if remaining <= 0:
            break

        sleep_time = min(60, remaining)

        print(f"Следующая проверка через {sleep_time:.0f} секунд...")
        await asyncio.sleep(sleep_time)

        if datetime.now() >= end_time:
            break

        try:
            print("Повторно открываю расписание...")

            await open_schedule(page, email, password)

            print(f"Текущий URL: {page.url}")

        except Exception as error:
            print(f"Ошибка повторного открытия расписания: {error}")

    print("Время пары закончилось.")
    return False, "Время истекло"


# ====== SCHEDULE PROCESSING ======


async def check(schedule, page, email, password):

    for lesson in schedule:
        pair = str(lesson["pair"])

        if pair not in TIME_SLOTS:
            print(f"Неизвестный номер пары: {pair}")
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

        print(
            f"Проверяю пару {pair}: "
            f"{start_time_str} - {end_time_str}, "
            f"сейчас {current_time.strftime('%H:%M')}"
        )

        if current_time >= end_time:
            print(f"Пара {pair} уже прошла. Пропускаю...")
            continue

        # Ожидание начала пары
        while current_time < start_time:
            delta = (start_time - current_time).total_seconds()

            print(f"До начала пары {pair} осталось {delta / 60:.1f} минут.")

            await asyncio.sleep(delta)
            current_time = datetime.now()

        if datetime.now() >= end_time:
            print(f"Время пары {pair} закончилось. Пропускаю...")
            continue

        print(f"Время пары {pair}, открываю сайт...")

        try:
            await open_schedule(page, email, password)

            was_checked, error = await check_in_bonch(
                end_time,
                page,
                email,
                password,
            )

            if was_checked:
                print(f"Кнопки занятия нажаты. Пара {pair}")
            else:
                print(f"Ошибка при отметке пары {pair}: {error}")

        except Exception as error:
            print(f"Ошибка при обработке пары {pair}: {error}")

    print("Все пары на сегодня обработаны.")
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

    email = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        raise ValueError("REDIS_URL не задан в .env")

    print("Создание экземпляра браузера...")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
        )

        context = await browser.new_context()

        page = await context.new_page()
        page.set_default_timeout(10000)
        db = RedisDB(redis_url)

        try:
            print("Инициализация базы данных...")

            while True:
                current_date = datetime.now().date()

                print(f"\nПроверка расписания на {current_date}")

                schedule, today_has_lessons = await db.check_scheduler(current_date)

                if today_has_lessons:
                    print("Сегодня есть пары.")

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

                    print(f"Жду до полуночи ({sleep_seconds / 3600:.2f} часов)")

                    await asyncio.sleep(sleep_seconds)

                    continue

                # Сегодня занятий нет
                if not schedule:
                    print("Расписание пустое. Повторная проверка через час.")
                    await asyncio.sleep(3600)
                    continue

                next_date_row = schedule[0]
                next_date = normalize_datetime(next_date_row[1])

                current_datetime = datetime.now()

                sleep_seconds = (next_date - current_datetime).total_seconds()

                if sleep_seconds <= 0:
                    print("Дата следующего расписания уже наступила.")
                    await asyncio.sleep(60)
                    continue

                print(
                    f"Сегодня пар нет. "
                    f"Жду до {next_date} "
                    f"({sleep_seconds / 60:.1f} минут)"
                )

                await asyncio.sleep(sleep_seconds)

        finally:
            print("Закрываю браузер...")

            await db.close()
            await context.close()
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
