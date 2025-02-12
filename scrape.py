import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import json
import os

# Scrape YC directory and extract startup links
def scrape_website(website, progress_bar=None, max_scrolls=30):
    print("Launching Chrome browser headlessly...")
    
    chrome_driver_path = "./chromedriver.exe"
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    
    try:
        driver.get(website)
        print("Page loaded...")
        time.sleep(5)  # Initial load wait

        last_height = driver.execute_script("return document.body.scrollHeight")
        scrolls = 0

        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more content to load.")
                break
            
            last_height = new_height
            scrolls += 1
            print(f"Scrolled {scrolls}/{max_scrolls} times")

            # Update progress bar
            if progress_bar:
                progress_bar.progress(scrolls / max_scrolls)
        
        return driver.page_source  # Return the full HTML content
    
    finally:
        driver.quit()

# Extract startup details from the scraped HTML
def extract_startups(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    startup_data = []
    
    for card in soup.find_all("a", class_="_company_1pgsr_355"):
        try:
            name = card.find("span", class_="_coName_1pgsr_470").text.strip()
            location = card.find("span", class_="_coLocation_1pgsr_486").text.strip()
            year = card.find("span", class_="pill").text.strip()
            description = card.find("span", class_="_coDescription_1pgsr_495").text.strip()
            tags = [tag.text.strip() for tag in card.find_all("span", class_="pill")[1:]]  # Skip first pill (year)
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

# Save data to JSON
def save_to_json(data, filename):
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {file_path}")

# Load data from JSON
def load_from_json(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Visit each startup page while tracking progress
def visit_startups(startup_list, progress_bar=None, progress_file="progress.json", output_file="startup_pages.json"):
    if not startup_list:
        print("No startup data found. Make sure to scrape first!")
        if progress_bar:
            progress_bar.empty()
        return []

    progress = load_from_json(progress_file)
    visited_startups = load_from_json(output_file)

    if not isinstance(progress, dict):
        progress = {"last_index": -1}

    last_index = progress.get("last_index", -1)
    chrome_driver_path = "./chromedriver.exe"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    try:
        total_startups = len(startup_list)
        print(f"Visiting {total_startups} startups...")

        for i, startup in enumerate(startup_list):
            if i <= last_index:
                continue  # Skip already visited startups

            print(f"Visiting {i+1}/{total_startups}: {startup['name']}")

            try:
                driver.get(startup["link"])
                time.sleep(3)  # Allow page to load
                
                # Extract startup details
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                
                # Example: Extract the 'About' section
                about_section = soup.find("div", class_="about")
                about_text = about_section.text.strip() if about_section else "N/A"

                startup["about"] = about_text
                visited_startups.append(startup)

                # Save progress after every page visit
                save_to_json(visited_startups, output_file)

            except Exception as e:
                print(f"Error visiting {startup['name']}: {e}")
                break  # Exit the loop on critical error
            
            # Update progress bar
            if progress_bar:
                progress_bar.progress((i + 1) / total_startups)

            # Save last successful index
            progress["last_index"] = i
            save_to_json(progress, progress_file)

            time.sleep(1)  # Avoid overwhelming the server

    finally:
        driver.quit()

    return visited_startups  # Return the visited startup list
