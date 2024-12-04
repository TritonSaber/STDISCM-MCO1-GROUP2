from celery_main.celery import app
import requests
from bs4 import BeautifulSoup
import csv
import time
import threading

http = requests.Session()
data_lock = threading.Lock()
seen_emails = set()
statistics = {}
thread_times = {}

@app.task(bind=True, default_retry_delay=10)
def scrape_emails(self, url, time_limit):
    start_time = time.time()
    threads = []
    elapsed_time = 0

    def fetch_emails(url):
        nonlocal elapsed_time
        if elapsed_time > time_limit * 60:
            print("Time limit exceeded, stopping the scraping.")
            return [], True
        
        response = http.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            faculty_info = []
            emails_found = 0

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

                role_text = role_tag.get_text(strip=True) if role_tag else 'Not applicable'
                source_url = url

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

            update_statistics(url, emails_found)
            return faculty_info, False
        else:
            print("Failed to retrieve the webpage.")
            return None, False

    def update_statistics(url, emails_found):
        if url in statistics:
            statistics[url]['Pages Scraped'] += 1
            statistics[url]['Emails Found'] += emails_found
        else:
            statistics[url] = {
                'Pages Scraped': 1,
                'Emails Found': emails_found
            }

    # Start fetching emails
    email_data, time_exceeded = fetch_emails(url)
    if time_exceeded:
        return

    if email_data:
        with open('faculty_emails.txt', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Name', 'Role', 'Email', 'Source'])
            if f.tell() == 0:
                writer.writeheader()
            for row in email_data:
                writer.writerow(row)

        print(f"Data for {url} saved.")
    else:
        print(f"No data found for {url}.")

    write_statistics_to_file()

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

def write_statistics_to_file():
    with open('scrape_statistics.txt', 'w', encoding='utf-8') as f:
        f.write("Scrape Statistics\n")
        f.write("====================\n")
        for url, stats in statistics.items():
            f.write(f"URL: {url}\n")
            f.write(f"  Pages Scraped: {stats['Pages Scraped']}\n")
            f.write(f"  Emails Found: {stats['Emails Found']}\n")
            f.write("====================\n")

    print("Statistics written to scrape_statistics.txt")