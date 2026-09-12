import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్")
st.write("కేసు వివరాలు నమోదు చేయండి లేదా PDF / Text ఫిర్యాదు కాపీని అప్‌లోడ్ చేయండి.")

# Streamlit Secrets నుండి API Key పొందడం
if "GROQ_API_KEY" not in st.secrets:
    st.error("Streamlit Secrets లో 'GROQ_API_KEY' కనిపించలేదు. దయచేసి App Settings -> Secrets లో నమోదు చేయండి.")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]

# టెక్స్ట్ లేదా PDF అప్‌లోడ్ ట్యాబ్‌లు
tab1, tab2 = st.tabs(["📝 టెక్స్ట్ వివరాలు", "📁 PDF / Text ఫైల్ అప్‌లోడ్"])

case_text = ""

with tab1:
    text_input = st.text_area(
        "ఫిర్యాదు వివరాలు ఇక్కడ నమోదు చేయండి:",
        height=160,
        placeholder="ఉదాహరణ: ఇంట్లోకి అక్రమంగా ప్రవేశించి నల్లపూసల గొలుసు, నగదు దొంగిలించారు..."
    )
    if text_input:
        case_text = text_input

with tab2:
    uploaded_file = st.file_uploader(
        "ఫిర్యాదు PDF లేదా TXT ఫైల్ ఎంచుకోండి",
        type=["pdf", "txt"]
    )
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                reader = PdfReader(uploaded_file)
                extracted_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
                case_text = extracted_text
                st.success(f"✅ PDF ఫైల్ విజయవంతంగా లోడ్ అయింది: {uploaded_file.name}")
            except Exception as pdf_err:
                st.error(f"PDF చదవడంలో లోపం: {pdf_err}")
        elif uploaded_file.type == "text/plain":
            case_text = uploaded_file.getvalue().decode("utf-8")
            st.success(f"✅ Text ఫైల్ లోడ్ అయింది: {uploaded_file.name}")

# సంక్షిప్తమైన మరియు కచ్చితమైన ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాల (BNS, BNSS, BSA) మరియు పాత చట్టాల (IPC, CrPC, IEA) నిపుణులైన లీగల్ అసిస్టెంట్. 
ప్రతి సెక్షన్‌కు కొత్త చట్టం మరియు పాత చట్టం రెండూ (ఉదా: BNS Section 303 / IPC Section 379) పక్కపక్కనే తెలుగులో రాయండి.

నివేదిక ఈ క్రమంలో ఉండాలి:
1. Sections & Punishments (కొత్త & పాత సెక్షన్లు, శిక్షలు)
2. నేర వర్గీకరణ (Cognizable/Bailable)
3. Procedures & Timelines (BNSS & CrPC దర్యాప్తు పద్ధతులు, కాలపరిమితులు)
4. Evidence Guidelines (BSA & IEA)
5. IO Action Checklist
"""

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి లేదా ఫైల్ అప్‌లోడ్ చేయండి.")
    else:
        trimmed_case_text = case_text[:2000]

        with st.spinner("చట్టాల ప్రకారం విశ్లేషిస్తోంది..."):
            try:
                client = Groq(api_key=api_key)

                # సర్వర్ నుండి అందుబాటులో ఉన్న మోడల్స్‌ను ఆటోమేటిక్‌గా ఫెచ్ చేయడం
                models_data = client.models.list().data
                all_ids = [m.id for m in models_data if "whisper" not in m.id and "guard" not in m.id]
                
                # అందుబాటులో ఉన్న మొదటి మోడల్‌ను ఆటోమేటిక్‌గా ఎంచుకుంటుంది (404 ఎర్రర్ రాదు)
                chosen_model = all_ids[0] if all_ids else "llama-3.1-8b-instant"

                response = client.chat.completions.create(
                    model=chosen_model,
                    temperature=0.0,
                    max_tokens=400,
                    messages=[
                        {"role": "system", "content": legal_system_instruction},
                        {"role": "user", "content": f"ఫిర్యాదు వివరాలు:\n{trimmed_case_text}"}
                    ]
                )

                result = response.choices[0].message.content

                if result:
                    st.markdown("### 📋 దర్యాప్తు నివేదిక (కొత్త & పాత చట్టాలు):")
                    st.markdown(result)

                    st.download_button(
                        label="📥 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="Legal_Report_BNS_IPC.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
