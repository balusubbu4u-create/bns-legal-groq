import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="BNS Legal Assistant (Groq)",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్")
st.write("కేసు వివరాలు నమోదు చేసి క్షణాల్లో చట్టపరమైన నివేదిక పొందండి.")

# సైడ్‌బార్‌లో API Key ఆప్షన్
api_key = st.secrets.get("GROQ_API_KEY") or st.sidebar.text_input(
    "🔑 Groq API Key:",
    type="password",
    help="Groq Console నుండి తీసుకున్న API Key ఇక్కడ ఇవ్వండి"
)

# లీగల్ ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) పై ప్రావీణ్యం ఉన్న అధికారిక లీగల్ అసిస్టెంట్.

ముఖ్య నియమాలు:
1. వాస్తవాల ఆధారితం: అందించిన ఫిర్యాదు వివరాల ఆధారంగా మాత్రమే ఖచ్చితమైన సెక్షన్లు పేర్కొనాలి.
2. లీగల్ టెర్మినాలజీ: నివేదిక తెలుగులో స్పష్టంగా ఉండాలి. సెక్షన్ పేర్లు, వర్గీకరణలను బ్రాకెట్లలో ఇంగ్లీష్‌లో కూడా ఇవ్వాలి.
3. కాలపరిమితులు: BNSS ప్రకారం దర్యాప్తుకు వర్తించే సమయ పరిమితులు (Timelines) స్పష్టంగా ప్రస్తావించాలి.

క్రింది క్రమంలో మాత్రమే నివేదిక అందించాలి:
1. వర్తించే BNS Sections & Punishments (పాత IPC పోలికలతో)
2. నేరం యొక్క వర్గీకరణ (Cognizable/Non-Cognizable, Bailable/Non-Bailable)
3. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్, రిమాండ్ నిబంధనలు)
4. BSA Evidence Guidelines (సాక్ష్యాధారాల సేకరణ, డిజిటల్ సాక్ష్యాలు)
5. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

case_text = st.text_area(
    "ఫిర్యాదు వివరాలు ఇక్కడ రాయండి:",
    height=200,
    placeholder="ఉదాహరణ: ఇంట్లో ఎవరూ లేని సమయంలో గుర్తుతెలియని వ్యక్తులు చొరబడి నల్లపూసల గొలుసు, ఉంగరాలు దొంగిలించారు..."
)

if st.button("కేస్ విశ్లేషించండి (Analyze)", type="primary"):
    if not case_text.strip():
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి.")
    elif not api_key:
        st.error("Groq API Key కాన్ఫిగర్ చేయబడలేదు. దయచేసి ఎడమవైపు సైడ్‌బార్‌లో Key ని నమోదు చేయండి.")
    else:
        with st.spinner("BNS, BNSS, BSA చట్టాల ప్రకారం విశ్లేషిస్తోంది..."):
            try:
                client = Groq(api_key=api_key)

                # llama-3.1-8b-instant ఎల్లప్పుడూ ఉచితంగా మరియు వేగంగా పనిచేస్తుంది
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
                        label="📥 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="BNS_Legal_Report.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
