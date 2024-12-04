from .task_receiver import scrape_emails
import sys

if __name__ == '__main__':
    url = sys.argv[1]
    num_nodes = int(sys.argv[2])
    for i in range(num_nodes):
        result = scrape_emails.delay(url)
        print('Task submitted for node', i)
