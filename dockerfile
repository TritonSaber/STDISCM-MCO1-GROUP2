FROM python:3
ADD ./celery_main/ /app/
WORKDIR /app/
RUN pip install amqp billiard celery certifi chardet idna kombu pytz requests urllib3 vine psycopg2 beautifulsoup4 bs4 lxml urllib3
ENTRYPOINT celery -A celery_main worker --concurrency=5 --loglevel=info