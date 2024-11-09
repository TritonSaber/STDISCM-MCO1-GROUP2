import time
import threading
import pandas
import re
import bs4

if __name__ == '__main__':
    url = 'https://dlsu.edu.ph'
    email_pattern = re.compile(r'^[a-zA-Z0-9_.-]*[@](dlsu.edu.ph)')


