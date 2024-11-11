import time
import threading
import pandas as pd
import re
import requests
import bs4
from bs4 import BeautifulSoup

http = requests.Session()

# Create a lock object for synchronization
print_lock = threading.Lock()

# Functionalities to be done:
# Thread/Process Used
# output: text file with email and name; stats of website from URL, number of pages scraped and email addr found
# so like, able to traverse tab to tab?

def decodeEmail(e):
    #https://stackoverflow.com/questions/36911296/scraping-of-protected-email cause cloudfare cool
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e)-1, 2):
        de += chr(int(e[i:i+2], 16)^k)

    return de

def fetch_emails(url):
    # Email pattern
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu.edu.ph')

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
            name_tag = div.find('strong')
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
            if role_tag:
                for a_tag in role_tag.find_all('a'):
                    a_tag.decompose()  # Remove <a> tag 
                for strong_tag in role_tag.find_all('strong'):
                    strong_tag.decompose() # Remove <strong> tag
                # Now get the role text without any <a> tags
                role_text = role_tag.get_text(strip=True)

            if name_text and email_text not in seen_emails:
                faculty_info.append({
                    'Name': name_text,
                    'Role': role_text,
                    'Email': email_text
                })
                seen_emails.add(email_text)

        df = pd.DataFrame(faculty_info)
        return df
    else:
        print("Failed to retrieve the webpage.")
        return None

# Function to scrape multiple pages concurrently (IDK YET)
def scrape_pages(urls):
    threads = []

    for url in urls:
        thread = threading.Thread(target=scrape_page, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

# Scrape a single page (to be called in each thread) (ALSO IDK BUT MAYBE A START)
def scrape_page(url):
    # Use the lock to ensure only one thread prints at a time
    with print_lock:
        print(f"Scraping {url}...")

    email_df = fetch_emails(url)

    # Use the lock to ensure only one thread prints at a time
    with print_lock:
        if email_df is not None:
            print(f"Emails found on {url}:")
            print(email_df)
        else:
            print(f"No emails found on {url}.")

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
        #'https://www.dlsu.edu.ph/research/offices/urco/',
        #'https://www.dlsu.edu.ph/offices/registrar/',
        'https://www.dlsu.edu.ph/colleges/cla/academic-departments/political-science/faculty-profile/',
        # Add more URLs here
        ]
        scrape_pages(urls_to_scrape)

