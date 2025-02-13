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
            description = card.find("span", class_="_coDescription_1pgsr_495").text.strip()
            tags = [tag.text.strip() for tag in card.find_all("span", class_="pill")]  
            link = "https://www.ycombinator.com" + card["href"]
            
            startup_data.append({
                "name": name,
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
    
    startup_details = load_from_json(DETAILS_FILE)  # Load existing details
    existing_names = {s["name"] for s in startup_details}  # Track existing names
    
    try:
        total_startups = len(startup_list)
        for i, startup in enumerate(startup_list):
            if i <= last_index or startup["name"] in existing_names:
                continue  
            try:
                driver.get(startup["link"])
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                active_status = "Active" if soup.find("div", string=lambda text: text and "Active" in text) else "Inactive"
                industries = [a.text.strip() for a in soup.find_all("a", href=lambda href: href and "/companies/industry/" in href)]
                about_section = soup.find("div", class_="about")
                about_text = about_section.text.strip() if about_section else "N/A"
                
                startup_details.append({
                    "name": startup["name"],
                    "description": startup["description"],
                    "tags": startup["tags"],
                    "link": startup["link"],
                    "active_status": active_status,
                    "industries": industries,
                    "about": about_text
                })
                
                progress["last_index"] = i
                save_to_json(progress, PROGRESS_FILE)
                save_to_json(startup_details, DETAILS_FILE)
                if progress_bar:
                    progress_bar.progress((i + 1) / total_startups)
            except (TimeoutException, WebDriverException) as e:
                logging.error(f"Error scraping {startup['name']}: {e}")
                break  
            time.sleep(1)
    finally:
        driver.quit()

# Streamlit UI
st.title('YC Directory Scraper')

if not os.path.exists(STARTUPS_FILE) or not load_from_json(STARTUPS_FILE):
    url = st.text_input('Enter YC Directory URL:', "https://www.ycombinator.com/companies")
    if st.button("Scrape Startups"):
        if url:
            st.write("Scraping the website...")
            progress_bar = st.progress(0)
            dom_content = scrape_website(url, progress_bar=progress_bar)
            startup_data = extract_startups(dom_content)
            save_to_json(startup_data, STARTUPS_FILE)
            st.success(f"Extracted {len(startup_data)} startups. Data saved to {STARTUPS_FILE}")
else:
    st.write("Startups data found!")
    if st.button("Scrape Startup Details"):
        startup_data = load_from_json(STARTUPS_FILE)
        if not startup_data:
            st.error("No startup data found! Please scrape the website first.")
        else:
            scrape_progress = st.progress(0)
            scrape_startup_pages(startup_data, progress_bar=scrape_progress)
            scrape_progress.progress(1.0)
            st.success("Finished scraping startup details!")
