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

# కొత్త చట్టాల (BNS, BNSS, BSA) కోసం కఠినమైన ప్రాంప్ట్
legal_system_instruction = """
మీరు పూర్తిగా కొత్త భారతీయ క్రిమినల్ చట్టాలైన భారతీయ న్యాయ సంహిత (Bharatiya Nyaya Sanhita - BNS), భారతీయ నాగరిక సురక్ష సంహిత (Bharatiya Nagarik Suraksha Sanhita - BNSS), మరియు భారతీయ సాక్ష్య అధినియమం (Bharatiya Sakshya Adhiniyam - BSA) పై మాత్రమే ఆధారపడే అధికారిక లీగల్ అసిస్టెంట్.

⚠️ అత్యంత ముఖ్యమైన నిబంధనలు:
1. పాత IPC (Indian Penal Code), CrPC, లేదా Indian Evidence Act లకు సంబంధించిన పాత సెక్షన్లను ఎట్టి పరిస్థితుల్లోనూ వాడవద్దు, ప్రస్తావించవద్దు.
2. కేవలం కొత్త BNS సెక్షన్లు (ఉదా: దొంగతనానికి BNS Section 303 లేదా 305, అతిక్రమణకు BNS Section 329/331 వంటివి), BNSS ప్రొసీజర్లు మరియు BSA నిబంధనలను మాత్రమే ఖచ్చితంగా పేర్కొనాలి.
3. విశ్లేషణ పూర్తిగా స్పష్టమైన తెలుగులో ఉండాలి. ముఖ్యమైన సెక్షన్ పేర్లు, వర్గీకరణలను బ్రాకెట్లలో ఇంగ్లీష్‌లో పేర్కొనండి.

క్రింది క్రమం (Headings) లో మాత్రమే నివేదిక రూపొందించాలి:
1. వర్తించే BNS Sections & Punishments (కేవలం కొత్త BNS సెక్షన్లు, శిక్షల వివరాలు)
2. నేరం యొక్క వర్గీకరణ (Cognizable/Non-Cognizable, Bailable/Non-Bailable, Compoundable/Non-Compoundable)
3. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్ నిబంధనలు, రిమాండ్, దర్యాప్తు సమయ పరిమితులు)
4. BSA Evidence & Forensic Guidelines (సాక్ష్యాధారాల సేకరణ, డిజిటల్/ఎలక్ట్రానిక్ సాక్ష్యాల సర్టిఫికేషన్, ఫోరెన్సిక్ మార్గదర్శకాలు)
5. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి లేదా ఫైల్ అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner("కొత్త చట్టాలు (BNS, BNSS, BSA) ప్రకారం విశ్లేషిస్తోంది..."):
            try:
                client = Groq(api_key=api_key)

                # మీ అకౌంట్‌లో యాక్టివ్‌గా ఉన్న మోడల్‌ను ఆటోమేటిక్‌గా ఎంచుకోవడం
                models_data = client.models.list().data
                valid_models = [
                    m.id for m in models_data 
                    if "whisper" not in m.id and "guard" not in m.id
                ]
                chosen_model = valid_models[0] if valid_models else "llama-3.1-8b-instant"

                response = client.chat.completions.create(
                    model=chosen_model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": legal_system_instruction},
                        {"role": "user", "content": f"ఫిర్యాదు వివరాలు:\n{case_text}"}
                    ]
                )

                result = response.choices[0].message.content

                if result:
                    st.markdown("### 📋 దర్యాప్తు నివేదిక:")
                    st.markdown(result)

                    st.download_button(
                        label="📥 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="BNS_Legal_Report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
