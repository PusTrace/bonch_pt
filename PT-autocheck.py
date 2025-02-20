import os
import time
import datetime
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


if __name__ == "__main__":
    options = Options()
    #options.add_argument('--headless')  # Запуск без отображения окна браузера
    #options.add_argument('--disable-gpu')  # Для предотвращения ошибок на некоторых системах
    #options.add_argument('--no-sandbox')  # Иногда требуется для работы в контейнерах или в ограниченных окружениях

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://lk.sut.ru/cabinet/?login=yes")
    login()
    go_to_url()
    driver.quit()