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
    # Compile the email pattern
    #email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu.edu.ph')
    #email_pattern = re.compile(r'^[a-zA-Z0-9_.-]*[@](dlsu.edu.ph)')
    #email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu\.edu\.ph')
    email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}') #just getting whatever email in the page
    # Send a GET request to the URL
    response = http.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the webpage content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Set to store emails found
        faculty_info = []
        seen_emails = set()

        # First, find emails in regular text (not encoded) (Not needed)
        # emails.update(email_pattern.findall(soup.get_text()))

        # Then, search for mailto: links and decode obfuscated emails
        for div in soup.find_all('div', class_="wpb_wrapper"):
            
            #href = div.find('a', href=lambda x: x and x.startswith('mailto'))
            name_tag = div.find('strong')
            role_tag = div.find('p')
            email_tag = div.find('a', href=True) 

            name_text = name_tag.get_text(strip=True) if name_tag else None
            role_text = role_tag.get_text(strip=True).replace(name_text, '').strip('" ') if role_tag and name_tag else None
            

            if email_tag:
                href = email_tag['href']
                if href.startswith('/cdn-cgi/l/email-protection'):
                    encoded_email = href.split('#')[-1]  # Get the encoded part after '#'
                    email_text = decodeEmail(encoded_email)
                elif href.startswith('mailto:'):
                    email_text = href[7:]  # Extract email after 'mailto:'
                else:
                    email_text = None

            if name_text and email_text not in seen_emails:
                faculty_info.append({
                    'Name': name_text,
                    'Role': role_text,
                    'Email': email_text
                })
                seen_emails.add(email_text)

            #if href.startswith('/cdn-cgi/l/email-protection'):
            ##    encoded_email = href.split('#')[-1]  # Get the encoded part after '#'
            #   decoded_email = decodeEmail(encoded_email)
                #print(decoded_email)
            #    emails.add(decoded_email)
            #else: #accounts for their names? possible never gets their names
            #    name.add(href)
        
        #for a_tag in soup.find_all('a', href=True):
        #    #link_text = a_tag.get_text(strip=True)
        #    href = a_tag['href']
        #    #print(f"Text: {link_text} | URL: {href}")
        #    if href.startswith('/cdn-cgi/l/email-protection'):
        #        encoded_email = href.split('#')[-1]  # Get the encoded part after '#'
        #        decoded_email = decodeEmail(encoded_email)
                #print(decoded_email)
        #        emails.add(decoded_email)
        #    else: #accounts for their names? possible never gets their names
        #        name.add(href)

        
        # Check if emails were found
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
    phase = 2 #1 for testing, 2 for threads kind of
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

            #dev test
            testing = 0
            if testing == 1:
                print("The following is to be deleted, this is for testing, scraping <h_> tags in a website.")
                headers = fetch_headers(test_url)
                if headers:
                    print("Headers success")
                else:
                    print("No headers")

                print("Fetching all <a> tag contents...")
                links = fetch_links(test_url)
                if links:
                    print("Links extracted successfully.")
                else:
                    print("No links or an error occurred.")

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

    if phase == 3:
        # Usage
        url = 'https://www.dlsu.edu.ph/colleges/cla/academic-departments/political-science/faculty-profile/'
        faculty_df = fetch_faculty_info(url)
        print(faculty_df)


    #sample = '86f3e8eff0e3f4f5eff2fff4e3f5e3e7f4e5eee5e9e9f4e2efe8e7f2efe9e8e9e0e0efe5e3c6e2eaf5f3a8e3e2f3a8f6ee'
    #test_decode_sample = decodeEmail(sample)
    #print(test_decode_sample) #decoding works but need to find out how to extract it

