import os
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from deadline_packages.utils import Database
from datetime import datetime, timedelta, date

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# ====== FUNCTIONS ======

def login(email, password, driver):
    log("Начинаю логин...")
    if email is None or password is None:
        raise ValueError("Environment variables LOGIN and PASSWORD must be set.")
    wait = WebDriverWait(driver, 10)
    mail_input = wait.until(EC.presence_of_element_located((By.ID, "users")))
    mail_input.send_keys(email)
    password_input = wait.until(EC.presence_of_element_located((By.ID, "parole")))
    password_input.send_keys(password)
    btn_for_login = wait.until(EC.presence_of_element_located((By.ID, "logButton")))
    btn_for_login.click()
    log("Логин выполнен.")

def go_to_url(driver):
    log("Переход на страницу занятий...")
    wait = WebDriverWait(driver, 10)
    open_learn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading1 > h5 > div")))
    open_learn.click()
    go_to_scheduler = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#menu_li_6118")))
    go_to_scheduler.click()
    log("На странице расписания.")

def check_in_bonch(end_time, driver):
    """
    Пытается отметить занятие до указанного end_time (datetime.time).
    Каждые 5 минут обновляет страницу.
    """
    log("Проверяю кнопки 'Начать занятие'...")
    while True:
        current_time = datetime.now().time()
        if current_time > end_time:
            log("Время пары закончилось, пропускаю отметку.")
            return False, "Время истекло"

        try:
            start_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'Начать занятие')]"))
            )
            if start_buttons:
                for button in start_buttons:
                    try:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
                        log("Нажимаю 'Начать занятие'...")
                        button.click()
                        time.sleep(0.5)
                    except Exception as e:
                        log(f"Не удалось кликнуть по кнопке: {e}")
                log("Занятие отмечено!")
                return True, None
            else:
                log("Кнопок 'Начать занятие' пока нет, жду 5 минут и обновляю страницу...")
                time.sleep(5*60)
                driver.refresh()
        except Exception as e:
            log(f"Ошибка при поиске кнопки: {e}")
            time.sleep(5*60)
            driver.refresh()



def check(schedule):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    
    missed_lessons = 0
    for lesson in schedule:
        pair = lesson[2]
        start_time_str, end_time_str = time_slots[pair]
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.strptime(start_time_str, "%H:%M").time())
        end_time   = datetime.combine(today, datetime.strptime(end_time_str, "%H:%M").time())
        current_time = datetime.now()
        log(f"Проверяю время пары {pair}: {start_time_str} - {end_time_str}, текущее: {current_time.strftime('%H:%M')}")

        if current_time > end_time:
            log(f"Пара {pair} уже прошла. Пропускаю...")
            missed_lessons += 1
            continue

        while current_time < start_time:

            delta = (start_time - current_time).total_seconds()
            log(f"Ещё не время пары {pair}, жду {delta/60:.1f} минут...")
            time.sleep(max(delta, 0))
            current_time = datetime.now().time()

        # время пары
        log(f"Время пары {pair}, заходим на сайт...")
        driver.get("https://lk.sut.ru/cabinet/?login=yes")
        login(email, password, driver)
        go_to_url(driver)
        was_checked, error = check_in_bonch(end_time, driver)
        if was_checked:
            log(f"Я тебя отметил ленивая ты жопа! Пара {pair}")
        else:
            log(f"Ошибка при отметке пары {pair}: {error}")

    log("Все пары на сегодня обработаны.")
    return True


# ====== MAIN ======

if __name__ == "__main__":
    load_dotenv()
    email = os.getenv('LOGIN')
    password = os.getenv('PASSWORD')
    time_slots = {
        "1": ("09:00", "10:35"),
        "2": ("10:45", "12:20"),
        "3": ("13:00", "14:35"),
        "4": ("14:45", "16:20"),
        "5": ("16:30", "18:05"),
        "6": ("18:15", "19:50")
    }
    log("Инициализация базы данных...")
    db = Database()

    while True:
        current_date = datetime.now().date()
        log(f"Проверка расписания на {current_date}")
        schedule, today_has_lessons = db.check_scheduler(current_date)
        
        if today_has_lessons:
            log("Сегодня есть пары.")
            was_checked = check(schedule)
            if was_checked:
                now = datetime.now()
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = (tomorrow - now).total_seconds()
                log(f"Жду до полуночи ({sleep_seconds/3600:.2f} часов)")
                time.sleep(sleep_seconds)
                continue
        else:
            current_datetime = datetime.now()
            next_date_row = schedule[0]
            next_date = next_date_row[1]

            if isinstance(next_date, date) and not isinstance(next_date, datetime):
                next_datetime = datetime.combine(next_date, datetime.min.time())
            else:
                if next_date.tzinfo is not None:
                    next_datetime=next_date.astimezone().replace(tzinfo=None)
                else:
                    next_datetime = next_date

            # убираем таймзону, если есть
            if isinstance(next_datetime, datetime) and next_datetime.tzinfo is not None:
                next_datetime = next_datetime.astimezone().replace(tzinfo=None)

            sleep_seconds = (next_datetime - current_datetime).total_seconds()


            log(f"Сегодня пар нет. Жду до {next_date} ({sleep_seconds/60:.1f} минут)")
            time.sleep(sleep_seconds)
            continue
