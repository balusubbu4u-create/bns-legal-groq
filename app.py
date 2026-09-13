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

# సైడ్‌బార్‌లో మోడల్ ఎంపిక - వేగవంతమైన, హై-లిమిట్ మోడల్ మొదటిదిగా
st.sidebar.header("⚙️ మోడల్ సెట్టింగ్స్")
available_models = [
    "llama-3.1-8b-instant",       # అత్యంత వేగవంతమైనది, ఎక్కువ రేట్ లిమిట్ (429 రాదు)
    "llama-3.3-70b-versatile",    # లోతైన విశ్లేషణ (పరిమితి త్వరగా అయిపోవచ్చు)
    "gemma2-9b-it"
]

selected_model = st.sidebar.selectbox(
    "🤖 Groq AI Model వెర్షన్ ఎంచుకోండి:",
    options=available_models,
    index=0,
    help="llama-3.1-8b-instant ఎంచుకుంటే 429 Rate Limit ఎర్రర్ రాకుండా వేగంగా పనిచేస్తుంది."
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
1. ప్రతి లీగల్ సెక్షన్‌కు కొత్త చట్టం (BNS/BNSS/BSA) మరియు పాత చట్టం (IPC/CrPC/IEA) పక్కపక్కనే స్పష్టంగా రాయాలి (ఉదా: BNS Section 303 / IPC Section 379).
2. దర్యాప్తు విధానం (Investigation Procedure) లో పోలీసు అధికారి (IO) మొదటి నుండి చివరి వరకు పాటించాల్సిన స్టాండర్డ్ ఆపరేటింగ్ ప్రొసీజర్ (SOP) ను దశలవారీగా పేర్కొనాలి.
3. మొత్తం నివేదిక స్పష్టమైన తెలుగులో, పాయింట్ల రూపంలో ఉండాలి.

క్రింది క్రమంలో మాత్రమే సమగ్ర నివేదిక రూపొందించాలి:

### 1. వర్తించే సెక్షన్లు & శిక్షల వివరాలు (BNS vs IPC)
- ప్రతి నేరానికి BNS Section మరియు పాత IPC Section.
- గరిష్ట శిక్ష మరియు జరిమానా.
- నేరాల స్వభావం (Cognizable / Non-Cognizable, Bailable / Non-Bailable).

### 2. దర్యాప్తు విధానం & చట్టపరమైన ప్రక్రియ (BNSS vs CrPC SOP)
- ఎఫ్‌ఐఆర్ నమోదు & ప్రిలిమినరీ ఎంక్వైరీ (BNSS 173 / CrPC 154).
- నోటీసులు & హాజరు (BNSS 35(3) / CrPC 41A).
- అరెస్ట్, రిమాండ్ & కస్టడీ నిబంధనలు (BNSS 187).
- శోధన & స్వాధీనం (Search & Seizure) - BNSS 105 ప్రకారం తప్పనిసరి వీడియో రికార్డింగ్, పంచనామా.
- కాలపరిమితులు (Timelines): దర్యాప్తు మరియు చార్జ్‌షీట్ దాఖలు గడువులు.

### 3. సాక్ష్యాధారాల సేకరణ & ఫోరెన్సిక్ మార్గదర్శకాలు (BSA vs IEA)
- సంఘటనా స్థలం పరిశీలన, వీడియోగ్రఫీ.
- డిజిటల్ సాక్ష్యాలు: BSA Section 63 సర్టిఫికేషన్ (పాత 65B స్థానంలో).
- తీవ్ర నేరాలకు ఫోరెన్సిక్ విజిట్ (BNSS 176(3)).

### 4. దర్యాప్తు అధికారి (IO) సమగ్ర యాక్షన్ చెక్‌లిస్ట్
- [ ] వెంటనే చేయాల్సిన అత్యవసర చర్యలు.
- [ ] సేకరించాల్సిన డాక్యుమెంట్లు, సాక్షుల వాంగ్మూలాలు (BNSS 180 / CrPC 161).
- [ ] సాంకేతిక ఆధారాల సేకరణ (CDR, CCTV).

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("🔍 కేస్ విశ్లేషించి దర్యాప్తు నివేదిక రూపొందించండి", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి లేదా ఫైల్ అప్‌లోడ్ చేయండి.")
    else:
        trimmed_case_text = case_text[:3000]

        with st.spinner("దర్యాప్తు నివేదిక సిద్ధమవుతోంది..."):
            try:
                client = Groq(api_key=api_key)

                # ఒకవేళ ఎంచుకున్న మోడల్‌కి 429 వస్తే ఆటోమేటిక్‌గా 8b మోడల్‌కి మారే లాజిక్
                try:
                    response = client.chat.completions.create(
                        model=selected_model,
                        temperature=0.1,
                        messages=[
                            {"role": "system", "content": legal_system_instruction},
                            {"role": "user", "content": f"కేసు వివరాలు:\n{trimmed_case_text}"}
                        ]
                    )
                except Exception as model_err:
                    if "429" in str(model_err) and selected_model != "llama-3.1-8b-instant":
                        st.info("⚠️ 70B మోడల్‌కు రేట్ లిమిట్ చేరింది. ఆటోమేటిక్‌గా వేగవంతమైన 8B మోడల్‌తో విశ్లేషిస్తోంది...")
                        response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            temperature=0.1,
                            messages=[
                                {"role": "system", "content": legal_system_instruction},
                                {"role": "user", "content": f"కేసు వివరాలు:\n{trimmed_case_text}"}
                            ]
                        )
                    else:
                        raise model_err

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
