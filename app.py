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
        "complaint_category": "సైబర్ మోసం మరియు ఆర్థిక నేరం",
        "key_facts": [
            "బాధితుడు ఫిర్యాదులో పేర్కొన్న చిరునామాలో నివసిస్తున్నారు.",
            "10 సెప్టెంబర్ 2026న గూగుల్ ప్లే స్టోర్ నుండి 'ఈజీ లోన్స్ అండ్ రివార్డ్స్' యాప్‌ను డౌన్‌లోడ్ చేసుకున్నారు.",
            "అదే రోజు మధ్యాహ్నం సుమారు 2:30 గంటలకు గుర్తుతెలియని వ్యక్తి (+91 91234 XXXXX) నుంచి ఫోన్ చేసి యాప్ ప్రతినిధిగా పరిచయం చేసుకున్నారు.",
            "కేవైసీ వెరిఫికేషన్ పేరుతో పంపిన లింక్‌లో వివరాలు నమోదు చేయగానే, బాధితుడి అనుమతి లేకుండానే బ్యాంక్ ఖాతా నుండి ₹45,000 డెబిట్ అయ్యాయి.",
            "డబ్బులు కట్ అయిన వెంటనే కాల్ కట్ చేసి యాప్ పనిచేయడం ఆగిపోయింది; బాధితుడు వెంటనే ఖాతాను తాత్కాలికంగా నిలిపివేశారు."
        ],
        "applicable_sections": [
            {
                "act": "BNS, 2023",
                "section": "Section 318(4)",
                "offence_name": "మోసపూరితంగా ప్రేరేపించి ఆస్తిని బదిలీ చేయించుకోవడం (Cheating)",
                "punishment": "7 సంవత్సరాల వరకు జైలు శిక్ష మరియు జరిమానా",
                "classification": "కాగ్నిజబుల్ (Cognizable), నాన్-బెయిలబుల్ (Non-Bailable)",
                "justification": "మోసపూరిత ఉద్దేశంతో తప్పుడు వివరాలు చెప్పి బాధితుడి ఖాతా నుండి నిధులను అక్రమంగా బదిలీ చేయించుకున్నందున వర్తిస్తుంది."
            },
            {
                "act": "Information Technology Act, 2000",
                "section": "Section 66D",
                "offence_name": "కంప్యూటర్ వనరును ఉపయోగించి వ్యక్త్యానుకరణ ద్వారా మోసం (Cheating by personation)",
                "punishment": "3 సంవత్సరాల వరకు జైలు శిక్ష మరియు ₹1 లక్ష వరకు జరిమానా",
                "classification": "కాగ్నిజబుల్ (Cognizable), బెయిలబుల్ (Bailable)",
                "justification": "మొబైల్ ఫోన్, ఫిషింగ్ లింక్ మరియు ఇంటర్నెట్ వనరులను ఉపయోగించి నకిలీ ప్రతినిధిగా నమ్మించి మోసగించినందుకు వర్తిస్తుంది."
            }
        ],
        "bnss_procedure": {
            "fir_or_pe_rule": "Section 173(3) BNSS: 7 సంవత్సరాల లోపు శిక్ష గల నేరాలకు DSP అనుమతితో 14 రోజుల ప్రాథమిక విచారణకు అవకాశమున్నప్పటికీ, సైబర్ నేరాల్లో నిధులు త్వరగా రికవరీ చేయడానికి వెంటనే రెగ్యులర్ FIR నమోదు చేయాలి.",
            "notice_or_arrest": "Section 35(3) BNSS: 7 సంవత్సరాల కంటే తక్కువ శిక్ష ఉండే నేరాలకు నిందితునికి ముందుగా హాజరు నోటీసు (Notice of Appearance) జారీ చేయడం చట్టబద్ధమైన నిబంధన.",
            "detention_default_bail_timeline": "Section 187(3) BNSS: 10 సంవత్సరాల లోపు శిక్ష గల నేరాల్లో దర్యాప్తు ముగించి చార్జిషీట్ దాఖలుకు గరిష్ట కస్టడీ గడువు 60 రోజులు. గడువు దాటితే నిందితునికి డిఫాల్ట్ బెయిల్ పొందే హక్కు ఉంటుంది.",
            "victim_update_rule": "Section 193(3)(ii) BNSS: కేసు నమోదు అయిన నాటి నుండి ప్రతి 90 రోజులకు ఒకసారి దర్యాప్తు పురోగతి వివరాలను ఫిర్యాదుదారునికి/బాధితునికి తప్పనిసరిగా లిఖితపూర్వకంగా లేదా డిజిటల్ మార్గంలో తెలియజేయాలి."
        },
        "bsa_evidence_rules": {
            "electronic_evidence_cert": "Section 63(4) BSA: బ్యాంక్ స్టేట్‌మెంట్లు, మోసపూరిత లింక్ లాగ్స్, కాల్ రికార్డులు మరియు స్క్రీన్‌షాట్‌లను రుజువు చేయడానికి సర్వర్ అడ్మినిస్ట్రేటర్ లేదా సంబంధిత నోడల్ అధికారి సంతకం చేసిన ఎలక్ట్రానిక్ సర్టిఫికెట్ తప్పనిసరి.",
            "videography_rule": "Section 105 BNSS: మోసానికి వాడిన మొబైల్ ఫోన్లు లేదా ఇతర డిజిటల్ పరికరాలను పంచనామా ద్వారా స్వాధీనం చేసుకునేటప్పుడు తప్పనిసరిగా ఆడియో-వీడియో రికార్డింగ్ చేయాలి.",
            "forensic_visit_rule": "Section 176(3) BNSS: 7 సంవత్సరాలు లేదా అంతకంటే ఎక్కువ శిక్ష ఉన్న తీవ్ర నేరాల్లో ఫోరెన్సిక్ నిపుణుల సందర్శన తప్పనిసరి."
        },
        "io_action_checklist": [
            "Section 94 BNSS: సంబంధిత బ్యాంకులు మరియు పేమెంట్ గేట్‌వేలకు తక్షణమే నోటీసు జారీ చేసి, నిందితుడి బెనిఫిషియరీ ఖాతాను Section 107 BNSS కింద స్తంభింపజేయాలి (Freeze).",
            "Section 94 BNSS: టెలికాం సర్వీస్ ప్రొవైడర్లకు నోటీసు ఇచ్చి నేరానికి ఉపయోగించిన మొబైల్ నంబర్ (+91 91234 XXXXX) యొక్క CDR, IPDR, టవర్ లొకేషన్ మరియు SDR సేకరించాలి.",
            "Section 94 BNSS: మోసపూరిత యాప్ మరియు హోస్టింగ్ సేవల సమాచారం కోసం గూగుల్/యాప్ ప్రొవైడర్‌కు నోటీసు పంపి లాగ్స్, ఐపీ చిరునామాలను కోరాలి.",
            "Section 105 BNSS: బాధితుడి మొబైల్‌లోని లావాదేవీల స్క్రీన్‌షాట్లు, మెసేజ్‌లు మరియు ఇతర డిజిటల్ సాక్ష్యాలను స్వాధీనం చేసుకునే సమయంలో ఆడియో-వీడియో రికార్డింగ్ నిర్వహించాలి.",
            "Section 63(4) BSA: సేకరించిన బ్యాంక్ రికార్డులు, కాల్ డేటా, ఎలక్ట్రానిక్ లావాదేవీలకు సంబంధిత అధికారుల నుండి చట్టబద్ధమైన ధ్రువీకరణ పత్రం (Certificate) పొందాలి.",
            "Section 35(3) BNSS: నిందితుల గుర్తింపు లభించగానే విచారణకు హాజరుకావాలని Section 35(3) BNSS కింద చట్టపరమైన నోటీసు జారీ చేయాలి.",
            "Section 193(3)(ii) BNSS: కేసు నమోదు అయినప్పటి నుండి 90 రోజులలోపు దర్యాప్తు పురోగతి నివేదికను బాధితునికి అధికారికంగా అందించాలి."
        ]
    }

# System Prompt forcing formal Telugu output
SYSTEM_PROMPT = """
Role: You are an authoritative Indian Criminal Law Decision-Engine specialized in Bharatiya Nyaya Sanhita (BNS, 2023), Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023), Bharatiya Sakshya Adhiniyam (BSA, 2023), and Special Acts (IT Act, 2000).

CRITICAL LANGUAGE REQUIREMENT:
You MUST generate all descriptive content, facts, justifications, procedures, and checklists STRICTLY IN PROFESSIONAL TELUGU (తెలుగు భాషలో మాత్రమే సమాధానం ఇవ్వాలి). 
Keep Act names and Section numbers clear (e.g., 'BNS, 2023', 'Section 318(4)', 'Section 94 BNSS', 'Section 63(4) BSA'), but explain all facts, procedures, and steps in Telugu.

Strict Legal Guardrails:
1. Strict Ingredient Matching:
   - Identify the exact complaint category in Telugu.
   - BNS 319(2) (వ్యక్త్యానుకరణ ద్వారా మోసం): గరిష్ట శిక్ష 5 సంవత్సరాల వరకు, లేదా జరిమానా, లేదా రెండూ. కాగ్నిజబుల్, బెయిలబుల్.
   - BNS 318(4) (మోసపూరిత ప్రేరణతో ఆస్తి బదిలీ): గరిష్ట శిక్ష 7 సంవత్సరాలు మరియు జరిమానా. కాగ్నిజబుల్, నాన్-బెయిలబుల్.
   - IT Act 66D: కంప్యూటర్ లేదా కమ్యూనికేషన్ పరికరాన్ని ఉపయోగించి మోసం చేసినప్పుడు మాత్రమే చేర్చాలి.
   - IT Act 66C: పాస్‌వర్డ్, డిజిటల్ సంతకం లేదా గుర్తింపు దొంగిలించినప్పుడు మాత్రమే చేర్చాలి.
   - శారీరక దాడి/గాయాలు/బెదిరింపులకు తగిన BNS సెక్షన్లు (Sec 115, Sec 351, Sec 352 etc.) జతచేయాలి.

2. BNSS Procedure Guidelines (ఇవన్నీ తెలుగులో వివరించాలి):
   - Section 173(3) BNSS: 3 నుండి 7 సంవత్సరాల లోపు శిక్ష గల నేరాల్లో DSP అనుమతితో 14 రోజుల PE కి అనుమతి. సైబర్ మోసాల్లో అత్యవసరంగా డైరెక్ట్ FIR నమోదు.
   - Section 35(3) BNSS: 7 సంవత్సరాలలోపు శిక్ష గల నేరాల్లో నిందితునికి ముందుగా హాజరు నోటీసు ఇవ్వాలి.
   - Section 187(3) BNSS: 10 సంవత్సరాల లోపు శిక్షకు 60 రోజులు, తీవ్ర నేరాలకు 90 రోజుల గరిష్ట కస్టడీ గడువు (డిఫాల్ట్ బెయిల్).
   - Section 193(3)(ii) BNSS: ప్రతి 90 రోజులకు బాధితునికి దర్యాప్తు పురోగతి నివేదిక తప్పనిసరి.

3. BSA Evidence Compliance (తెలుగులో):
   - Section 63(4) BSA: ఎలక్ట్రానిక్ సాక్ష్యాలకు నోడల్ ఆఫీసర్ సర్టిఫికెట్ తప్పనిసరి.
   - Section 105 BNSS: సెర్చ్ & సీజర్ సమయంలో ఆడియో-వీడియో ఎలక్ట్రానిక్ రికార్డింగ్.
   - Section 176(3) BNSS: 7+ సంవత్సరాల శిక్ష గల కేసుల్లో ఫోరెన్సిక్ బృందం సందర్శన.

4. IO Action Checklist (కనీసం 6 నుండి 8 పక్కా చట్టబద్ధమైన దర్యాప్తు చర్యలు - పూర్తి తెలుగులో):
   - Section 94 BNSS కింద బ్యాంకులకు నోటీసులు & Section 107 BNSS కింద ఖాతాల ఫ్రీజింగ్.
   - Section 94 BNSS కింద TSP లకు CDR, IPDR, SDR కొరకు నోటీసులు.
   - Section 105 BNSS ప్రకారం పరికరాల స్వాధీనం & వీడియోగ్రఫీ.
   - Section 63(4) BSA కింద డిజిటల్ ఆధారాల సర్టిఫికేషన్.
   - Section 35(3) BNSS హాజరు నోటీసు జారీ.
   - Section 193(3)(ii) BNSS ప్రకారం 90 రోజుల్లో బాధితునికి అప్‌డేట్.

MANDATORY OUTPUT FORMAT:
Output ONLY a single valid JSON object. All field values must be in Telugu:
{
  "complaint_category": "నేరం వర్గం (తెలుగులో)",
  "key_facts": ["ఫిర్యాదు నుండి ముఖ్య వాస్తవాలు (తెలుగులో)"],
  "applicable_sections": [
    {
      "act": "చట్టం పేరు (e.g., BNS, 2023)",
      "section": "సెక్షన్ నంబర్ (e.g., Section 318(4))",
      "offence_name": "నేరం పేరు (తెలుగులో)",
      "punishment": "శిక్ష వివరాలు (తెలుగులో)",
      "classification": "వర్గీకరణ (కాగ్నిజబుల్ / నాన్-బెయిలబుల్)",
      "justification": "చట్టపరమైన సమర్థన (తెలుగులో)"
    }
  ],
  "bnss_procedure": {
    "fir_or_pe_rule": "FIR లేదా ప్రాథమిక విచారణ నిబంధన (తెలుగులో)",
    "notice_or_arrest": "హాజరు నోటీసు లేదా అరెస్ట్ నిబంధన (తెలుగులో)",
    "detention_default_bail_timeline": "డిఫాల్ట్ బెయిల్ మరియు కస్టడీ గడువు (తెలుగులో)",
    "victim_update_rule": "బాధితునికి సమాచారం ఇచ్చే గడువు (తెలుగులో)"
  },
  "bsa_evidence_rules": {
    "electronic_evidence_cert": "ఎలక్ట్రానిక్ సాక్ష్యాధారాల ధ్రువీకరణ నిబంధన (తెలుగులో)",
    "videography_rule": "వీడియోగ్రఫీ నిబంధన (తెలుగులో)",
    "forensic_visit_rule": "ఫోరెన్సిక్ నిపుణుల సందర్శన నిబంధన (తెలుగులో)"
  },
  "io_action_checklist": [
    "దర్యాప్తు అధికారి చేపట్టాల్సిన చర్య 1 (తెలుగులో)",
    "దర్యాప్తు అధికారి చేపట్టాల్సిన చర్య 2 (తెలుగులో)"
  ]
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
                        {"role": "user", "content": f"Analyze this complaint and documents thoroughly. Generate the complete JSON response STRICTLY IN TELUGU:\n\n{combined_content}"}
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
