import pika
import sys

def send_to_queue(queue_name, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='', routing_key=queue_name, body=message)
    print(f" [x] Sent '{message}'")
    connection.close()

if __name__ == "__main__":
    url = input("Enter the URL to scrape: ")
    time_limit = input("Enter the time limit in minutes: ")
    nodes = input("Enter the number of nodes: ")

    # Send the task to the queue
    task_message = f"{url},{time_limit}"
    send_to_queue("scraping_tasks", task_message)
