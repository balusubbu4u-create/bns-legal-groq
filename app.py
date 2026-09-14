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

# App UI Header
st.title("⚖️ BNS / BNSS / BSA Legal & Investigation Engine")
st.caption("Powered by Groq API | భారతీయ నూతన నేర చట్టాల సమగ్ర దర్యాప్తు విశ్లేషణ వేదిక")

# Fetch Groq API Key securely from Streamlit Secrets or Environment Variables
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
    elif "groq_api_key" in st.secrets:
        api_key = st.secrets["groq_api_key"]
    elif "OPENROUTER_API_KEY" in st.secrets:
        api_key = st.secrets["OPENROUTER_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

# Clean key
if api_key:
    api_key = str(api_key).strip().strip('"').strip("'")

# Sidebar for Model Selection and Key fallback
st.sidebar.header("⚙️ సెట్టింగ్స్")
selected_model = st.sidebar.selectbox(
    "మోడల్‌ను ఎంచుకోండి:",
    options=["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.1-8b-instant"],
    index=0
)

if not api_key:
    st.sidebar.warning("⚠️ Groq API కీ లభించలేదు.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_...) ని ఇక్కడ నమోదు చేయండి:", type="password")
    if api_key:
        api_key = str(api_key).strip().strip('"').strip("'")

base_url = "https://api.groq.com/openai/v1"

# Helper function to extract text from uploaded files (PDF, Images, TXT)
def extract_text_from_file(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    extracted_text = ""
    
    try:
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif file_extension in ['jpg', 'jpeg', 'png']:
            img = Image.open(uploaded_file)
            extracted_text = f"[Attached Image File: {uploaded_file.name} of size {img.size}]\n"
        elif file_extension in ['txt', 'doc', 'docx']:
            extracted_text = uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        extracted_text = f"[Error reading file {uploaded_file.name}: {str(e)}]"
        
    return extracted_text

# System Prompt with Strict Legal Guardrails
SYSTEM_PROMPT = """
Role: You are an authoritative Indian Criminal Law Decision-Engine specialized in Bharatiya Nyaya Sanhita (BNS, 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023), Bharatiya Sakshya Adhiniyam (BSA, 2023), and Special Acts (such as IT Act, 2000).

Task: Analyze the user complaint and uploaded document contents (any crime type: Cyber/Financial Fraud, Assault/Bodily Harm, Property Damage/Theft, Threats/Criminal Intimidation, Women/Child Safety, Breach of Trust, etc.) and extract strict statutory sections, procedural guidelines, evidence rules, and IO action checklists.

Strict Legal Guardrails:
1. Strict Ingredient Matching:
   - Identify the exact complaint category.
   - Do NOT guess or hallucinate sections. Only assign a section if facts fulfill statutory legal ingredients.
   - BNS 319(2) (Cheating by personation): Max punishment is strictly up to 5 years, or fine, or both. Classification: Cognizable, Bailable.
   - BNS 318(4) (Cheating & dishonest inducement): Max 7 years and fine. Classification: Cognizable, Non-Bailable.
   - IT Act 66D: Add ONLY if cheating was done using a computer resource/communication device.
   - IT Act 66C: Add ONLY if electronic signature, password, or unique identification feature was dishonestly stolen/used.
   - Bodily Harm/Assault/Threats: Map to relevant BNS sections (e.g., Sec 115, Sec 351, Sec 352, etc.).

2. BNSS Procedure Guidelines:
   - Section 173(3) BNSS: Preliminary Enquiry (PE) up to 14 days is permissible ONLY for offences punishable with 3 years or more but less than 7 years, strictly requiring PRIOR PERMISSION of an officer not below the rank of DSP. For urgent cyber/financial asset preservation, direct FIR is preferable.
   - Section 35(3) BNSS: Notice of Appearance is statutory before arrest for offences punishable with less than 7 years, unless specific conditions for arrest are recorded in writing.
   - Section 187(3) BNSS: Clarify that the statutory 60-day period (for offences punishable with under 10 years) or 90-day period (for offences punishable with death/life/10+ years) is the maximum detention threshold for default bail purposes.
   - Section 193 BNSS: Final report must be submitted without unnecessary delay, and progress must be reported to the informant every 90 days under Sec 193(3)(ii).

3. BSA Evidence Compliance:
   - Section 63(4) BSA: Require prescribed certification from the responsible person/entity in charge of the computer/device or management for any electronic evidence.
   - Section 105 BNSS: Mandatory audio-video electronic recording during search and seizure.
   - Section 176(3) BNSS: Mandatory crime scene forensic visit for offences punishable with 7+ years, subject to state notification framework.

Output Schema:
CRITICAL: Respond ONLY with a valid JSON object. Do not include markdown codeblocks, thinking steps, or introductory text.
{
  "complaint_category": "string",
  "key_facts": ["string"],
  "applicable_sections": [
    {
      "act": "string",
      "section": "string",
      "offence_name": "string",
      "punishment": "string",
      "classification": "string",
      "justification": "string"
    }
  ],
  "bnss_procedure": {
    "fir_or_pe_rule": "string",
    "notice_or_arrest": "string",
    "detention_default_bail_timeline": "string",
    "victim_update_rule": "string"
  },
  "bsa_evidence_rules": {
    "electronic_evidence_cert": "string",
    "videography_rule": "string",
    "forensic_visit_rule": "string"
  },
  "io_action_checklist": ["string"]
}
"""

# Input Area for Text Complaint
user_complaint = st.text_area(
    "ఫిర్యాదు వివరాలను టైప్ చేయండి (Complaint Text):",
    placeholder="ఉదాహరణ: సైబర్ మోసం, శారీరక దాడి, బెదిరింపులు లేదా దొంగతనం వివరాలు...",
    height=150
)

# File Uploader for PDF, JPG, PNG, Screenshots
uploaded_files = st.file_uploader(
    "సంబంధిత డాక్యుమెంట్లు, PDFలు, స్క్రీన్‌షాట్లు లేదా ఇమేజ్‌లను అప్‌లోడ్ చేయండి (Multiple files allowed):",
    type=["pdf", "jpg", "jpeg", "png", "txt"],
    accept_multiple_files=True
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    analyze_button = st.button("విశ్లేషించు (Analyze)", type="primary", use_container_width=True)

if analyze_button:
    if not api_key:
        st.error("❌ Groq API కీ కనుగొనబడలేదు. దయచేసి Streamlit Secrets లో `GROQ_API_KEY` ని కాన్ఫిగర్ చేయండి లేదా సైడ్‌బార్‌లో నమోదు చేయండి.")
    elif not user_complaint.strip() and not uploaded_files:
        st.warning("దయచేసి ఫిర్యాదు పాఠ్యాన్ని నమోదు చేయండి లేదా ఏదైనా డాక్యుమెంట్/స్క్రీన్‌షాట్ అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner(f"ఫిర్యాదు వివరాలను `{selected_model}` ద్వారా విశ్లేషిస్తోంది..."):
            try:
                combined_content = f"User Complaint Text:\n{user_complaint}\n\n"
                
                if uploaded_files:
                    combined_content += "--- Attached Documents / Files Content ---\n"
                    for file in uploaded_files:
                        file_text = extract_text_from_file(file)
                        combined_content += f"\nFile Name: {file.name}\n{file_text}\n"

                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )

                # Calling without strict JSON constraint to avoid 400 validation aborts on reasoning models
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this complaint and attached documents, then return the report in exact JSON format:\n\n{combined_content}"}
                    ],
                    temperature=0.1
                )

                raw_output = response.choices[0].message.content.strip()

                # Robust JSON extraction using Regex
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    clean_json = json_match.group(0)
                else:
                    clean_json = raw_output

                report_data = json.loads(clean_json)

                st.success("విశ్లేషణ విజయవంతంగా పూర్తయింది!")
                st.markdown(f"### 📂 నేరం వర్గం: `{report_data.get('complaint_category', 'General Offence')}`")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📌 ముఖ్య వాస్తవాలు (Facts)",
                    "⚖️ వర్తించే సెక్షన్లు (Sections)",
                    "🏛️ BNSS ప్రక్రియలు (Procedures)",
                    "🔍 BSA ఆధారాలు & ఫోరెన్సిక్స్",
                    "📋 IO యాక్షన్ చెక్‌లిస్ట్"
                ])

                with tab1:
                    st.subheader("ఫిర్యాదు & డాక్యుమెంట్ల నుండి సేకరించిన ప్రాథమిక అంశాలు")
                    for fact in report_data.get("key_facts", []):
                        st.markdown(f"* {fact}")

                with tab2:
                    st.subheader("BNS / IT Act / ఇతర చట్టాల సెక్షన్లు & శిక్షల వివరాలు")
                    sections = report_data.get("applicable_sections", [])
                    if sections:
                        for sec in sections:
                            with st.expander(f"{sec.get('act')} — {sec.get('section')}: {sec.get('offence_name')}", expanded=True):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.write(f"**శిక్ష (Punishment):** {sec.get('punishment')}")
                                with c2:
                                    st.write(f"**వర్గీకరణ:** {sec.get('classification')}")
                                st.write(f"**చట్టపరమైన సమర్థన (Legal Justification):** {sec.get('justification')}")
                    else:
                        st.info("నిర్దిష్ట సెక్షన్లు గుర్తించబడలేదు.")

                with tab3:
                    st.subheader("BNSS దర్యాప్తు గడువులు మరియు నిబంధనలు")
                    bnss = report_data.get("bnss_procedure", {})
                    st.markdown(f"**1. FIR / ప్రాథమిక విచారణ (Section 173(3) BNSS):**\n\n{bnss.get('fir_or_pe_rule')}")
                    st.markdown("---")
                    st.markdown(f"**2. హాజరు నోటీసు / అరెస్ట్ (Section 35 BNSS):**\n\n{bnss.get('notice_or_arrest')}")
                    st.markdown("---")
                    st.markdown(f"**3. డిఫాల్ట్ బెయిల్ / నిర్బంధ పరిమితి (Section 187(3) BNSS):**\n\n{bnss.get('detention_default_bail_timeline')}")
                    st.markdown("---")
                    st.markdown(f"**4. బాధితునికి పురోగతి నివేదిక (Section 193(3)(ii) BNSS):**\n\n{bnss.get('victim_update_rule')}")

                with tab4:
                    st.subheader("సాక్ష్యాధారాల ధ్రువీకరణ & ఫోరెన్సిక్ మార్గదర్శకాలు")
                    bsa = report_data.get("bsa_evidence_rules", {})
                    st.markdown(f"**ఎలక్ట్రానిక్ ఆధారాల ధ్రువీకరణ (Section 63(4) BSA):**\n\n{bsa.get('electronic_evidence_cert')}")
                    st.markdown("---")
                    st.markdown(f"**సెర్చ్ & సీజర్ వీడియోగ్రఫీ (Section 105 BNSS):**\n\n{bsa.get('videography_rule')}")
                    st.markdown("---")
                    st.markdown(f"**ఫోరెన్సిక్ నిపుణుల సందర్శన (Section 176(3) BNSS):**\n\n{bsa.get('forensic_visit_rule')}")

                with tab5:
                    st.subheader("దర్యాప్తు అధికారి (IO) చేపట్టాల్సిన పనుల జాబితా")
                    for idx, task in enumerate(report_data.get("io_action_checklist", []), 1):
                        st.checkbox(task, key=f"io_task_{idx}")

            except json.JSONDecodeError:
                st.error("మోడల్ నుండి వచ్చిన సమాధానం సరిగ్గా JSON లోకి మారలేదు. దయచేసి మళ్లీ విశ్లేషించు బటన్ నొక్కండి.")
                st.code(raw_output)
            except Exception as e:
                st.error(f"విశ్లేషణ సమయంలో సమస్య ఏర్పడింది: {str(e)}")
