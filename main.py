import streamlit as st
from scrape import (
    scrape_website, 
    extract_body_content,
    save_to_json,
    save_to_csv
)
from parseGem import parse_with_gemini

# Streamlit UI
st.title('AI Web Scraper')
url = st.text_input('Enter a Website URL: ')

# Step 1: Scrape the Website
if st.button("Scrape Website"):
    if url:
        st.write("Scraping the website...")

        # Scrape the website
        dom_content = scrape_website(url)
        body_content = extract_body_content(dom_content)

        # Save the scraped data locally
        save_to_json(body_content, "scraped_data.json")
        save_to_csv(body_content, "scraped_data.csv")

        # Store in Streamlit session state
        st.session_state.dom_content = body_content

        # Display the DOM content
        with st.expander("View DOM Content"):
            st.text_area("DOM Content", body_content, height=300)

# Step 2: Ask Questions About the DOM Content
if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")

    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content...")

            # Parse the content with Gemini
            parsed_result = parse_with_gemini(st.session_state.dom_content, parse_description)
            
            st.write(parsed_result)
            st.write("-- Parsing Done --")
