import os
import time
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from dotenv import load_dotenv

#consts
url = "https://lk.sut.ru/cabinet/?login=yes"
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

def login():
    if email is None or password is None:
        raise ValueError("Environment variables LOGIN and PASSWORD must be set.")
    wait = WebDriverWait(driver, 10)
    mail_input = wait.until(EC.presence_of_element_located((By.ID, "users")))
    mail_input.send_keys(email)
    password_input = wait.until(EC.presence_of_element_located((By.ID, "parole")))
    password_input.send_keys(password)
    btn_for_login = wait.until(EC.presence_of_element_located((By.ID, "logButton")))
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
    

if __name__ == "__main__":
    options = Options()
    options.add_argument('--headless')  # Запуск без отображения окна браузера
    options.add_argument('--disable-gpu')  # Для предотвращения ошибок на некоторых системах
    options.add_argument('--no-sandbox')  # Иногда требуется для работы в контейнерах или в ограниченных окружениях


    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    driver.get("https://lk.sut.ru/cabinet/?login=yes")
    login()
    go_to_url()
    check_in_bonch()
    driver.quit()
