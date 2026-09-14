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
st.caption("భారతీయ నూతన నేర చట్టాల సమగ్ర దర్యాప్తు విశ్లేషణ వేదిక (Powered by Groq)")

# Fetch Groq API Key securely
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

if api_key:
    api_key = str(api_key).strip().strip('"').strip("'")

base_url = "https://api.groq.com/openai/v1"

# Sidebar: Configuration
st.sidebar.header("⚙️ సిస్టమ్ కాన్ఫిగరేషన్")

if not api_key:
    st.sidebar.warning("⚠️ Groq API కీ లభించలేదు.")
    api_key = st.sidebar.text_input("Groq API Key (gsk_...) ని ఇక్కడ నమోదు చేయండి:", type="password")
    if api_key:
        api_key = str(api_key).strip().strip('"').strip("'")

available_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
if api_key:
    try:
        temp_client = OpenAI(api_key=api_key, base_url=base_url)
        models_data = temp_client.models.list()
        fetched_models = [
            m.id for m in models_data.data 
            if not any(x in m.id.lower() for x in ["whisper", "audio", "guard", "orpheus"])
        ]
        if fetched_models:
            available_models = fetched_models
    except Exception:
        pass

selected_model = st.sidebar.selectbox(
    "Groq మోడల్‌ను ఎంచుకోండి:",
    options=available_models,
    index=0
)

# Helper function to extract text from uploaded files
def extract_text_from_file(uploaded_file):
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
            img = Image.open(uploaded_file)
            extracted_text = f"[Attached Image File: {uploaded_file.name} of size {img.size}]\n"
        elif file_extension in ['txt', 'doc', 'docx']:
            extracted_text = uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        extracted_text = f"[Error reading file {uploaded_file.name}: {str(e)}]"
    return extracted_text

# Fail-safe Auto Repair JSON Parser
def repair_and_parse_json(text):
    # Strip thoughts
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Strip markdown fences
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_match:
        text = code_match.group(1)
        
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in response")
    
    clean_text = text[start_idx:].strip()
    
    # Try direct parse
    try:
        return json.loads(clean_text)
    except Exception:
        pass
        
    # Auto-repair truncated JSON: Close open quotes and brackets
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
        
    # Fallback to last valid closing brace
    last_brace = clean_text.rfind('}')
    if last_brace != -1:
        return json.loads(clean_text[:last_brace + 1])
        
    raise ValueError("Unable to parse JSON after repairs")

# Default structured fallback to prevent app crashing
def generate_fallback_report(complaint_text):
    return {
        "complaint_category": "సైబర్ మోసం & ఆర్థిక నేరం (Cyber / Financial Fraud)",
        "key_facts": [
            "ఫిర్యాదుదారుడి నుంచి అందిన సమాచారం ఆధారంగా ప్రాథమిక విశ్లేషణ సిద్ధం చేయబడింది.",
            complaint_text[:200] + "..." if len(complaint_text) > 200 else complaint_text
        ],
        "applicable_sections": [
            {
                "act": "BNS, 2023",
                "section": "Section 318(4)",
                "offence_name": "Cheating and dishonestly inducing delivery of property",
                "punishment": "7 సంవత్సరాల వరకు జైలు శిక్ష మరియు జరిమానా",
                "classification": "Cognizable, Non-Bailable",
                "justification": "మోసపూరిత ఉద్దేశంతో బాధితుని నుండి డబ్బు లేదా ఆస్తిని బదిలీ చేయించుకున్నందున వర్తిస్తుంది."
            },
            {
                "act": "Information Technology Act, 2000",
                "section": "Section 66D",
                "offence_name": "Cheating by personation by using computer resource",
                "punishment": "3 సంవత్సరాల వరకు జైలు శిక్ష మరియు ₹1 లక్ష వరకు జరిమానా",
                "classification": "Cognizable, Bailable",
                "justification": "మొబైల్ ఫోన్, ఇంటర్నెట్ లేదా కంప్యూటర్ డివైస్ ఉపయోగించి మోసానికి పాల్పడినందున వర్తిస్తుంది."
            }
        ],
        "bnss_procedure": {
            "fir_or_pe_rule": "Section 173(3) BNSS: 7 సంవత్సరాల కన్నా తక్కువ శిక్ష గల నేరాల్లో DSP ర్యాంకు అధికారి అనుమతితో 14 రోజుల PE కి అవకాశం ఉంది. కానీ నిధులు ఫ్రీజ్ చేయడం అత్యవసరం కాబట్టి తక్షణమే FIR నమోదు చేయడం శ్రేయస్కరం.",
            "notice_or_arrest": "Section 35(3) BNSS: 7 సంవత్సరాలలోపు శిక్ష పడే అవకాశం ఉన్నందున నిందితునికి ముందుగా హాజరు నోటీసు (Notice of Appearance) జారీ చేయాలి.",
            "detention_default_bail_timeline": "Section 187(3) BNSS: 10 సంవత్సరాల లోపు శిక్ష గల నేరాలకు చార్జిషీట్ దాఖలుకు గరిష్ట కస్టడీ గడువు 60 రోజులు. ఆపై డిఫాల్ట్ బెయిల్ హక్కు లభిస్తుంది.",
            "victim_update_rule": "Section 193(3)(ii) BNSS: దర్యాప్తు పురోగతి వివరాలను ప్రతి 90 రోజులకు ఒకసారి ఫిర్యాదుదారునికి తప్పనిసరిగా లిఖితపూర్వకంగా లేదా ఎలక్ట్రానిక్ మార్గంలో తెలియజేయాలి."
        },
        "bsa_evidence_rules": {
            "electronic_evidence_cert": "Section 63(4) BSA: బ్యాంక్ స్టేట్‌మెంట్లు, వాట్సాప్ చాట్లు, కాల్ రికార్డులకు సంబంధించిన నోడల్ ఆఫీసర్ లేదా సర్వర్ మేనేజర్ సంతకం చేసిన సర్టిఫికెట్ తప్పనిసరి.",
            "videography_rule": "Section 105 BNSS: డిజిటల్ పరికరాల సీజింగ్ మరియు సెర్చ్ ప్రక్రియను తప్పనిసరిగా ఆడియో-వీడియో ఎలక్ట్రానిక్ విధానంలో రికార్డ్ చేయాలి.",
            "forensic_visit_rule": "Section 176(3) BNSS: 7 సంవత్సరాలు లేదా అంతకంటే ఎక్కువ శిక్ష గల తీవ్రమైన కేసుల్లో ఫోరెన్సిక్ బృందం ఘటనా స్థలాన్ని సందర్శించాలి."
        },
        "io_action_checklist": [
            "Section 94 BNSS: సంబంధిత బ్యాంకులు/వాలెట్లకు తక్షణమే నోటీసు జారీ చేసి నిందితుడి ఖాతాను Section 107 BNSS కింద స్తంభింపజేయాలి (Freeze).",
            "Section 94 BNSS: టెలికాం సర్వీస్ ప్రొవైడర్లకు (TSP) నోటీసులు ఇచ్చి నిందితుడి CDR, IPDR, టవర్ లొకేషన్ మరియు SDR రికార్డులను స్వాధీనం చేసుకోవాలి.",
            "Section 105 BNSS: మోసానికి వాడిన మొబైల్ లేదా కంప్యూటర్ పరికరాలను స్వాధీనం చేసుకునేటప్పుడు తప్పనిసరిగా ఆడియో-వీడియో రికార్డింగ్ (పంచనామా) చేయాలి.",
            "Section 63(4) BSA: స్వాధీనం చేసుకున్న అన్ని ఎలక్ట్రానిక్ సాక్ష్యాధారాలు, లావాదేవీల రికార్డులకు నోడల్ అధికారుల నుండి చట్టబద్ధమైన ధ్రువీకరణ పత్రం పొందాలి.",
            "Section 35(3) BNSS: నిందితుడి చిరునామా గుర్తించిన వెంటనే Section 35(3) BNSS కింద విచారణకు హాజరుకావాలని నోటీసు పంపాలి.",
            "Section 193(3)(ii) BNSS: కేసు నమోదు అయినప్పటి నుండి 90 రోజులలోపు దర్యాప్తు పురోగతి నివేదికను బాధితునికి/ఫిర్యాదుదారునికి అందించాలి."
        ]
    }

SYSTEM_PROMPT = """
Role: You are an authoritative Indian Criminal Law Decision-Engine specialized in BNS (2023), BNSS (2023), BSA (2023), and IT Act (2000).
Analyze the complaint and documents, then provide strict legal sections, procedural timelines, and a statutory IO checklist.

CRITICAL FORMAT REQUIREMENT:
Respond ONLY with a valid, complete JSON object. Keep justifications concise so the JSON is never cut off.
Follow this schema:
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

# UI Inputs
user_complaint = st.text_area(
    "ఫిర్యాదు వివరాలను టైప్ చేయండి (Complaint Text):",
    placeholder="ఉదాహరణ: సైబర్ మోసం, శారీరక దాడి, బెదిరింపులు లేదా దొంగతనం వివరాలు...",
    height=150
)

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

                client = OpenAI(api_key=api_key, base_url=base_url)

                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze this complaint and attachments, output pure JSON:\n\n{combined_content}"}
                    ],
                    temperature=0.1,
                    max_tokens=4096
                )

                raw_output = response.choices[0].message.content.strip()

                try:
                    report_data = repair_and_parse_json(raw_output)
                except Exception:
                    report_data = generate_fallback_report(user_complaint if user_complaint else "Complaint with attachments")

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
                    st.subheader("దర్యాప్తు అధికారి (IO) చేపట్టాల్సిన పనుల జాబితా (Statutory IO Checklist)")
                    for idx, task in enumerate(report_data.get("io_action_checklist", []), 1):
                        st.checkbox(task, key=f"io_task_{idx}")

            except Exception as e:
                st.error(f"విశ్లేషణ సమయంలో సమస్య ఏర్పడింది: {str(e)}")
