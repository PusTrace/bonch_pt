
FROM python:3.14-slim

WORKDIR /app

COPY services/bonch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/bonch .

CMD ["python", "autocheck.py"]
CMD ["python", "schedule_parser.py"]
CMD ["python", "schedule.py"]
