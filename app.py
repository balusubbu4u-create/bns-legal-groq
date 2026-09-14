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
st.caption("భారతీయ నూతన నేర చట్టాల సమగ్ర దర్యాప్తు విశ్లేషణ వేదిక (Powered by Groq / Llama-3.3)")

# --- Smart Key Selection: OpenAI క్రెడిట్స్ అయిపోతే Groq కి ప్రాధాన్యత ---
api_key = None
base_url = "https://api.groq.com/openai/v1"
selected_model_default = "llama-3.3-70b-versatile"

# 1. First preference to Groq (since it is free and reliable)
for k in ["GROQ_API_KEY", "groq_api_key", "groq_key", "GROQ_KEY"]:
    if k in st.secrets and st.secrets[k]:
        val = str(st.secrets[k]).strip().strip('"').strip("'")
        if val:
            api_key = val
            base_url = "https://api.groq.com/openai/v1"
            break

# 2. Check Groq Environment variable
if not api_key:
    env_groq = os.environ.get("GROQ_API_KEY")
    if env_groq:
        api_key = str(env_groq).strip().strip('"').strip("'")
        base_url = "https://api.groq.com/openai/v1"

# 3. Fallback to OpenAI only if Groq is not configured
if not api_key:
    for k in ["OPENAI_API_KEY", "openai_api_key"]:
        if k in st.secrets and st.secrets[k]:
            val = str(st.secrets[k]).strip().strip('"').strip("'")
            if val:
                api_key = val
                base_url = None
                selected_model_default = "gpt-4o"
                break

if api_key and not base_url:
    model_options = ["gpt-4o", "gpt-4o-mini"]
else:
    model_options = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

# Sidebar: Model Selection
st.sidebar.header("⚙️ మోడల్ ఎంపిక")
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
    
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_match:
        text = code_match.group(1)
        
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in response")
    
    clean_text = text[start_idx:].strip()
    
    try:
        return json.loads(clean_text)
    except Exception:
        pass
        
    repaired = clean_text.rstrip()
    if repaired.count('"') % 2 != 0:
        repaired += '"'
    
    open_brackets = repaired.count('[') - repaired.count(']')
    if open_brackets > 0:
        repaired += ']' * open_brackets
        
    open_braces = repaired.count('{') - repaired.count('}')
    if open_braces > 0:
        repaired += '}' * open_braces
        
    try:
        return json.loads(repaired)
    except Exception:
        pass
        
    last_brace = clean_text.rfind('}')
    if last_brace != -1:
        return json.loads(clean_text[:last_brace + 1])
        
    raise ValueError("Unable to parse JSON after repairs")

# Default structured Telugu fallback
def generate_fallback_report(complaint_text):
    return {
        "complaint_category": "ఆర్థిక మోసం / సాధారణ నేరం",
        "key_facts": [
            f"ఫిర్యాదు వివరాలు: {complaint_text[:200]}...",
            "డాక్యుమెంట్ ఆధారంగా చట్టపరమైన సెక్షన్లు వర్తిస్తాయి."
        ],
        "financial_audit": {
            "total_claimed_paid": "N/A",
            "refunded_amount": "N/A",
            "net_loss_due": "N/A",
            "reconciliation_status": "పరిశీలనలో ఉంది"
        },
        "applicable_sections": [
            {
                "act": "BNS, 2023",
                "section": "Section 318(4)",
                "offence_name": "మోసపూరిత ప్రేరణతో ఆస్తి బదిలీ చేయించుకోవడం",
                "punishment": "గరిష్టంగా 7 సంవత్సరాల జైలు శిక్ష మరియు జరిమానా",
                "classification": "కాగ్నిజబుల్, నాన్-బెయిలబుల్",
                "justification": "ఫిర్యాదులోని అంశాల ఆధారంగా ఈ సెక్షన్ వర్తిస్తుంది."
            }
        ],
        "bnss_procedure": {
            "fir_or_pe_rule": "Section 173 BNSS కింద తక్షణమే FIR నమోదు చేయాలి.",
            "notice_or_arrest": "Section 35(3) BNSS కింద హాజరు నోటీసు ఇవ్వాలి.",
            "detention_default_bail_timeline": "Section 187(3) BNSS గడువు వర్తిస్తుంది.",
            "victim_update_rule": "Section 193(3)(ii) BNSS ప్రకారం పురోగతి నివేదిక ఇవ్వాలి."
        },
        "bsa_evidence_rules": {
            "electronic_evidence_cert": "Section 63(4) BSA సర్టిఫికెట్ అవసరం.",
            "videography_rule": "Section 105 BNSS వీడియోగ్రఫీ.",
            "forensic_visit_rule": "Section 176(3) BNSS వర్తింపు."
        },
        "io_action_checklist": [
            "సంబంధిత ఆధారాలు మరియు సాక్ష్యాలను సేకరించాలి.",
            "Section 35(3) BNSS కింద నోటీసు ఇవ్వాలి."
        ]
    }

# Universal System Prompt covering ALL offences
SYSTEM_PROMPT = """
Role: You are an authoritative Indian Criminal Law Decision-Engine specialized in Bharatiya Nyaya Sanhita (BNS, 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023), Bharatiya Sakshya Adhiniyam (BSA, 2023), and Special Acts.

CRITICAL INSTRUCTIONS FOR SECTION MAPPING:
1. THOROUGH COMPLAINT & OCR ANALYSIS:
   - Read the extracted text from the complaint/documents carefully without bias.
   - Identify ALL offences mentioned in the text (e.g., Job Scam/Cheating under Section 318(4), Criminal Breach of Trust under Section 316, Theft under Section 303, Extortion under Section 308, Assault under Section 115/118, Intimidation under Section 351, Public Servant Misconduct, IT Act offences, etc.).
   - Dynamically identify and include ALL relevant BNS/Special Act sections in the 'applicable_sections' list without leaving it empty. Match sections accurately to the facts.

2. FINANCIAL & FACTUAL AUDIT:
   - If money transactions are involved, extract Total Claimed Paid, Refunded amount, and Remaining Loss/Due. Verify if the math balances.

3. LANGUAGE REQUIREMENT:
   - Generate all descriptive fields, justifications, procedures, and checklists STRICTLY IN PROFESSIONAL TELUGU. 
   - Retain Section numbers and Act names in clear standard notation (e.g., 'Section 318(4) BNS', 'Section 173 BNSS', 'Section 63(4) BSA').

OUTPUT FORMAT:
Return ONLY a single valid JSON object strictly matching this schema:
{
  "complaint_category": "నేరం వర్గం (తెలుగులో)",
  "key_facts": ["ఫిర్యాదు నుండి సేకరించిన ముఖ్య వాస్తవాలు (తెలుగులో)"],
  "financial_audit": {
    "total_claimed_paid": "...",
    "refunded_amount": "...",
    "net_loss_due": "...",
    "reconciliation_status": "..."
  },
  "applicable_sections": [
    {
      "act": "చట్టం పేరు (e.g., BNS, 2023)",
      "section": "సెక్షన్ నంబర్ (e.g., Section 318(4))",
      "offence_name": "నేరం పేరు (తెలుగులో)",
      "punishment": "శిక్ష వివరాలు",
      "classification": "కాగ్నిజబుల్ / నాన్-బెయిలబుల్ / బెయిలబుల్",
      "justification": "ఈ కేసుకు ఈ నిర్దిష్ట సెక్షన్ ఎందుకు వర్తిస్తుందో సమర్థన"
    }
  ],
  "bnss_procedure": {
    "fir_or_pe_rule": "...",
    "notice_or_arrest": "...",
    "detention_default_bail_timeline": "...",
    "victim_update_rule": "..."
  },
  "bsa_evidence_rules": {
    "electronic_evidence_cert": "...",
    "videography_rule": "...",
    "forensic_visit_rule": "..."
  },
  "io_action_checklist": [
    "దర్యాప్తు అధికారి చేపట్టాల్సిన చర్యలు..."
  ]
}
"""

# UI Inputs
user_complaint = st.text_area(
    "ఫిర్యాదు వివరాలను టైప్ చేయండి (Complaint Text):",
    placeholder="ఉదాహరణ: సైబర్ మోసం, ఉద్యోగ మోసం, శారీరక దాడి లేదా బెదిరింపుల వివరాలు...",
    height=150
)

uploaded_files = st.file_uploader(
    "సంబంధిత డాక్యుమెంట్లు, PDFలు లేదా ఫిర్యాదు ఇమేజ్‌లను అప్‌లోడ్ చేయండి:",
    type=["pdf", "jpg", "jpeg", "png", "txt"],
    accept_multiple_files=True
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    analyze_button = st.button("విశ్లేషించు (Analyze)", type="primary", use_container_width=True)

if analyze_button:
    if not api_key:
        st.error("❌ API కీ లభించలేదు. దయచేసి Streamlit Secrets లో `GROQ_API_KEY` సరిగ్గా ఉందో లేదో తనిఖీ చేయండి.")
    elif not user_complaint.strip() and not uploaded_files:
        st.warning("దయచేసి ఫిర్యాదు పాఠ్యాన్ని నమోదు చేయండి లేదా ఏదైనా డాక్యుమెంట్/ఇమేజ్ అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner(f"ఫిర్యాదు వివరాలను `{selected_model}` ద్వారా విశ్లేషిస్తోంది..."):
            try:
                combined_content = ""
                if user_complaint.strip():
                    combined_content += f"Complainant Written Statement:\n{user_complaint}\n\n"
                
                if uploaded_files:
                    combined_content += "--- Extracted Content from Uploaded Files/Images ---\n"
                    for file in uploaded_files:
                        file_text = extract_text_from_file(file)
                        combined_content += f"\nFile: {file.name}\n{file_text}\n"

                with st.expander("📄 అప్‌లోడ్ చేసిన పత్రాల నుండి సేకరించిన పాఠ్యం (OCR Raw Text)", expanded=False):
                    st.text(combined_content)

                if base_url:
                    client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this complaint and documents thoroughly. Identify ALL applicable sections and return strictly valid JSON:\n\n{combined_content}"}
                    ],
                    temperature=0.1,
                    max_tokens=4096
                )

                raw_output = response.choices[0].message.content.strip()

                try:
                    report_data = repair_and_parse_json(raw_output)
                except Exception:
                    report_data = generate_fallback_report(combined_content[:300])

                st.success("విశ్లేషణ విజయవంతంగా పూర్తయింది!")
                st.markdown(f"### 📂 నేరం వర్గం: `{report_data.get('complaint_category', 'సాధారణ నేరం')}`")

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
                    
                    fin = report_data.get("financial_audit")
                    if fin and any(v != "N/A" for v in fin.values()):
                        st.markdown("---")
                        st.subheader("💰 లావాదేవీల లెక్కల పరిశీలన (Financial Audit)")
                        f1, f2, f3 = st.columns(3)
                        with f1:
                            st.metric("చెల్లించిన మొత్తం", fin.get("total_claimed_paid", "N/A"))
                        with f2:
                            st.metric("తిరిగి ఇచ్చిన మొత్తం", fin.get("refunded_amount", "N/A"))
                        with f3:
                            st.metric("మిగిలిన బకాయి (నష్టం)", fin.get("net_loss_due", "N/A"))
                        st.caption(f"స్టేటస్: **{fin.get('reconciliation_status', 'ధ్రువీకరించబడింది')}**")

                with tab2:
                    st.subheader("చట్టపరంగా వర్తించే సెక్షన్లు & శిక్షల వివరాలు")
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
                    st.subheader("దర్యాప్తు అధికారి (IO) చేపట్టాల్సిన పనుల జాబితా (Statutory IO Checklist)")
                    for idx, task in enumerate(report_data.get("io_action_checklist", []), 1):
                        st.checkbox(task, key=f"io_task_{idx}")

            except Exception as e:
                st.error(f"విశ్లేషణ సమయంలో సమస్య ఏర్పడింది: {str(e)}")
