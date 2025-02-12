from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as genai

# Configure Gemini API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. Extract Information: Only extract the information that directly matches the provided description: {parse_description}. "
    "2. No Extra Content: Do not include any additional text, comments, or explanations in your response. "
    "3. Empty Response: If no information matches the description, return an empty string ('')."
    "4. Direct Data Only: Your output should contain only the data that is explicitly requested, with no other text."
)

# Initialize Gemini Pro model
model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

def parse_with_gemini(dom_chunks, parse_description):
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    parsed_results = []

    for i, chunk in enumerate(dom_chunks, start=1):
        response = chain.invoke(
            {"dom_content": chunk, "parse_description": parse_description}
        )
        print(f"Parsed batch: {i} of {len(dom_chunks)}")
        parsed_results.append(response.content)  # Extract content from response

    return "\n".join(parsed_results)

