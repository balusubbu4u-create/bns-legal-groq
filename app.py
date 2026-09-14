import streamlit as st

# 1. Mandatory first Streamlit command
st.set_page_config(
    page_title="AI Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

import json
import os
import re
from openai import OpenAI
from io import BytesIO
from PIL import Image
import PyPDF2
import easyocr

# App UI Header
st.title("⚖️ BNS / BNSS / BSA Legal & Investigation Engine")
st.caption("భారతీయ నూతన నేర చట్టాల సమగ్ర దర్యాప్తు విశ్లేషణ వేదిక")

# Fetch API Key securely (Checks OpenAI, Groq, OpenRouter automatically)
api_key = None
base_url = None
is_groq = False

try:
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        base_url = None
    elif "openai_api_key" in st.secrets:
        api_key = st.secrets["openai_api_key"]
        base_url = None
    elif "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
        base_url = "https://api.groq.com/openai/v1"
        is_groq = True
    elif "groq_api_key" in st.secrets:
        api_key = st.secrets["groq_api_key"]
        base_url = "https://api.groq.com/openai/v1"
        is_groq = True
    elif "OPENROUTER_API_KEY" in st.secrets:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        base_url = "https://openrouter.ai/api/v1"
except Exception:
    pass

# Check Environment Variables as fallback
if not api_key:
    if os.environ.get("OPENAI_API_KEY"):
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = None
    elif os.environ.get("GROQ_API_KEY"):
        api_key = os.environ.get("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
        is_groq = True

if api_key:
    api_key = str(api_key).strip().strip('"').strip("'")

# Sidebar: Model Selection only (NO API key input field in sidebar)
st.sidebar.header("⚙️ మోడల్ ఎంపిక")

if is_groq:
    model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
else:
    model_options = ["gpt-4o", "gpt-4o-mini"]

selected_model = st.sidebar.selectbox(
    "మోడల్‌ను ఎంచుకోండి:",
    options=model_options,
    index=0
)

# Cache EasyOCR Reader for Telugu and English
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['te', 'en'], gpu=False)

# File text extraction handling PDF, Text, and Images via OCR
def extract_text_from_file(uploaded_file):
    uploaded_file.seek(0)
    file_extension = uploaded_file.name.split('.')[-1].lower()
    extracted_text = ""
    try:
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            for page in pdf_reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text += t + "\n"
        elif file_extension in ['jpg', 'jpeg', 'png']:
            image_bytes = uploaded_file.read()
            reader = load_ocr_reader()
            results = reader.readtext(image_bytes, detail=0)
            extracted_text = "\n".join(results)
        elif file_extension in ['txt', 'doc', 'docx']:
            extracted_text = uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        extracted_text = f"[Error reading file {uploaded_file.name}: {str(e)}]"
    return extracted_text

# Fail-safe Auto Repair JSON Parser
def repair_and_parse_json(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*
