import requests
from bs4 import BeautifulSoup


url = "https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya?group=56160"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}


response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

table_with_schedule = []

schedule_table = soup.find_all("div", {"class": "vt244b"})

if schedule_table:
    rows = schedule_table[0].find_all("div", {"class": "vt244"})
    for row in rows:
        columns = row.find_all("div", {"class": "vt239"})
        for column in columns:
            print(column.text)

