import os
import time
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import re

#consts
url = "https://lk.sut.ru/cabinet/?login=yes"
email = os.getenv('YOUR_EMAIL')
password = os.getenv('YOUR_PASSWORD')

time_slots = {
    "1": ("09:00", "10:35"),
    "ФЗ": ("9:00", "10:30"),
    "2": ("10:45", "12:20"),
    "3": ("13:00", "14:35"),
    "4": ("14:45", "16:20"),
    "5": ("16:30", "18:05"),
    "6": ("18:15", "19:50")
}

def login():
    wait = WebDriverWait(driver, 10)
    mail_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#users")))
    mail_input.send_keys(email)
    password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#parole")))
    password_input.send_keys(password)
    btn_for_login = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#logButton")))
    btn_for_login.click()
def go_to_url():
    wait = WebDriverWait(driver, 10)
    open_learn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#heading1 > h5 > div")))
    open_learn.click()
    go_to_scheduler = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#menu_li_6118")))
    go_to_scheduler.click()

def check_in_bonch():
    while True:
        try:
            start_buttons = driver.find_elements(By.XPATH, "//a[text()='Начать занятие']")
            if start_buttons:
                for button in start_buttons:
                    button.click()
                    time.sleep(0.5)
                time.sleep(45*60)
                break
            else:
                time.sleep(5*60)
                driver.refresh()
        except Exception as e:
            driver.quit()
            break
    
    
    
def load_schedule(filename):
    # Загружаем расписание из JSON файла
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_schedule(json_data, time_slots):
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    
    if current_date in json_data:
        day_schedule = json_data[current_date]
        if day_schedule:
            first_pair_found = False  # Переменная для отслеживания первой пары
            for time_slot, pair_time in day_schedule.items():
                # Получаем время начала и конца пары
                start_time, end_time = time_slots.get(time_slot, ("00:00", "00:00"))
                
                # Если это первая пара (первая из списка, независимо от номера)
                if not first_pair_found:
                    # Если первая пара, сдвигаем время старта на 45 минут
                    first_pair_found = True
                    start_time = (datetime.strptime(start_time, "%H:%M") + timedelta(minutes=45)).strftime("%H:%M")
                
                # Проверяем, попадает ли текущее время в интервал
                if start_time <= current_time <= end_time:
                    return True
        else:
            return False
    else:
        return False


def schedule_check(filename, time_slots):
    schedule_data = load_schedule(filename)
    return check_schedule(schedule_data, time_slots)

if __name__ == "__main__":
    options = Options()
    #options.add_argument('--headless')  # Запуск без отображения окна браузера
    #options.add_argument('--disable-gpu')  # Для предотвращения ошибок на некоторых системах
    #options.add_argument('--no-sandbox')  # Иногда требуется для работы в контейнерах или в ограниченных окружениях

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    if schedule_check("schedule.json", time_slots):
        driver.get("https://lk.sut.ru/cabinet/?login=yes")
        login()
        go_to_url()
        check_in_bonch()
        driver.quit()
    else:
        time.sleep(5*60)