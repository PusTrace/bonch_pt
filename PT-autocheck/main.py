#library
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime


#consts
url = "https://lk.sut.ru/cabinet/?login=yes"
service = Service()
driver = webdriver.Chrome(service=service)
driver.get(url=url)


# functions
def login_in_bonch():
    Emailfield = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/div/dl/dd[1]/input")
    Emailfield.send_keys("your_email_address@mail.ru")
    with open('pswd.txt', 'r') as file:
        pswd = file.read().strip()
    pswdfield = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/div/dl/dd[2]/input")
    pswdfield.send_keys(pswd)
    driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/div/dl/dd[3]/input").click()
    time.sleep(2)

def jump_schedule():
    # переход в учёбу
    driver.find_element(By.XPATH, "/html/body/div[1]/div[10]/div/div/div/div[1]/div[1]/h5/div").click()
    time.sleep(1)
    # переход к расписанию
    driver.find_element(By.XPATH,
                        "/html/body/div[1]/div[10]/div/div/div/div[1]/div[2]/div/div/ul/li[1]/span/nobr/a").click()
    time.sleep(2)

def check_in_bonch():
    # Находим все ссылки с текстом "Начать занятие"
    start_buttons = driver.find_elements(By.XPATH, "//a[text()='Начать занятие']")

    # Проходим по всем кнопкам и кликаем на каждую
    for button in start_buttons:
        button.click()
        time.sleep(1)  # Даем странице время обработать каждый клик
    time.sleep(5)

# Функция для обновления страницы
def refresh_page():
    print(f"Обновляю страницу на {datetime.now()}...")
    driver.refresh()

# Функция для ожидания заданной даты и времени
def wait_until(target_date):
    while True:
        # Получаем текущее время
        current_time = datetime.now()

        # Сравниваем текущее время с целевым
        if current_time >= target_date:
            refresh_page()  # Обновляем страницу
            break
        else:
            # Ждем 1 минуту перед следующей проверкой
            time.sleep(120)

# in futer data base with dates
target_date = datetime(2024, 9, 7, 10, 35)  # Например, 10 сентября 2024 года в 08:48


# main
login_in_bonch()
while True:
    try:
        jump_schedule()
        # Пытаемся найти кнопку "Начать занятие"
        wait = WebDriverWait(driver, 10)  # Ждём до 10 секунд
        start_button = wait.until(EC.presence_of_element_located((By.XPATH, "//a[text()='Начать занятие']")))

        # Если кнопка найдена, выходим из цикла и выполняем нужные действия
        print("Я тебя отметил")
        check_in_bonch()
    except (TimeoutException, NoSuchElementException):
        # Если кнопка не найдена, ждем до целевого времени
        print("Кнопка не найдена, ожидаем")
        wait_until(target_date)