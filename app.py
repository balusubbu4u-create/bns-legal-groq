import streamlit as st
from groq import Groq
import base64
import io
from PIL import Image

st.set_page_config(
    page_title="BNS Legal Assistant (Groq)",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్ (Groq)")
st.write("కేసు వివరాలు నమోదు చేయండి లేదా ఫిర్యాదు ఫోటో అప్‌లోడ్ చేయండి.")

# సైడ్‌బార్‌లో API Key ఆప్షన్ (secrets లేకపోయినా పనిచేస్తుంది)
api_key = st.secrets.get("GROQ_API_KEY") or st.sidebar.text_input(
    "🔑 Groq API Key ఇక్కడ ఇవ్వండి:",
    type="password"
)

tab1, tab2 = st.tabs(["📝 టెక్స్ట్ వివరాలు", "📷 ఫోటో అప్‌లోడ్"])

case_text = ""
uploaded_image = None

with tab1:
    text_input = st.text_area(
        "ఫిర్యాదు వివరాలు ఇక్కడ రాయండి:",
        height=160,
        placeholder="ఉదాహరణ: ఒక వ్యక్తి ఇంట్లోకి అక్రమంగా ప్రవేశించి బెదిరింపులకు పాల్పడ్డాడు..."
    )
    if text_input:
        case_text = text_input

with tab2:
    uploaded_file = st.file_uploader(
        "ఫిర్యాదు కాపీ ఫోటో ఎంచుకోండి (JPG, PNG)",
        type=["jpg", "jpeg", "png"]
    )
    if uploaded_file:
        uploaded_image = Image.open(uploaded_file)
        st.image(uploaded_image, caption="అప్‌లోడ్ చేసిన చిత్రం", use_container_width=True)

# లీగల్ నిబంధనల ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) పై ప్రావీణ్యం ఉన్న అధికారిక లీగల్ అసిస్టెంట్.

ముఖ్య నియమాలు & మార్గదర్శకాలు:
1. వాస్తవాల ఆధారితం: అందించిన వివరాలు/చిత్రంలోని వాస్తవాల ఆధారంగా మాత్రమే ఖచ్చితమైన సెక్షన్లు పేర్కొనాలి.
2. ఖచ్చితత్వం: చట్టపరమైన సెక్షన్లలో ఎలాంటి ఊహాజనిత నంబర్లు చెప్పకూడదు.
3. లీగల్ టెర్మినాలజీ: విశ్లేషణ తెలుగులో ఉండాలి. ముఖ్యమైన సెక్షన్ పేర్లను బ్రాకెట్లలో ఇంగ్లీష్‌లో కూడా రాయాలి.
4. కాలపరిమితులు: BNSS ప్రకారం దర్యాప్తుకు వర్తించే టైమ్‌లైన్స్ స్పష్టంగా ప్రస్తావించాలి.

క్రింది నిర్మాణం (Headings) లో మాత్రమే నివేదిక అందించాలి:
1. వర్తించే BNS Sections & Punishments (పాత IPC పోలికలతో)
2. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్, రిమాండ్ నిబంధనలు)
3. BSA Evidence & Forensic Guidelines (సాక్ష్యాధారాలు, ఫోరెన్సిక్ నిబంధనలు)
4. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text and not uploaded_image:
        st.warning("దయచేసి వివరాలు రాయండి లేదా ఫోటో అప్‌లోడ్ చేయండి.")
    elif not api_key:
        st.error("Groq API Key కాన్ఫిగర్ చేయబడలేదు. దయచేసి ఎడమవైపు సైడ్‌బార్‌లో API Key ని నమోదు చేయండి.")
    else:
        with st.spinner("Groq ద్వారా వేగంగా చట్టాలను పరిశీలిస్తోంది..."):
            try:
                client = Groq(api_key=api_key)

                # ఫోటో అప్‌లోడ్ చేసినప్పుడు: Groq Vision Model
                if uploaded_image:
                    buffered = io.BytesIO()
                    uploaded_image.save(buffered, format="JPEG")
                    base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")

                    response = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        temperature=0.0,
                        messages=[
                            {"role": "system", "content": legal_system_instruction},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "ఈ చిత్రంలోని ఫిర్యాదు వివరాలను చదివి చట్టాల ప్రకారం విశ్లేషించండి."},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_img}"
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                # కేవలం టెక్స్ట్ రాసినప్పుడు: Groq Instant Model
                else:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
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
