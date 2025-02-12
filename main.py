import streamlit as st
from scrape import scrape_website, extract_startups, save_to_json, load_from_json, visit_startups
import os

st.title('YC Directory Scraper')

# User inputs website URL
url = st.text_input('Enter YC Directory URL:', value="https://www.ycombinator.com/companies")

if st.button("Scrape Startups"):
    if url:
        st.write("Scraping the website...")
        progress_bar = st.progress(0)  # Initialize progress bar
        dom_content = scrape_website(url, progress_bar=progress_bar)
        startup_data = extract_startups(dom_content)
        save_to_json(startup_data, "startups.json")
        st.write(f"Extracted {len(startup_data)} startups. Data saved to startups.json")

if os.path.exists("startups.json"):
    if st.button("Visit Startups & Extract Details"):
        startup_data = load_from_json("startups.json")
        if not startup_data:
            st.error("No startup data found! Please scrape the website first.")
        else:
            visit_progress = st.progress(0)
            visit_startups(startup_data, progress_bar=visit_progress)  # ✅ Removed unnecessary argument
            st.success("Finished visiting startup pages. Data updated!")
