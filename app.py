import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="BNS Legal Assistant (Groq)",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ అసిస్టెంట్ (Groq)")
st.write("కేసు వివరాలు నమోదు చేసి విశ్లేషించండి.")

# లీగల్ నిబంధనల ప్రాంప్ట్
legal_system_instruction = """
మీరు భారతీయ క్రిమినల్ చట్టాలు (Bharatiya Nyaya Sanhita - BNS, Bharatiya Nagarik Suraksha Sanhita - BNSS, Bharatiya Sakshya Adhiniyam - BSA) పై ప్రావీణ్యం ఉన్న అధికారిక లీగల్ అసిస్టెంట్.

ముఖ్య నియమాలు & మార్గదర్శకాలు:
1. వాస్తవాల ఆధారితం: అందించిన ఫిర్యాదులోని వాస్తవాల ఆధారంగా మాత్రమే ఖచ్చితమైన సెక్షన్లు పేర్కొనాలి.
2. ఖచ్చితత్వం: చట్టపరమైన సెక్షన్లలో ఎలాంటి ఊహాజనిత (hallucinated) నంబర్లు చెప్పకూడదు.
3. లీగల్ టెర్మినాలజీ: విశ్లేషణ తెలుగులో ఉండాలి. ముఖ్యమైన లీగల్ పదాలు, సెక్షన్ పేర్లను బ్రాకెట్లలో ఇంగ్లీష్‌లో కూడా రాయాలి.
4. కాలపరిమితులు: BNSS ప్రకారం దర్యాప్తుకు వర్తించే టైమ్‌లైన్స్ స్పష్టంగా ప్రస్తావించాలి.

క్రింది నిర్మాణం (Headings) లో మాత్రమే నివేదిక అందించాలి:
1. వర్తించే BNS Sections & Punishments (పాత IPC పోలికలతో)
2. BNSS Procedures & Timelines (నోటీసులు, అరెస్ట్, రిమాండ్ నిబంధనలు)
3. BSA Evidence & Forensic Guidelines (సాక్ష్యాధారాలు, ఫోరెన్సిక్ నిబంధనలు)
4. IO (Investigating Officer) కోసం Action Checklist

చివరలో తప్పనిసరిగా:
"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే; తుది చట్టపరమైన నిర్ణయాలు మరియు కోర్టు ప్రక్రియల కోసం న్యాయ నిపుణులను సంప్రదించాలి." అని రాయండి.
"""

case_text = st.text_area(
    "ఫిర్యాదు వివరాలు ఇక్కడ రాయండి:",
    height=160,
    placeholder="ఉదాహరణ: ఒక వ్యక్తి ఇంట్లోకి అక్రమంగా ప్రవేశించి బెదిరింపులకు పాల్పడ్డాడు..."
)

if st.button("కేస్ విశ్లేషించండి (Analyze with Groq)", type="primary"):
    if not case_text:
        st.warning("దయచేసి ఫిర్యాదు వివరాలను నమోదు చేయండి.")
    else:
        with st.spinner("Groq ద్వారా వేగంగా చట్టాలను పరిశీలిస్తోంది..."):
            try:
                api_key = st.secrets.get("GROQ_API_KEY")
                if not api_key:
                    st.error("GROQ_API_KEY కాన్ఫిగర్ చేయబడలేదు. Streamlit Secrets లో Key ని యాడ్ చేయండి.")
                    st.stop()

                client = Groq(api_key=api_key)

                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": legal_system_instruction},
                        {"role": "user", "content": f"కేసు వివరాలు:\n{case_text}"}
                    ]
                )

                result = chat_completion.choices[0].message.content

                if result:
                    st.markdown("### 📋 దర్యాప్తు నివేదిక:")
                    st.markdown(result)
                    
                    st.download_button(
                        label="📄 నివేదిక డౌన్‌లోడ్ చేయండి (TXT)",
                        data=result,
                        file_name="BNS_Legal_Report_Groq.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం ఏర్పడింది: {e}")
