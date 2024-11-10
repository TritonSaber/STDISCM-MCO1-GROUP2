import time
import threading
import pandas as pd
import re
import requests
import bs4
from bs4 import BeautifulSoup

http = requests.Session()

def fetch_headers(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the webpage content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dictionary to store headers
        headers = {
            "h1": [tag.get_text(strip=True) for tag in soup.find_all('h1')],
            "h2": [tag.get_text(strip=True) for tag in soup.find_all('h2')],
            "h3": [tag.get_text(strip=True) for tag in soup.find_all('h3')],
            "h4": [tag.get_text(strip=True) for tag in soup.find_all('h4')],
            "h5": [tag.get_text(strip=True) for tag in soup.find_all('h5')],
            "h6": [tag.get_text(strip=True) for tag in soup.find_all('h6')],
        }
        
        # Print headers found for inspection
        for header_level, texts in headers.items():
            print(f"{header_level} tags found:")
            for text in texts:
                print(f" - {text}")
        return headers
    else:
        print("Failed to retrieve the webpage.")
        return None

def fetch_emails(url):
    # Compile the email pattern
    #email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu.edu.ph')
    #email_pattern = re.compile(r'^[a-zA-Z0-9_.-]*[@](dlsu.edu.ph)')
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@dlsu\.edu\.ph')

    # Send a GET request to the URL
    response = http.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the webpage content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all text in the HTML that matches the email pattern
        emails = set(email_pattern.findall(soup.get_text()))
        
         # Set to store emails found
        emails = set()

        # Search for emails within "mailto:" links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('mailto:'):
                mailto_email = href[7:]  # Extract the email part after 'mailto:'
                if email_pattern.match(mailto_email):
                    emails.add(mailto_email)
        
        # Check if emails were found
        if emails:
            # Store emails in a DataFrame
            email_df = pd.DataFrame(emails, columns=["Email"])
            return email_df
        else:
            print("No emails found.")
            return None
    else:
        print("Failed to retrieve the webpage.")
        return None

if __name__ == '__main__':
    url = 'https://www.dlsu.edu.ph/'
    test_url = 'https://www.dlsu.edu.ph/research/offices/urco/'
    try:
        response = http.get(test_url, timeout=10)
        response.raise_for_status()
        print("Connection Success")
        print("Attempting to fetch...")
        email_df = fetch_emails(test_url)
        #print(email_df)
        if email_df is not None:
            if not email_df.empty:
                print("Emails found:")
                print(email_df)
            else:
                print("Email DataFrame is empty.")
        else:
            print("No emails or an error occurred.")

        print("The following is to be deleted, this is for testing, scraping <h_> tags in a website.")
        headers = fetch_headers(test_url)
        if headers:
            print("Headers success")
        else:
            print("No headers")
    except requests.exceptions.RequestException as e:
        print(f"Nope, Error: {e}")



