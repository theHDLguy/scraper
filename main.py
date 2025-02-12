import streamlit as st
from scrape import scrape_website, extract_startups, save_to_json, save_to_csv

# Streamlit UI
st.title('YC Directory Scraper')
url = st.text_input('Enter a Website URL: ')

if st.button("Scrape Website"):
    if url:
        st.write("Scraping the website...")
        
        # Scrape website and extract startup data
        dom_content = scrape_website(url)
        startup_data = extract_startups(dom_content)

        # Save data locally
        save_to_json(startup_data, "startups.json")
        save_to_csv(startup_data, "startups.csv")

        # Display extracted data
        st.write(f"Extracted {len(startup_data)} startups.")
        st.dataframe(startup_data)


# LLM integration:

# # Step 2: Ask Questions About the DOM Content
# if "dom_content" in st.session_state:
#     parse_description = st.text_area("Describe what you want to parse")

#     if st.button("Parse Content"):
#         if parse_description:
#             st.write("Parsing the content...")

#             # Parse the content with Gemini
#             parsed_result = parse_with_gemini(st.session_state.dom_content, parse_description)
            
#             st.write(parsed_result)
#             st.write("-- Parsing Done --")
