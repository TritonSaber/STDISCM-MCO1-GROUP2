from .task_receiver import scrape_emails
import sys

if __name__ == '__main__':
    url = sys.argv[1]
    num_nodes = int(sys.argv[2])
    time_limit = int(sys.argv[3])
    for i in range(num_nodes):
        result = scrape_emails.delay(url, time_limit)
        print('Task submitted for node', i)