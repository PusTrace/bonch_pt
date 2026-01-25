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
from datetime import datetime, timedelta, date
import psycopg2



class Database:
    def __init__(self):
        load_dotenv()
        self.conn = None

    def connect(self):
        """Создаёт синхронное соединение с базой данных PostgreSQL."""
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        # Чтобы fetch возвращал словари вместо кортежей
        self.conn.autocommit = True

    def check_scheduler(self, current_date: date):
        """
        Получает расписание на текущий день.
        Если на текущий день ничего нет — возвращает ближайшую дату после текущей.
        Возвращает: (список записей, bool — True если есть на сегодня)
        """
        with self.conn.cursor() as cur:
            # Проверяем расписание на текущий день
            cur.execute("""
                SELECT * FROM schedule 
                WHERE date::date = %s AND sect = 'ИКБ-31'
                ORDER BY pair::int ASC
            """, (current_date,))
            today_schedule = cur.fetchall()

            if today_schedule:
                return today_schedule, True

            # Если на сегодня ничего нет — ищем ближайшую дату
            cur.execute("""
                SELECT * FROM schedule 
                WHERE date = (
                    SELECT MIN(date) 
                    FROM schedule 
                    WHERE sect = 'ИКБ-31' AND date > %s
                )
                AND sect = 'ИКБ-31'
                ORDER BY pair::int ASC
            """, (current_date,))
            next_schedule = cur.fetchall()

        return next_schedule, False

        

def login(email, password, driver):
    print("Начинаю логин...")
    if email is None or password is None:
        raise ValueError("Environment variables printIN and PASSWORD must be set.")
    wait = WebDriverWait(driver, 10)
    mail_input = wait.until(EC.presence_of_element_located((By.ID, "users")))
    mail_input.send_keys(email)
    password_input = wait.until(EC.presence_of_element_located((By.ID, "parole")))
    password_input.send_keys(password)
    btn_for_printin = wait.until(EC.presence_of_element_located((By.ID, "logButton")))
    btn_for_printin.click()
    print("Логин выполнен.")

def go_to_url(driver):
    print("Переход на страницу занятий...")
    wait = WebDriverWait(driver, 10)
    open_learn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#heading1 > h5 > div")))
    open_learn.click()
    time.sleep(0.5)
    go_to_scheduler = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#menu_li_6118")))
    go_to_scheduler.click()
    print("На странице расписания.")


def check_in_bonch(end_time, driver):
    """
    Пытается отметить занятие до указанного end_time (datetime.time).
    Каждые 5 минут обновляет страницу.
    """
    print("Проверяю кнопки 'Начать занятие'...")
    while True:
        current_time = datetime.now()
        if current_time > end_time:
            print("Время пары закончилось, пропускаю отметку.")
            return False, "Время истекло"

        try:
            start_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//a[contains(text(), 'Начать занятие')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", start_buttons[0])
            if start_buttons:
                for button in start_buttons:
                    try:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
                        print("Нажимаю 'Начать занятие'...")
                        button.click()
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"Не удалось кликнуть по кнопке: {e}")
                print("Занятие отмечено!")
                return True, None
            else:
                print("Кнопок 'Начать занятие' пока нет, жду 5 минут и обновляю страницу...")
                time.sleep(5*60)
                driver.refresh()
        except Exception as e:
            print(f"Ошибка при поиске кнопки: {e}")
            time.sleep(5*60)
            driver.refresh()



def check(schedule, driver):
    
    missed_lessons = 0
    for lesson in schedule:
        pair = lesson[2]
        start_time_str, end_time_str = time_slots[pair]
        today = datetime.now().date()
        start_time = datetime.combine(today, datetime.strptime(start_time_str, "%H:%M").time())
        end_time   = datetime.combine(today, datetime.strptime(end_time_str, "%H:%M").time())
        current_time = datetime.now()
        print(f"Проверяю время пары {pair}: {start_time_str} - {end_time_str}, текущее: {current_time.strftime('%H:%M')}")

        if current_time > end_time:
            print(f"Пара {pair} уже прошла. Пропускаю...")
            missed_lessons += 1
            continue

        while current_time < start_time:

            delta = (start_time - current_time).total_seconds()
            print(f"Ещё не время пары {pair}, жду {delta/60:.1f} минут...")
            time.sleep(max(delta, 0))
            current_time = datetime.now()
        # время пары
        print(f"Время пары {pair}, заходим на сайт...")
        driver.get("https://lk.sut.ru/cabinet/?printin=yes")
        login(email, password, driver)
        go_to_url(driver)
        was_checked, error = check_in_bonch(end_time, driver)
        if was_checked:
            print(f"Я тебя отметил ленивая ты жопа! Пара {pair}")
        else:
            print(f"Ошибка при отметке пары {pair}: {error}")

    print("Все пары на сегодня обработаны.")
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

    
    print("Создание экземпляра браузера")
    options = Options()
    options.add_argument('--headless')   # или '--headless' в зависимости от версии
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print("Инициализация базы данных...")
        db = Database()
        db.connect()
        
        while True:
            current_date = datetime.now().date()
            print(f"Проверка расписания на {current_date}")
            schedule, today_has_lessons = db.check_scheduler(current_date)
            
            if today_has_lessons:
                print("Сегодня есть пары.")
                was_checked = check(schedule, driver)
                if was_checked:
                    now = datetime.now()
                    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                    sleep_seconds = (tomorrow - now).total_seconds()
                    print(f"Жду до полуночи ({sleep_seconds/3600:.2f} часов)")
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


                print(f"Сегодня пар нет. Жду до {next_date} ({sleep_seconds/60:.1f} минут)")
                time.sleep(sleep_seconds)
                continue
    finally:
        print("Выключаю драйвер...")
        try:
            driver.quit()
        except Exception:
            driver.close()
            driver.quit()
