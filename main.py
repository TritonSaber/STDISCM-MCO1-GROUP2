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
statistics = {}

seen_emails = set()

# Functionalities to be done:
# Thread/Process Used
# Input arguments: URL of website, and Minutes given for scraping
# Output: Text file with email and associated name, offic, dep, OR unit in CSV format; Text file containing statistics of website: URL, num of pages scraped and num of email addr found

# Remember to delete the faculty_emails.txt cause itll append forever and idk how to refresh it without breaking. Statistics file is good though

def decodeEmail(e):
    #https://stackoverflow.com/questions/36911296/scraping-of-protected-email cause cloudfare cool
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e)-1, 2):
        de += chr(int(e[i:i+2], 16)^k)

    return de

def fetch_emails(url, start_time, time_limit):
    #Check for time
    elapsed_time = time.time() - start_time
    if elapsed_time > time_limit * 60:
        print("Time limit exceeded, stopping the scraping.")
        return [], True  # Return True to indicate time limit exceeded

    emails_found = 0
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
                    emails_found += 1

        end_time = time.time()
        thread_duration = end_time - start_time  # Time taken for the thread
        thread_times[url] = thread_duration

        statistics[url] ={
            'Pages Scraped': 1, #cause we're still manually putting urls in and not traversing them atm
            'Emails Found': emails_found
        }

        return faculty_info, False
    else:
        print("Failed to retrieve the webpage.")
        thread_times[url] = None
        return None, False

# Function to scrape multiple pages concurrently (IDK YET)
def scrape_pages(urls, time_limit):
    threads = []

    # Get the start time to monitor elapsed time
    start_time = time.time()

    for url in urls:
        thread = threading.Thread(target=scrape_page, args=(url, start_time, time_limit))
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
    
    write_statistics_to_file()

#    save_to_csv()

#def save_data_from_thread(url):
#    faculty_info = fetch_emails(url)
#
#    # Ensure thread-safe appending of data
#    with data_lock:
#        all_faculty_info.extend(faculty_info)

#def save_to_csv():
    # Convert collected data to a DataFrame and save it to a CSV file
#    if all_faculty_info:
#        df = pd.DataFrame(all_faculty_info)
#        df.to_csv('dlsu_emails.csv', index=False, encoding='utf-8')
#        print("Data saved to 'dlsu_emails.csv'")
#    else:
#        print("No data to save.")

def scrape_page(url, start_time, time_limit):
    # Scrape the page and fetch emails
    email_data, time_exceeded = fetch_emails(url, start_time, time_limit)
    
    #if time limit exceeded, no more scraping
    if time_exceeded:
        return

    # Write data to text file in CSV format
    if email_data:
        with open('faculty_emails.txt', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Name', 'Role', 'Email', 'Source'])
            
            # Write the header if the file is empty
            if f.tell() == 0:
                writer.writeheader()
                
            # Write the rows
            for row in email_data:
                writer.writerow(row)

        print(f"Data for {url} saved.")
    else:
        print(f"No data found for {url}.")

# Function to write statistics to a text file
def write_statistics_to_file():
    total_time_elapsed = time.time() - start_time_total
    remaining_time = (time_limit * 60) - total_time_elapsed
    remaining_time = max(remaining_time, 0)  # Avoid negative remaining time

    with open('scrape_statistics.txt', 'w', encoding='utf-8') as f:
        f.write("Scrape Statistics\n")
        f.write("====================\n")
        for url, stats in statistics.items():
            f.write(f"URL: {url}\n")
            f.write(f"  Pages Scraped: {stats['Pages Scraped']}\n")
            f.write(f"  Emails Found: {stats['Emails Found']}\n")

            if url in thread_times:
                duration = thread_times[url]
                f.write(f"  Time Taken: {duration:.2f} seconds\n")
            else:
                f.write(f"  Time Taken: Failed to scrape or skipped\n")

            f.write("====================\n")
        f.write(f"Total Time Elapsed: {total_time_elapsed:.2f} seconds\n")
        f.write(f"Remaining Time: {remaining_time:.2f} seconds\n")
        f.write(f"Threads Used: {len(thread_times)}\n")


if __name__ == '__main__':
    time_limit = int(input("Enter the maximum number of minutes the program can run: "))
    start_time_total = time.time()
    phase = 2 #1 for manual(outdated kinda), 2 for threads kind of
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
        scrape_pages(urls_to_scrape, time_limit)

