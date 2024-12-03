FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install requests beautifulsoup4 pika

CMD ["python", "producer.py"]  # Or "worker.py" depending on the service
