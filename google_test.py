import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs

# Setup Selenium WebDriver
options = Options()
options.headless = False  # Set to True to run the browser in headless mode
service = Service('C:/Users/Al Rehman Computers/Desktop/web driver/geckodriver-v0.35.0-win64/geckodriver.exe')
driver = webdriver.Firefox(service=service, options=options)

# Define search query and construct dynamic filename
search_query = 'law firms india'
search_query_safe = search_query.replace(' ', '_').replace('+', '_')  # Make the query URL-safe
filename = f'{search_query_safe}.csv'

# CSV file setup
fields = ['Title', 'Link', 'Website', 'Emails', 'Phone Numbers', 'Social Media Links', 'Stars', 'Reviews', 'Phone']

# Check if the CSV file exists; if not, create it and add headers
try:
    with open(filename, 'r'):
        pass
except FileNotFoundError:
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(fields)

# Navigate to the Google Maps URL
url = 'https://www.google.com/maps/search/law+firms+india/@18.9981541,65.8702213,5z?entry=ttu&g_ep=EgoyMDI0MDgyMS4wIKXMDSoASAFQAw%3D%3D'
driver.get(url)

# Wait for the page to load completely
time.sleep(3)  # Static wait; replace with dynamic wait if necessary

# Find the scrollable div within the page
scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

# Execute a script to scroll through the scrollable div
driver.execute_script("""
    var scrollableDiv = arguments[0];
    var endClassName = arguments[1];
    
    function scrollWithinElement(scrollableDiv, endClassName) {
        return new Promise((resolve, reject) => {
            var totalHeight = 0;
            var distance = 500;
            var scrollDelay = 5000;

            var timer = setInterval(() => {
                var scrollHeightBefore = scrollableDiv.scrollHeight;
                scrollableDiv.scrollBy(0, distance);
                totalHeight += distance;

                setTimeout(() => {
                    var scrollHeightAfter = scrollableDiv.scrollHeight;

                    // Check if the end class element is in view
                    var endElement = scrollableDiv.querySelector('.' + endClassName);
                    var endElementInView = endElement && endElement.getBoundingClientRect().top <= window.innerHeight;

                    if (scrollHeightAfter > scrollHeightBefore && !endElementInView) {
                        // Continue scrolling if new content is loaded and end class element is not in view
                        totalHeight = 0; // Reset the total height to continue scrolling
                    } else {
                        // Stop scrolling if no new content is loaded or end class element is in view
                        clearInterval(timer);
                        resolve();
                    }
                }, scrollDelay);
            }, 200);
        });
    }
    return scrollWithinElement(scrollableDiv, 'm6QErb.XiKgde.tLjsW.eKbjU');
""", scrollable_div)

# Find all relevant items within the scrollable div
items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')

for item in items:
    data = {}
    try:
        data['Title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
    except Exception:
        data['Title'] = "Not found"

    try:
        data['Link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
    except Exception:
        data['Link'] = "Not found"

    try:
        data['Website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
        
        url = data['Website']  # Replace with the target website
        response = requests.get(url)
        html_content = response.text

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'lxml')

        # Define Regex Patterns
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'\+?\d{1,4}?[\s.-]?\(?\d{1,4}?\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}'
        social_media_pattern = r'(https?://(?:www\.)?(?:facebook|twitter|instagram|linkedin|youtube|tiktok|pinterest)\.com/[a-zA-Z0-9_/?=&-]+)'

        # Use Regex to find all emails, phone numbers, and social media links in the text
        data['Emails'] = ', '.join(re.findall(email_pattern, soup.get_text()))
        data['Phone Numbers'] = ', '.join(re.findall(phone_pattern, soup.get_text()))
        data['Social Media Links'] = ', '.join(re.findall(social_media_pattern, html_content))

    except Exception:
        data['Website'] = "Not found"
        data['Emails'] = ""
        data['Phone Numbers'] = ""
        data['Social Media Links'] = ""

    try:
        rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
        rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]

        if rating_numbers:
            data['Stars'] = rating_numbers[0]
            data['Reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
        else:
            data['Stars'] = "Not found"
            data['Reviews'] = "Not found"
    except Exception:
        data['Stars'] = "Not found"
        data['Reviews'] = "Not found"

    try:
        text_content = item.text
        phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
        matches = re.findall(phone_pattern, text_content)

        phone_numbers = [match[0] for match in matches]
        unique_phone_numbers = list(set(phone_numbers))

        data['Phone'] = unique_phone_numbers[0] if unique_phone_numbers else "Phone Number not found"
    except Exception:
        data['Phone'] = "Not found"

    # Append the data to the CSV file
    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writerow(data)

    print("-" * 50)  # Divider between each result

# Close the Selenium WebDriver
driver.quit()

print(f"Scraping completed. Data has been saved to {filename}.")
