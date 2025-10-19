# Используем официальный образ Python
FROM python:3.13-slim

# Задаём рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем команду запуска
CMD ["python", "autocheck.py"]
