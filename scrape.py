import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import json
import os
import pandas as pd

def scrape_website(website, max_scrolls=30):
    print('Launching Chrome browser headlessly...')
    
    chrome_driver_path = './chromedriver.exe'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    
    try:
        driver.get(website)
        print('Page loaded...')
        time.sleep(5)  # Initial page load

        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new content to load
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more content to load.")
                break

            last_height = new_height
            scrolls += 1
            print(f"Scrolled {scrolls}/{max_scrolls} times")

        html = driver.page_source
        return html

    finally:
        driver.quit()


def extract_startups(html_content):
    """Extracts startup details from the scraped HTML"""
    soup = BeautifulSoup(html_content, "html.parser")
    startup_data = []

    for card in soup.find_all("a", class_="_company_1pgsr_355"):
        try:
            name = card.find("span", class_="_coName_1pgsr_470").text.strip()
            location = card.find("span", class_="_coLocation_1pgsr_486").text.strip()
            year = card.find("span", class_="pill").text.strip()
            description = card.find("span", class_="_coDescription_1pgsr_495").text.strip()
            tags = [tag.text.strip() for tag in card.find_all("span", class_="pill")[1:]]  # Skip the first pill (year)
            link = "https://www.ycombinator.com" + card["href"]

            startup_data.append({
                "name": name,
                "location": location,
                "year": year,
                "description": description,
                "tags": ", ".join(tags),
                "link": link
            })

        except AttributeError:
            continue  # Skip if any element is missing

    return startup_data


def save_to_json(data, filename="startups.json"):
    """Save extracted startups to a JSON file"""
    file_path = os.path.join(os.getcwd(), filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"Data saved to {file_path}")


def save_to_csv(data, filename="startups.csv"):
    """Save extracted startups to a CSV file"""
    file_path = os.path.join(os.getcwd(), filename)
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False, encoding="utf-8")
    
    print(f"Data saved to {file_path}")
