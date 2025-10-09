# базовый образ
FROM python:3.12-slim

# рабочая папка внутри контейнера
WORKDIR /app

# копируем зависимости
COPY requirements.txt .

# ставим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# копируем сам скрипт
COPY app.py .

# команда, которая будет выполняться при старте контейнера
CMD ["python", "app.py"]
