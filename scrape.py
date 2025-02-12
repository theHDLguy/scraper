import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import json
import os
import pandas as pd

def scrape_website(website):
    print('Launching Chrome browser headlessly...')
    
    chrome_driver_path = './chromedriver.exe'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")  # Disable GPU acceleration (useful for headless)
    options.add_argument("--no-sandbox")  # Bypass OS security model (useful in some environments)
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource issues in some cases

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    
    try:
        driver.get(website)
        print('Page loaded...')
        time.sleep(10)  # Give time for JavaScript-heavy content to load
        html = driver.page_source
        return html
    
    finally:
        driver.quit()

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    
    return str(body_content) if body_content else ""

def save_to_json(data, filename="scraped_data.json"):
    """ Save extracted content to a JSON file """
    file_path = os.path.join(os.getcwd(), filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"Data saved to {file_path}")

def save_to_csv(data, filename="scraped_data.csv"):
    """ Save extracted content to a CSV file """
    
    file_path = os.path.join(os.getcwd(), filename)
    df = pd.DataFrame([{"content": data}])
    df.to_csv(file_path, index=False, encoding="utf-8")
    
    print(f"Data saved to {file_path}")
