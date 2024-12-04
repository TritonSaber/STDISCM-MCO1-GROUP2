from celery_main.celery import app
import requests
from bs4 import BeautifulSoup
import re

@app.task(bind=True, default_retry_delay=10)
def scrape_emails(self, url):
    print('Scraping emails from', url)
    response = requests.get(url)
    if response.status_code == 200:
        emails = extract_emails(response.text)
        save_emails(emails)
    else:
        print('Failed to retrieve the page')

def extract_emails(text):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    return email_pattern.findall(text)

def save_emails(emails):
    with open('emails.txt', 'a') as f:
        for email in emails:
            f.write(email + '\n')
