FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

WORKDIR /app

COPY autocheck/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY autocheck/. .

CMD ["python", "main.py"]

