import streamlit as st
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from bs4 import BeautifulSoup
import json
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CHROME_DRIVER_PATH = "./chromedriver.exe"
STARTUPS_FILE = "startups.json"
DETAILS_FILE = "startup_details.json"
PROGRESS_FILE = "progress.json"

# Utility Functions
def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Data saved to {filename}")

def load_from_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Step 1: Scrape Startup Listings
def scrape_website(website, progress_bar=None, max_scrolls=30):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    try:
        driver.get(website)
        time.sleep(3)
        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1
            if progress_bar:
                progress_bar.progress(scrolls / max_scrolls)
        
        return driver.page_source  
    finally:
        driver.quit()

def extract_startups(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    startup_data = []
    
    for card in soup.find_all("a", class_="_company_1pgsr_355"):
        try:
            name = card.find("span", class_="_coName_1pgsr_470").text.strip()
            location = card.find("span", class_="_coLocation_1pgsr_486").text.strip()
            year = card.find("span", class_="pill").text.strip()
            description = card.find("span", class_="_coDescription_1pgsr_495").text.strip()
            tags = [tag.text.strip() for tag in card.find_all("span", class_="pill")[1:]]  
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
            continue  
    
    return startup_data


# Step 2: Scrape Startup Pages
def scrape_startup_pages(startup_list, progress_bar=None):
    progress = load_from_json(PROGRESS_FILE) or {"last_index": -1}
    last_index = progress.get("last_index", -1)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    
    scraped_pages = {}
    try:
        total_startups = len(startup_list)
        for i, startup in enumerate(startup_list):
            if i <= last_index:
                continue  
            try:
                driver.get(startup["link"])
                time.sleep(3)
                scraped_pages[startup["name"]] = driver.page_source
                progress["last_index"] = i
                save_to_json(progress, PROGRESS_FILE)
                if progress_bar:
                    progress_bar.progress((i + 1) / total_startups)
            except (TimeoutException, WebDriverException) as e:
                logging.error(f"Error scraping {startup['name']}: {e}")
                break  
            time.sleep(1)
    finally:
        driver.quit()
    save_to_json(scraped_pages, "scraped_pages.json")

def extract_startup_details():
    scraped_pages = load_from_json("scraped_pages.json")
    if not scraped_pages:
        logging.error("No startup pages found! Scrape them first.")
        return []
    
    startup_details = []
    for name, html_content in scraped_pages.items():
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract active status
        active_status = "Inactive"
        active_div = soup.find("div", class_="yc-tw-Pill", string=lambda text: text and "Active" in text)
        if active_div:
            active_status = "Active"

        # Extract industries
        industries = [a.text.strip() for a in soup.find_all("a", href=lambda href: href and "/companies/industry/" in href)]

        # Extract location
        location = None
        location_tag = soup.find("a", href=lambda href: href and "/companies/location/" in href)
        if location_tag:
            location = location_tag.text.strip()
        
        
        about_section = soup.find("div", class_="about")
        about_text = about_section.text.strip() if about_section else "N/A"
        startup_details.append({"name": name, "about": about_text})
    save_to_json(startup_details, DETAILS_FILE)




















# Streamlit App
st.title('YC Directory Scraper')
url = st.text_input('Enter YC Directory URL:', "https://www.ycombinator.com/companies")

if st.button("Scrape Startups"):
    if url:
        st.write("Scraping the website...")
        progress_bar = st.progress(0)
        dom_content = scrape_website(url, progress_bar=progress_bar)
        startup_data = extract_startups(dom_content)
        save_to_json(startup_data, STARTUPS_FILE)
        st.write(f"Extracted {len(startup_data)} startups. Data saved to {STARTUPS_FILE}")

if os.path.exists(STARTUPS_FILE):
    if st.button("Scrape Startup Pages"):
        startup_data = load_from_json(STARTUPS_FILE)
        if not startup_data:
            st.error("No startup data found! Please scrape the website first.")
        else:
            scrape_progress = st.progress(0)
            scrape_startup_pages(startup_data, progress_bar=scrape_progress)
            scrape_progress.progress(1.0)
            st.success("Finished scraping startup pages!")
    
    if st.button("Extract Startup Details"):
        extract_startup_details()
        st.success(f"Extracted startup details successfully! Data saved to {DETAILS_FILE}")
