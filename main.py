import time
import threading
import pandas as pd
import re
import requests
import bs4
from bs4 import BeautifulSoup
import csv

http = requests.Session()

# Create a lock object for synchronization
data_lock = threading.Lock()

all_faculty_info = []

thread_times = {}

# Functionalities to be done:
# Thread/Process Used
# Input arguments: URL of website, and Minutes given for scraping
# Output: Text file with email and associated name, offic, dep, OR unit in CSV format; Text file containing statistics of website: URL, num of pages scraped and num of email addr found

# Remember to close the csv file when saving/running

def decodeEmail(e):
    #https://stackoverflow.com/questions/36911296/scraping-of-protected-email cause cloudfare cool
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e)-1, 2):
        de += chr(int(e[i:i+2], 16)^k)

    return de

def fetch_emails(url):
    start_time = time.time()
    # Email pattern
    #email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu.edu.ph')

    # Send a GET request to the URL
    response = http.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the webpage content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Set to store emails found
        faculty_info = []
        seen_emails = set()

        # Searching in wpb_wrapper, in faculty profile that each entry has
        for div in soup.find_all('div', class_="wpb_wrapper"):
            
            if 'faculty-profile' in url:
                name_tag = div.find('strong')
            else:
                name_tag = soup.find('h1')

            role_tag = div.find('p')
            email_tag = div.find_all('a', href=True) 

            name_text = name_tag.get_text(strip=True) if name_tag else None

            #print(f"Div: {div.prettify()}")
            email_text = None
            for a_tag in email_tag:
                if '/cdn-cgi/l/email-protection' in a_tag['href']: #We know it's going to be encrypted but still, this checks for every a tag in the div, which should be 2 sometimes.
                    # Handle encoded email link
                    encoded_email = a_tag['href'].split('#')[-1]  # Get the encoded part after '#'
                    email_text = decodeEmail(encoded_email)
                    break  # Stop after decoding

            # For Role Column
            if role_tag and 'faculty-profile' in url:
                for a_tag in role_tag.find_all('a'):
                    a_tag.decompose()  # Remove <a> tag 
                for strong_tag in role_tag.find_all('strong'):
                    strong_tag.decompose() # Remove <strong> tag
                # Now get the role text without any <a> tags
                role_text = role_tag.get_text(strip=True)
            else:
                role_text = 'Not applicable'

            source_url = url

            if name_text and email_text not in seen_emails:
                if email_text is not None:
                    faculty_info.append({
                        'Name': name_text,
                        'Role': role_text,
                        'Email': email_text,
                        'Source': source_url
                    })
                    seen_emails.add(email_text)

        end_time = time.time()
        thread_duration = end_time - start_time  # Time taken for the thread
        thread_times[url] = thread_duration

        return faculty_info
    else:
        print("Failed to retrieve the webpage.")
        thread_times[url] = None
        return None

# Function to scrape multiple pages concurrently (IDK YET)
def scrape_pages(urls):
    threads = []

    for url in urls:
        thread = threading.Thread(target=save_data_from_thread, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("Thread durations:")
    for url, duration in thread_times.items():
        if duration is not None:
            print(f"{url}: {duration:.2f} seconds")
        else:
            print(f"{url}: Failed to scrape or skipped")

    save_to_csv()

def save_data_from_thread(url):
    faculty_info = fetch_emails(url)

    # Ensure thread-safe appending of data
    with data_lock:
        all_faculty_info.extend(faculty_info)

def save_to_csv():
    # Convert collected data to a DataFrame and save it to a CSV file
    if all_faculty_info:
        df = pd.DataFrame(all_faculty_info)
        df.to_csv('dlsu_emails.csv', index=False, encoding='utf-8')
        print("Data saved to 'dlsu_emails.csv'")
    else:
        print("No data to save.")



if __name__ == '__main__':
    phase = 2 #1 for manual, 2 for threads kind of
    if phase == 1:
        url = 'https://www.dlsu.edu.ph/'
        test_url = 'https://www.dlsu.edu.ph/research/offices/urco/'
        try:
            response = http.get(test_url, timeout=10)
            response.raise_for_status()
            print("Connection Success")
            print("Attempting to fetch...")
            email_df = fetch_emails(test_url)
            print(email_df)
            if email_df is not None:
                if not email_df.empty:
                    print("Emails found:")
                    print(email_df)
                else:
                    print("Email DataFrame is empty.")
            else:
                print("No emails or an error occurred.")
        except requests.exceptions.RequestException as e:
            print(f"Nope, Error: {e}")
    
    if phase == 2:
        urls_to_scrape = [
        #'https://www.dlsu.edu.ph/',
        'https://www.dlsu.edu.ph/research/offices/urco/',
        'https://www.dlsu.edu.ph/offices/registrar/',
        'https://www.dlsu.edu.ph/colleges/cla/academic-departments/political-science/faculty-profile/',
        # Add more URLs here
        ]
        scrape_pages(urls_to_scrape)

