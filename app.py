import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ & దర్యాప్తు అసిస్టెంట్")
st.caption("భారతీయ క్రిమినల్ చట్టాలు (BNS, BNSS, BSA) & పాత చట్టాల (IPC, CrPC, IEA) సమగ్ర విశ్లేషణ")

# Streamlit Secrets నుండి API Key పొందడం
if "GROQ_API_KEY" not in st.secrets:
    st.error("Streamlit Secrets లో 'GROQ_API_KEY' కనిపించలేదు. దయచేసి App Settings -> Secrets లో నమోదు చేయండి.")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]

# సైడ్‌బార్‌లో లైవ్ మోడల్ వెర్షన్లను పొందడం
st.sidebar.header("⚙️ మోడల్ సెట్టింగ్స్")

@st.cache_data(ttl=3600)
def get_available_groq_models(key):
    try:
        client = Groq(api_key=key)
        models_data = client.models.list().data
        # ఆడియో, గార్డ్ మోడల్స్ కాకుండా టెక్స్ట్ మోడల్స్ మాత్రమే
        chat_models = [
            m.id for m in models_data 
            if "whisper" not in m.id and "guard" not in m.id
        ]
        # Llama మోడల్స్‌ను ముందు వరుసలో ఉంచడం
        chat_models.sort(key=lambda x: ("llama" in x.lower() or "gemma" in x.lower()), reverse=True)
        return chat_models
    except Exception:
        return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

available_models = get_available_groq_models(api_key)

selected_model = st.sidebar.selectbox(
    "🤖 Groq AI Model వెర్షన్ ఎంచుకోండి:",
    options=available_models,
    index=0,
    help="మీ Groq ఖాతాలో లైవ్‌గా పనిచేసే మోడల్స్ ఇక్కడ కనిపిస్తాయి."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**కవర్ చేయబడే అంశాలు:**
- 🔹 BNS vs IPC సెక్షన్లు
- 🔹 BNSS vs CrPC దర్యాప్తు విధానం
- 🔹 BSA vs IEA ఎలక్ట్రానిక్/ఫోరెన్సిక్ సాక్ష్యాలు
- 🔹 IO సమగ్ర యాక్షన్ చెక్‌లిస్ట్
""")

tab1, tab2 = st.tabs(["📝 టెక్స్ట్ వివరాలు", "📁 PDF / Text ఫైల్ అప్‌లోడ్"])

case_text = ""

with tab1:
    text_input = st.text_area(
        "ఫిర్యాదు వివరాలు ఇక్కడ నమోదు చేయండి:",
        height=180,
        placeholder="ఉదాహరణ: అర్ధరాత్రి ఇంట్లోకి అక్రమంగా ప్రవేశించి బంగారు నగలు, నగదు దోచుకెళ్లారు. బాధితులపై దాడి చేసి బెదిరించారు..."
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

# దర్యాప్తు విధానం మరియు సెక్షన్ల సమగ్ర విశ్లేషణ ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) మరియు వాటి పాత చట్టాలైన IPC, CrPC, Indian Evidence Act (IEA) లపై అత్యున్నత ప్రావీణ్యం ఉన్న అధికారిక లీగల్ & ఇన్వెస్టిగేషన్ స్పెషలిస్ట్.

ఖచ్చితమైన నియమాలు:
1. ప్రతి లీగల్ సెక్షన్‌కు కొత్త చట్టం (BNS/BNSS/BSA) మరియు పాత చట్టం (IPC/CrPC/IEA) పక్కపక్కనే స్పష్టంగా రాయాలి. (ఉదా: BNS Section 303 / IPC Section 379).
2. 'దర్యాప్తు విధానం' (Investigation Procedure) లో కేవలం పైపైన కాకుండా, పోలీసు అధికారి (IO) మొదటి నుండి చివరి వరకు పాటించాల్సిన స్టాండర్డ్ ఆపరేటింగ్ ప్రొసీజర్ (SOP) ను దశలవారీగా పేర్కొనాలి.
3. మొత్తం నివేదిక స్పష్టమైన తెలుగులో, పాయింట్ల రూపంలో ఉండాలి.

క్రింది క్రమంలో మాత్రమే సమగ్ర నివేదిక రూపొందించాలి:

### 1. వర్తించే సెక్షన్లు & శిక్షల వివరాలు (BNS vs IPC)
- ఫిర్యాదులోని అంశాలకు వర్తించే ప్రతి నేరానికి BNS Section మరియు పాత IPC Section.
- ఆయా సెక్షన్లకు నిర్దేశించిన గరిష్ట శిక్ష మరియు జరిమానా.
- నేరాల స్వభావం (Cognizable / Non-Cognizable, Bailable / Non-Bailable).

### 2. దర్యాప్తు విధానం & చట్టపరమైన ప్రక్రియ (BNSS vs CrPC SOP)
- **ఎఫ్‌ఐఆర్ నమోదు & ప్రిలిమినరీ విచారణ:** BNSS 173 (పాత CrPC 154) నిబంధనలు.
- **నోటీసులు & హాజరు:** 7 సంవత్సరాల లోపు శిక్ష పడే కేసుల్లో BNSS 35(3) (పాత CrPC 41A) నోటీసు విధానం.
- **అరెస్ట్ & రిమాండ్ నిబంధనలు:** BNSS సెక్షన్లు, సమాచార హక్కులు, 24 గంటల మెజిస్ట్రేట్ హాజరు, పోలీస్/జ్యుడీషియల్ కస్టడీ గరిష్ట పరిమితులు (BNSS 187).
- **శోధన & స్వాధీనం (Search & Seizure):** BNSS 105 ప్రకారం ఆడియో-వీడియో రికార్డింగ్ నిబంధన, పంచనామా విధానం.
- **కాలపరిమితులు (Timelines):** దర్యాప్తు పూర్తి, మెడికల్ రిపోర్టులు, మరియు చార్జ్‌షీట్ దాఖలు గడువులు (60/90 రోజులు).

### 3. సాక్ష్యాధారాల సేకరణ & ఫోరెన్సిక్ మార్గదర్శకాలు (BSA vs IEA)
- సంఘటనా స్థలం పరిశీలన, క్రైమ్ సీన్ ఫోటోగ్రఫీ/వీడియోగ్రఫీ నిబంధనలు.
- డిజిటల్ & ఎలక్ట్రానిక్ సాక్ష్యాల గుర్తింపు: BSA Section 63 సర్టిఫికేషన్ (పాత 65B సర్టిఫికెట్ స్థానంలో).
- 7 ఏళ్లు పైబడిన శిక్ష పడే తీవ్ర నేరాలకు ఫోరెన్సిక్ నిపుణుల తప్పనిసరి విజిట్ (BNSS 176(3)).

### 4. దర్యాప్తు అధికారి (IO) సమగ్ర యాక్షన్ చెక్‌లిస్ట్
- [ ] వెంటనే చేయాల్సిన 5 అత్యవసర చర్యలు.
- [ ] సేకరించాల్సిన డాక్యుమెంట్లు, స్టేట్‌మెంట్లు (BNSS 180 / CrPC 161).
- [ ] సాంకేతిక ఆధారాల సేకరణ (CDR, CCTV, మొబైల్ డాటా).

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("🔍 కేస్ విశ్లేషించి దర్యాప్తు నివేదిక రూపొందించండి", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి లేదా ఫైల్ అప్‌లోడ్ చేయండి.")
    else:
        # కంటెక్స్ట్ విండో దాటకుండా ఉండటానికి మొదటి 2500 అక్షరాలు
        trimmed_case_text = case_text[:2500]

        with st.spinner(f"AI మోడల్ ({selected_model}) ద్వారా దర్యాప్తు విధానాలు మరియు సెక్షన్ల పరిశీలన జరుగుతోంది..."):
            try:
                client = Groq(api_key=api_key)

                response = client.chat.completions.create(
                    model=selected_model,
                    temperature=0.1,
                    messages=[
                        {"role": "system", "content": legal_system_instruction},
                        {"role": "user", "content": f"కేసు ఫిర్యాదు పూర్తి వివరాలు:\n{trimmed_case_text}"}
                    ]
                )

                result = response.choices[0].message.content

                if result:
                    st.markdown("---")
                    st.markdown("## 📋 సమగ్ర దర్యాప్తు & చట్టపరమైన విశ్లేషణ నివేదిక")
                    st.markdown(result)

                    st.download_button(
                        label="📥 నివేదికను ఫైల్‌గా డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="BNS_Investigation_Report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
