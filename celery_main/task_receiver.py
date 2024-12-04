from celery_main.celery import app
import requests
from bs4 import BeautifulSoup
import csv
import time
import threading

http = requests.Session()
data_lock = threading.Lock()
seen_emails = set()

@app.task(bind=True, default_retry_delay=10)
def scrape_emails(self, url, time_limit):
    print('Scraping emails from', url)
    start_time = time.time()
    emails_found = 0
    faculty_info = []

    # Check for time limit
    if time.time() - start_time > time_limit * 60:
        print("Time limit exceeded, stopping the scraping.")
        return []

    response = http.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        for div in soup.find_all('div', class_="wpb_wrapper"):
            name_tag = div.find('strong')
            role_tag = div.find('p')
            email_tag = div.find_all('a', href=True)

            name_text = name_tag.get_text(strip=True) if name_tag else None
            email_text = None

            for a_tag in email_tag:
                if '/cdn-cgi/l/email-protection' in a_tag['href']:
                    encoded_email = a_tag['href'].split('#')[-1]
                    email_text = decode_email(encoded_email)
                    break

            if role_tag:
                role_text = role_tag.get_text(strip=True)
            else:
                role_text = 'Not applicable'

            source_url = url

            # Use a lock to ensure thread safety when accessing seen_emails
            with data_lock:
                if email_text and email_text not in seen_emails:
                    faculty_info.append({
                        'Name': name_text,
                        'Role': role_text,
                        'Email': email_text,
                        'Source': source_url
                    })
                    seen_emails.add(email_text)
                    emails_found += 1

        save_emails(faculty_info)
        return faculty_info
    else:
        print('Failed to retrieve the page')
        return []

def decode_email(e):
    try:
        if not e:
            return None
        de = ""
        k = int(e[:2], 16)
        for i in range(2, len(e)-1, 2):
            de += chr(int(e[i:i+2], 16) ^ k)
        return de
    except ValueError as ve:
        print(f"Error decoding email: {ve} - Invalid email format: {e}")
        return None

def save_emails(emails):
    with open('faculty_emails.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Name', 'Role', 'Email', 'Source'])
        if f.tell() == 0:  # Write header if file is empty
            writer.writeheader()
        for email in emails:
            writer.writerow(email)