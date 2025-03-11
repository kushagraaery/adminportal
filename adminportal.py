import streamlit as st
import pandas as pd
import openai
import base64
import requests
import json
from io import BytesIO
import os
from dotenv import load_dotenv

# Set OpenAI API Key (Replace with your key)
# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Add your GitHub token in the .env file
GITHUB_REPO = "kushagraaery/adminportal"  # Replace with your GitHub repo
BRANCH = "main"  # Change if needed
FILE_NAME = "Generated_Responses.xlsx"
BASE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_NAME}"

# Initialize session state
if "df_responses" not in st.session_state:
    st.session_state.df_responses = None

def generate_answer(society, question):
    """Fetch answer from OpenAI GPT model."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI assistant providing precise and relevant answers."},
            {"role": "user", "content": f"For the society '{society}', answer the following question: {question}"}
        ]
    )
    return response["choices"][0]["message"]["content"].strip()

# Helper function to update Excel file in GitHub
def update_excel_in_github(df):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(BASE_URL, headers=headers)
    sha = response.json().get("sha", "") if response.status_code == 200 else None
    
    # Convert DataFrame to binary Excel content
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    file_content = output.getvalue()
    
    # Prepare API payload
    payload = {
        "message": "Updated Excel file via Streamlit",
        "content": base64.b64encode(file_content).decode("utf-8"),
        "sha": sha
    }
    
    response = requests.put(BASE_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        st.success("Data updated successfully in GitHub repository!")
    else:
        st.error(f"Failed to update the data: {response.text}")

# Streamlit UI
st.title("Admin Portal")

st.sidebar.header("Upload Files")
society_file = st.sidebar.file_uploader("Upload Society Names (CSV/Excel)", type=["csv", "xlsx"])
questions_file = st.sidebar.file_uploader("Upload Questions (CSV/Excel)", type=["csv", "xlsx"])

generate_btn = st.sidebar.button("Generate Responses")

if society_file and questions_file:
    societies = pd.read_csv(society_file, usecols=[0]) if society_file.name.endswith("csv") else pd.read_excel(society_file, usecols=[0])
    questions = pd.read_csv(questions_file, usecols=[0]) if questions_file.name.endswith("csv") else pd.read_excel(questions_file, usecols=[0])
    
    societies = societies.iloc[:, 0].dropna().unique().tolist()
    questions = questions.iloc[:, 0].dropna().unique().tolist()
    
    if not societies or not questions:
        st.error("Ensure both files contain data in the first column.")
    else:
        if generate_btn:
            response_data = {"Society": societies}
            
            for question in questions:
                response_data[question] = [generate_answer(society, question) for society in societies]
            
            st.session_state.df_responses = pd.DataFrame(response_data)

if st.session_state.df_responses is not None:
    st.write("### Generated Responses")
    st.dataframe(st.session_state.df_responses)
    if st.button("Update the Database"):
        update_excel_in_github(st.session_state.df_responses)
