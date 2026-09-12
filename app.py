import time
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్")
st.write("కేసు వివరాలు రాయండి లేదా ఫిర్యాదు కాపీ ఫోటో/PDF అప్‌లోడ్ చేయండి.")

tab1, tab2 = st.tabs(["📝 టెక్స్ట్ వివరాలు", "📷 ఫోటో / PDF డాక్యుమెంట్"])

case_text = ""
uploaded_image = None
uploaded_pdf_bytes = None

with tab1:
    text_input = st.text_area(
        "ఫిర్యాదు వివరాలు ఇక్కడ రాయండి:",
        height=150,
        key="legal_text"
    )
    if text_input:
        case_text = text_input

with tab2:
    uploaded_file = st.file_uploader(
        "ఫిర్యాదు కాపీ లేదా FIR (JPG, JPEG, PNG, PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        key="legal_file"
    )
    if uploaded_file:
        file_type = uploaded_file.type
        # PDF ఫైల్ అయితే
        if file_type == "application/pdf":
            uploaded_pdf_bytes = uploaded_file.getvalue()
            st.success(f"✅ PDF డాక్యుమెంట్ లోడ్ అయింది: {uploaded_file.name}")
        # ఇమేజ్ ఫైల్ అయితే
        else:
            uploaded_image = Image.open(uploaded_file)
            st.image(
                uploaded_image,
                caption="అప్‌లోడ్ చేసిన చిత్రం",
                use_container_width=True
            )

# లీగల్ నిబంధనలు
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) పై ప్రావీణ్యం ఉన్న అధికారిక లీగల్ అసిస్టెంట్.

ముఖ్య నియమాలు & మార్గదర్శకాలు:
1. వాస్తవాల ఆధారితం: అందించిన ఫిర్యాదు/చిత్రం/PDF లోని వాస్తవాల ఆధారంగా మాత్రమే ఖచ్చితమైన సెక్షన్లు పేర్కొనాలి.
2. ఖచ్చితత్వం: చట్టపరమైన సెక్షన్లలో ఎలాంటి ఊహాజనిత (hallucinated) నంబర్లు చెప్పకూడదు.
3. లీగల్ టెర్మినాలజీ: విశ్లేషణ తెలుగులో ఉండాలి. ముఖ్యమైన సెక్షన్ పేర్లను బ్రాకెట్లలో ఇంగ్లీష్‌లో కూడా రాయాలి.
4. కాలపరిమితులు: BNSS ప్రకారం దర్యాప్తుకు వర్తించే టైమ్‌లైన్స్ స్పష్టంగా ప్రస్తావించాలి.

క్రింది నిర్మాణం (Headings) లో మాత్రమే నివేదిక అందించాలి:
1. వర్తించే BNS Sections & Punishments (పాత IPC సెక్షన్ల పోలికలతో)
2. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్, రిమాండ్ నిబంధనలు)
3. BSA Evidence & Forensic Guidelines (సాక్ష్యాధారాలు, ఫోరెన్సిక్ నిబంధనలు)
4. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text and not uploaded_image and not uploaded_pdf_bytes:
        st.warning("దయచేసి వివరాలు రాయండి లేదా ఫోటో/PDF అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner("చట్టాల ప్రకారం నివేదిక రూపొందిస్తోంది..."):
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("GEMINI_API_KEY కాన్ఫిగర్ చేయబడలేదు. Streamlit Secrets లో API Key సెట్ చేయండి.")
                    st.stop()

                client = genai.Client(api_key=api_key)

                # క్రైమ్ సంబంధిత పదాల వల్ల ఆగిపోకుండా Safety Settings
                safety_settings = [
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
                ]

                config = types.GenerateContentConfig(
                    system_instruction=legal_system_instruction,
                    temperature=0.0,
                    safety_settings=safety_settings
                )

                content = []

                if uploaded_image:
                    content.append(uploaded_image)
                elif uploaded_pdf_bytes:
                    content.append(
                        types.Part.from_bytes(
                            data=uploaded_pdf_bytes,
                            mime_type="application/pdf"
                        )
                    )

                if case_text:
                    content.append(f"కేసు ఫిర్యాదు వివరాలు:\n{case_text}")
                else:
                    content.append("అప్‌లోడ్ చేసిన డాక్యుమెంట్ లేదా ఫోటోలోని వివరాలను పరిశీలించి పూర్తి విశ్లేషణ అందించండి.")

                # ఖచ్చితమైన స్థిరమైన మోడల్
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=content,
                    config=config
                )

                if response and response.text:
                    st.markdown("### 📋 దర్యాప్తు నివేదిక:")
                    st.markdown(response.text)

                    st.download_button(
                        label="📥 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=response.text,
                        file_name="Legal_Investigation_Report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
