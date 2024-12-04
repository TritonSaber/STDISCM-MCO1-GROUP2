import time
import threading
import requests
from bs4 import BeautifulSoup
import csv
from tasks import app

http = requests.Session()

# Create a lock object for synchronization
data_lock = threading.Lock()

all_faculty_info = []

thread_times = {}
statistics = {}

seen_emails = set()

# Remember to delete the faculty_emails.txt cause itll append forever and idk how to refresh it without breaking. Statistics file is good though

def decodeEmail(e):
    #https://stackoverflow.com/questions/36911296/scraping-of-protected-email
    try:
        if not e:
            return None
        de = ""
        k = int(e[:2], 16)

        for i in range(2, len(e)-1, 2):
            de += chr(int(e[i:i+2], 16)^k)

        return de
    except ValueError as ve:
        print(f"Error decoding email: {ve} - Invalid email format: {e}")
        return None

def fetch_emails(url, start_time, time_limit):
    #Check for time
    elapsed_time = time.time() - start_time
    if elapsed_time > time_limit * 60:
        print("Time limit exceeded, stopping the scraping.")
        return [], True  # Return True to indicate time limit exceeded

    emails_found = 0

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
            
            if 'faculty-profile' in url or 'faculty' in url:
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
            if role_tag and 'faculty-profile' in url or role_tag and 'faculty' in url:
                for a_tag in role_tag.find_all('a'):
                    a_tag.decompose()  # Remove <a> tag 
                for strong_tag in role_tag.find_all('strong'):
                    strong_tag.decompose() # Remove <strong> tag
                # Now get the role text without any <a> tags
                role_text = role_tag.get_text(strip=True)
            else:
                role_text = 'Not applicable'

            source_url = url

            if email_text not in seen_emails:
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

        if url in statistics:
            statistics[url]['Pages Scraped'] += 1
            statistics[url]['Emails Found'] += emails_found
        else:
            statistics[url] = {
                'Pages Scraped': 1,  # First page visit for this URL/cause we're still manually putting urls in and not traversing them atm
                'Emails Found': emails_found
            }

        return faculty_info, False
    else:
        print("Failed to retrieve the webpage.")
        thread_times[url] = None
        return None, False

# Function to scrape multiple pages concurrently (IDK YET)
def scrape_pages(urls_to_scrape, time_limit):
    results = app.send_multiple(
        tasks=[scrape_page.s(url, time_limit) for url in urls_to_scrape],
        async=True
    )
    # Collect results and statistics from worker responses
    # (explained in the next step)

    # Update your statistics writing logic to handle collected data
    write_statistics_to_file.delay(collected_data)

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
    total_pages = sum(stats['Pages Scraped'] for stats in statistics.values())
    total_emails = sum(stats['Emails Found'] for stats in statistics.values())
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
        f.write("Overall Statistics:\n")
        f.write(f"Base URL: {base_url}\n")
        f.write(f"Total Pages Scraped: {total_pages}\n")
        f.write(f"Total Emails Found: {total_emails}\n")
        f.write(f"Total Time Elapsed: {total_time_elapsed:.2f} seconds\n")
        f.write(f"Remaining Time: {remaining_time:.2f} seconds\n")
        f.write(f"Threads Used: {len(thread_times)}\n")

def get_internal_links(url, visited=None, depth=0, max_depth=10): #3 stops at 13 seconds, 5, 10... tooo, kinda hard, even 100...
    if visited is None:
        visited=set()

    try:
        if url in visited or depth > max_depth:
            return visited

        # Send a GET request to the URL
        response = http.get(url)
        response.raise_for_status()  # Raise an exception for bad responses (4xx/5xx)

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links in the page
        links = soup.find_all('a', href=True) + soup.find_all('link', href=True)

        internal_links = set()

        # Filter the links to only include those that belong to the domain
        for link in links:
            href = link['href']
            if href.endswith('.pdf') or href.endswith('.css') or href.endswith('.png') or href.endswith('.io'): # we hate pdfs
                continue
            if href.startswith('/') or href.startswith('https://www.dlsu.edu.ph'):
                # Resolve relative links
                if href.startswith('/'):
                    href = 'https://www.dlsu.edu.ph' + href
                if href not in visited:
                    visited.add(href)
                    internal_links.add(href)
                    get_internal_links(href, visited, depth+1, max_depth)

        return visited
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve or parse {url}: {e}")
        return visited

if __name__ == '__main__':
    time_limit = int(input("Enter the maximum number of minutes the program can run: "))
    base_url = input("Enter the base URL to start scraping from: ")
    phase = int(input("Enter to use either scrape a set + your url (2), or search scrape (3): "))
    start_time_total = time.time()
    #phase = 2 #1 for manual(outdated), 2 for threads kind of, 3 for automatic crawling: Also these are all hardcoded, so dev tests- make sure to set to right phase when passing
    
    #I should remove this but keeping this for posterity- single search scrape for testing.
    if phase == 1:
        #url = 'https://www.dlsu.edu.ph/'
        #test_url = 'https://www.dlsu.edu.ph/research/offices/urco/'
        try:
            response = http.get(base_url, timeout=10)
            response.raise_for_status()
            print("Connection Success")
            print("Attempting to fetch...")
            email_df = fetch_emails(base_url)
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
        'https://www.dlsu.edu.ph/research/offices/urco/',
        'https://www.dlsu.edu.ph/offices/registrar/',
        'https://www.dlsu.edu.ph/colleges/cla/academic-departments/communication/faculty/',
        #'https://www.dlsu.edu.ph/colleges/cla/academic-departments/political-science/faculty-profile/', 
        base_url,
        ]
        scrape_pages(urls_to_scrape, time_limit)

    if phase == 3:
        urls_to_scrape = get_internal_links(base_url)
        scrape_pages(urls_to_scrape, time_limit)

        # Checking what urls can be gotten
        #for link in urls_to_scrape:
        #    print(link)
