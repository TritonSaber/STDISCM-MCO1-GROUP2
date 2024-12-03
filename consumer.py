import pika
import time
import requests
from bs4 import BeautifulSoup

def scrape_website(url, time_limit):
    # Add your scraping logic here
    print(f"Scraping {url} for {time_limit} minutes...")
    # Simulate scraping work
    time.sleep(10)
    print(f"Finished scraping {url}")

def callback(ch, method, properties, body):
    task = body.decode()
    url, time_limit = task.split(',')
    print(f" [x] Received task: {task}")
    scrape_website(url, int(time_limit))
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue="scraping_tasks")

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.basic_consume(queue="scraping_tasks", on_message_callback=callback)

    channel.start_consuming()
