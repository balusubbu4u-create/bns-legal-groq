import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్")
st.write("కేసు వివరాలు నమోదు చేయండి లేదా PDF ఫిర్యాదు కాపీని అప్‌లోడ్ చేయండి.")

# Streamlit Secrets నుండి నేరుగా కీ తీసుకోవడం
if "GROQ_API_KEY" not in st.secrets:
    st.error("Streamlit Secrets లో GROQ_API_KEY కనిపించలేదు. దయచేసి App Settings -> Secrets లో కీ ని సేవ్ చేయండి.")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]

tab1, tab2 = st.tabs(["📝 టెక్స్ట్ వివరాలు", "📁 PDF / Text ఫైల్ అప్‌లోడ్"])

case_text = ""

with tab1:
    text_input = st.text_area(
        "ఫిర్యాదు వివరాలు ఇక్కడ నమోదు చేయండి:",
        height=160,
        placeholder="ఉదాహరణ: ఇంట్లోకి అక్రమంగా ప్రవేశించి దొంగతనానికి పాల్పడ్డారు..."
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
                st.success(f"✅ PDF ఫైల్ లోడ్ అయింది: {uploaded_file.name}")
            except Exception as pdf_err:
                st.error(f"PDF చదవడంలో లోపం: {pdf_err}")
        elif uploaded_file.type == "text/plain":
            case_text = uploaded_file.getvalue().decode("utf-8")
            st.success(f"✅ Text ఫైల్ లోడ్ అయింది: {uploaded_file.name}")

# లీగల్ నిబంధనల ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) పై ప్రావీణ్యం ఉన్న అధికారిక లీగల్ అసిస్టెంట్.

క్రింది నిర్మాణం (Headings) లో మాత్రమే తెలుగులో నివేదిక అందించాలి:
1. వర్తించే BNS Sections & Punishments (పాత IPC పోలికలతో)
2. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్, రిమాండ్ నిబంధనలు)
3. BSA Evidence & Forensic Guidelines (సాక్ష్యాధారాలు, ఫోరెన్సిక్ నిబంధనలు)
4. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి లేదా PDF ఫైల్ అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner("చట్టాలను పరిశీలిస్తోంది..."):
            try:
                client = Groq(api_key=api_key)

                # మీ అకౌంట్‌లో యాక్టివ్‌గా ఉన్న మోడల్‌ను ఆటోమేటిక్‌గా ఎంచుకోవడం
                models_data = client.models.list().data
                valid_models = [m.id for m in models_data if "whisper" not in m.id and "guard" not in m.id]
                chosen_model = valid_models[0] if valid_models else "llama-3.1-8b-instant"

                response = client.chat.completions.create(
                    model=chosen_model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": legal_system_instruction},
                        {"role": "user", "content": f"కేసు వివరాలు:\n{case_text}"}
                    ]
                )

                result = response.choices[0].message.content

                if result:
                    st.markdown("### 📋 దర్యాప్తు నివేదిక:")
                    st.markdown(result)
                    
                    st.download_button(
                        label="📄 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="BNS_Legal_Report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
