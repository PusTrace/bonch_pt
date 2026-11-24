FROM python:3.14-slim

WORKDIR /app

COPY schedule/ .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "telegram_bot.py"]
