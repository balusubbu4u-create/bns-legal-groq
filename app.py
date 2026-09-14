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
st.caption("భారతీయ నూతన నేర చట్టాల సమగ్ర దర్యాప్తు విశ్లేషణ వేదిక (Powered by OpenAI GPT)")

# Fetch OpenAI API Key securely from Streamlit secrets or Environment
api_key = None
try:
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    elif "openai_api_key" in st.secrets:
        api_key = st.secrets["openai_api_key"]
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("OPENAI_API_KEY")

if api_key:
    api_key = str(api_key).strip().strip('"').strip("'")

# Sidebar: Configuration
st.sidebar.header("⚙️ సిస్టమ్ కాన్ఫిగరేషన్")

if not api_key:
    st.sidebar.warning("⚠️ OpenAI API కీ లభించలేదు.")
    api_key = st.sidebar.text_input("OpenAI API Key (sk-...) ని ఇక్కడ నమోదు చేయండి:", type="password")
    if api_key:
        api_key = str(api_key).strip().strip('"').strip("'")

available_models = ["gpt-4o", "gpt-4o-mini"]

selected_model = st.sidebar.selectbox(
    "OpenAI మోడల్‌ను ఎంచుకోండి:",
    options=available_models,
    index=0
)

# Cache EasyOCR Reader for Telugu and English to prevent repeated memory allocation
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

# Universal Dynamic System Prompt covering all legal provisions
SYSTEM_PROMPT = """
Role: You are an authoritative Indian Criminal Law Decision-Engine specialized in Bharatiya Nyaya Sanhita (BNS, 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023), Bharatiya Sakshya Adhiniyam (BSA, 2023), and Special Acts (Prevention of Corruption Act, IT Act, etc.).

CRITICAL INSTRUCTIONS FOR UNIVERSAL SECTION MAPPING:
1. THOROUGH COMPLAINT & OCR ANALYSIS:
   - Read the extracted text from the complaint/documents carefully without bias.
   - Accurately extract all offences described in the complaint (e.g., Cheating, Criminal Breach of Trust, Extortion, Physical Hurt/Assault, Criminal Intimidation, Forgery, Public Servant Misconduct, Cyber Fraud, etc.).
   - Dynamically identify and apply ALL legally applicable sections. Do NOT restrict to any single section.
   - If the accused is a Public Servant (e.g., Police Official), examine relevant provisions for public servant misconduct and criminal breach of trust.
   - Do NOT apply Cyber Crime sections (IT Act 66D / BNS 319) merely because payment was made via UPI/PhonePe unless actual digital impersonation or hacking occurred.

2. FINANCIAL & FACTUAL AUDIT:
   - If financial transactions are mentioned, extract: Total Amount Paid, Refunded Amount, and Net Outstanding / Loss. Verify whether the arithmetic balances.

3. STRICT TELUGU OUTPUT REQUIREMENT:
   - All descriptive text, key facts, legal justifications, procedural steps, and checklists MUST be generated STRICTLY IN PROFESSIONAL TELUGU.
   - Keep section numbers and act names explicit and standardized (e.g., 'Section 318(4) BNS', 'Section 316 BNS', 'Section 173 BNSS', 'Section 63(4) BSA').

OUTPUT FORMAT:
Return ONLY a single valid JSON object strictly matching this schema:
{
  "complaint_category": "నేరం వర్గం (తెలుగులో)",
  "key_facts": ["ఫిర్యాదు నుండి సేకరించిన ముఖ్య వాస్తవాలు (తెలుగులో)"],
  "financial_audit": {
    "total_claimed_paid": "చెల్లించిన మొత్తం (వర్తిస్తే, లేదంటే N/A)",
    "refunded_amount": "తిరిగి ఇచ్చిన మొత్తం (వర్తిస్తే, లేదంటే N/A)",
    "net_loss_due": "మిగిలిన బకాయి/నష్టం (వర్తిస్తే, లేదంటే N/A)",
    "reconciliation_status": "లెక్కల ధ్రువీకరణ స్థితి"
  },
  "applicable_sections": [
    {
      "act": "చట్టం పేరు (e.g., BNS, 2023)",
      "section": "సెక్షన్ నంబర్ (e.g., Section 318(4))",
      "offence_name": "నేరం పేరు (తెలుగులో)",
      "punishment": "శిక్ష వివరాలు",
      "classification": "కాగ్నిజబుల్ / నాన్-బెయిలబుల్ / బెయిలబుల్",
      "justification": "ఈ కేసుకు ఈ నిర్దిష్ట సెక్షన్ ఎందుకు వర్తిస్తుందో డాక్యుమెంట్ ఆధారిత సమర్థన"
    }
  ],
  "bnss_procedure": {
    "fir_or_pe_rule": "Section 173 BNSS కింద విచారణ లేదా FIR నిబంధన",
    "notice_or_arrest": "Section 35(3) BNSS కింద హాజరు నోటీసు / అరెస్ట్ మార్గదర్శకం",
    "detention_default_bail_timeline": "Section 187 BNSS కస్టడీ మరియు డిఫాల్ట్ బెయిల్ గడువు",
    "victim_update_rule": "Section 193(3)(ii) BNSS బాధితునికి దర్యాప్తు పురోగతి నివేదిక"
  },
  "bsa_evidence_rules": {
    "electronic_evidence_cert": "Section 63(4) BSA ఎలక్ట్రానిక్ సాక్ష్యాధారాల సర్టిఫికెట్ నిబంధన",
    "videography_rule": "Section 105 BNSS సెర్చ్ మరియు సీజర్ వీడియోగ్రఫీ నిబంధన",
    "forensic_visit_rule": "Section 176(3) BNSS ఫోరెన్సిక్ సందర్శన నిబంధన"
  },
  "io_action_checklist": [
    "దర్యాప్తు అధికారి (IO) ఈ కేసులో చేపట్టాల్సిన చట్టబద్ధమైన చర్య 1",
    "దర్యాప్తు అధికారి (IO) ఈ కేసులో చేపట్టాల్సిన చట్టబద్ధమైన చర్య 2"
  ]
}
"""

user_complaint = st.text_area(
    "ఫిర్యాదు వివరాలను టైప్ చేయండి (Complaint Text):",
    placeholder="ఉదాహరణ: ఫిర్యాదు సారాంశం నమోదు చేయండి...",
    height=150
)

uploaded_files = st.file_uploader(
    "సంబంధిత డాక్యుమెంట్లు లేదా ఫిర్యాదు ఇమేజ్‌లను అప్‌లోడ్ చేయండి:",
    type=["pdf", "jpg", "jpeg", "png", "txt"],
    accept_multiple_files=True
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    analyze_button = st.button("విశ్లేషించు (Analyze)", type="primary", use_container_width=True)

if analyze_button:
    if not api_key:
        st.error("❌ OpenAI API కీ కనుగొనబడలేదు. దయచేసి Streamlit secrets లో `OPENAI_API_KEY` ని కాన్ఫిగర్ చేయండి లేదా సైడ్‌బార్‌లో నమోదు చేయండి.")
    elif not user_complaint.strip() and not uploaded_files:
        st.warning("దయచేసి ఫిర్యాదు పాఠ్యాన్ని నమోదు చేయండి లేదా ఏదైనా పత్రం/ఇమేజ్ అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner("పత్రంలోని పాఠ్యాన్ని OCR ద్వారా సేకరించి OpenAI GPT ద్వారా విశ్లేషిస్తోంది..."):
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

                # Official OpenAI Client (uses api.openai.com)
                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this complaint and documents thoroughly. Identify ALL applicable criminal sections and return strictly valid JSON:\n\n{combined_content}"}
                    ],
                    temperature=0.1
                )

                raw_output = response.choices[0].message.content.strip()
                report_data = repair_and_parse_json(raw_output)

                st.success("విశ్లేషణ విజయవంతంగా పూర్తయింది!")
                st.markdown(f"### 📂 నేరం వర్గం: `{report_data.get('complaint_category', 'ఆర్థిక నేరం')}`")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📌 ముఖ్య వాస్తవాలు & ఆర్థిక లెక్కలు",
                    "⚖️ వర్తించే చట్టబద్ధమైన సెక్షన్లు",
                    "🏛️ BNSS ప్రక్రియలు (Procedures)",
                    "🔍 BSA ఆధారాలు & ఫోరెన్సిక్స్",
                    "📋 IO యాక్షన్ చెక్‌లిస్ట్"
                ])

                with tab1:
                    st.subheader("ఫిర్యాదు నుండి సేకరించిన ముఖ్య వాస్తవాలు")
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
                    st.subheader("చట్టపరంగా వర్తించే ఖచ్చితమైన సెక్షన్లు & శిక్షల వివరాలు")
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
                    st.markdown(f"**1. FIR నమోదు / ప్రాథమిక విచారణ (Section 173 BNSS):**\n\n{bnss.get('fir_or_pe_rule')}")
                    st.markdown("---")
                    st.markdown(f"**2. హాజరు నోటీసు / అరెస్ట్ (Section 35 BNSS):**\n\n{bnss.get('notice_or_arrest')}")
                    st.markdown("---")
                    st.markdown(f"**3. డిఫాల్ట్ బెయిల్ / కస్టడీ గడువు (Section 187 BNSS):**\n\n{bnss.get('detention_default_bail_timeline')}")
                    st.markdown("---")
                    st.markdown(f"**4. బాధితునికి పురోగతి నివేదిక (Section 193 BNSS):**\n\n{bnss.get('victim_update_rule')}")

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
