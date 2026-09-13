import os
import streamlit as st
from groq import Groq

# 1. Streamlit పేజ్ సెటప్
st.set_page_config(page_title="Police Legal & Investigation Assistant", layout="wide")

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్ (BNS, BNSS, BSA)")
st.write("నూతన క్రిమినల్ చట్టాల ప్రకారం దర్యాప్తు అధికారుల (IO) కోసం మార్గదర్శకాలు.")

# 2. API Key సెటప్ (సైడ్‌బార్‌లో)
api_key_input = st.sidebar.text_input("Groq API Key ఇవ్వండి:", type="password")

if api_key_input:
    GROQ_API_KEY = api_key_input
else:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# 3. పోలీసుల విచారణ ప్రక్రియకు తగిన స్ట్రక్చర్డ్ సిస్టమ్ ప్రాంప్ట్
SYSTEM_PROMPT = """
మీరు భారతీయ నూతన క్రిమినల్ చట్టాలపై (BNS, BNSS, BSA) లోతైన అవగాహన ఉన్న పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్.
పోలీస్ అధికారులు లేదా దర్యాప్తు అధికారులకు (IO) అర్థమయ్యేలా తెలుగులో స్పష్టమైన, ఆచరణాత్మకమైన సమాధానాలు ఇవ్వాలి.

ఫిర్యాదు ఏ రూపంలో ఉన్నా (లిఖితపూర్వకం, నోటి మాట, e-FIR, లేదా జీరో FIR), ప్రతి నేరానికి సమాధానం క్రింది ఖచ్చితమైన ఫార్మాట్‌లో ఉండాలి:

1. **నేర ప్రాథమిక వివరాలు & సెక్షన్ల పోలిక:**
   - నేరం పేరు (Offence Name)
   - BNS సెక్షన్ (Bharatiya Nyaya Sanhita, 2023) vs పాత IPC సెక్షన్
   - సంబంధిత BNSS సెక్షన్ (Bharatiya Nagarik Suraksha Sanhita, 2023) vs పాత CrPC సెక్షన్
   - సంబంధిత BSA సెక్షన్ (Bharatiya Sakshya Adhiniyam, 2023) vs పాత IEA సెక్షన్ (సాక్ష్యాధారాల నిబంధనలు)

2. **శిక్ష & బెయిల్ స్వభావం:**
   - శిక్ష పరిమాణం (ఖైదు, జరిమానా)
   - Cognizable / Non-Cognizable
   - Bailable / Non-Bailable
   - ఏ కోర్టు విచారిస్తుంది (Triable by which Court)

3. **ఫిర్యాదు స్వీకరణ & FIR నమోదు:**
   - ఫిర్యాదు ఏ రూపంలో ఉన్నా తీసుకోవలసిన జాగ్రత్తలు (BNSS సెక్షన్ 173 ప్రకారం: రాతపూర్వకం/మౌఖికం/e-FIR).
   - e-FIR లేదా జీరో FIR అయితే సంతకం ఎప్పుడు తీసుకోవాలి (3 రోజుల్లోపు భౌతిక సంతకం).
   - ప్రాథమిక విచారణ (Preliminary Enquiry - 14 రోజులు) అవసరమా లేదా నేరుగా FIR కట్టాలా.

4. **దర్యాప్తు విధానం (Investigation SOP - BNSS & BSA):**
   - అరెస్ట్ నిబంధనలు (BNSS 35 - 7 ఏళ్ల లోపు శిక్ష ఉన్న కేసుల్లో నోటీస్ & డీఎస్పీ అనుమతులు).
   - సంఘటనా స్థల పరిశీలన (Crime Scene) & ఫోరెన్సిక్ టీమ్ తప్పనిసరి నిబంధన (7 ఏళ్లకు పైబడిన శిక్ష గల కేసులకు BNSS 176(3)).
   - వీడియోగ్రఫీ & ఫోటోగ్రఫీ (పంచనామా, జప్తు - BNSS 105).
   - ఎలక్ట్రానిక్/డిజిటల్ సాక్ష్యాలు (మొబైల్, సీసీటీవీ, వాట్సాప్ చాట్లు) - BSA సెక్షన్ 61 & సెక్షన్ 63 సర్టిఫికేట్ నిబంధనలు.
   - సాక్షుల వాంగ్మూలాలు (BNSS 180 - ఆడియో-వీడియో రికార్డింగ్ సదుపాయం).

5. **చార్జిషీట్ దాఖలు (Final Report):**
   - BNSS సెక్షన్ 193 ప్రకారం చార్జిషీట్ నిబంధనలు.
   - రిమాండ్ గడువు (60 రోజులు లేదా 90 రోజుల కాలపరిమితి - BNSS 187).
   - చార్జిషీట్‌తో జతపరచవలసిన ప్రాథమిక డాక్యుమెంట్ల జాబితా (మహజర్, సీఎఫ్ఎస్ఎల్ రిపోర్ట్, BSA సర్టిఫికేట్, మెడికల్ రిపోర్ట్ మొదలైనవి).
"""

def investigate_case(police_query: str, client_obj):
    try:
        chat_completion = client_obj.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": police_query}
            ],
            model="llama-3.1-8b-instant",  # <--- మోడల్ పేరు అప్‌డేట్ చేయబడింది
            temperature=0.2,
            max_tokens=2500
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"లోపం సంభవించింది: {str(e)}"

# 4. Streamlit UI (ఫైల్ అప్‌లోడ్ మరియు టెక్స్ట్ ఇన్‌పుట్)
st.subheader("📁 కేసు డాక్యుమెంట్ లేదా ఫిర్యాదు అప్‌లోడ్ చేయండి")
uploaded_file = st.file_uploader("ఫైల్‌ను ఎంచుకోండి (PDF, TXT, JPG, PNG)", type=["pdf", "txt", "jpg", "png", "jpeg"])

file_content = ""
if uploaded_file is not None:
    st.success(f"ఫైల్ విజయవంతంగా అప్‌లోడ్ అయింది: {uploaded_file.name}")
    if uploaded_file.type == "text/plain":
        file_content = str(uploaded_file.read(), "utf-8")

default_query = """బాధితుడి ఇంటి తాళాలు పగలగొట్టి రాత్రి పూట 10 తులాల బంగారం దొంగిలించారు. 
బాధితుడు ఊర్లో లేడు, వాట్సాప్ లో మెసేజ్ ద్వారా సమాచారం పంపాడు. 
దీనికి సెక్షన్లు, శిక్ష, బెయిల్, రికవరీ, డిజిటల్ ఎవిడెన్స్ మరియు చార్జిషీట్ వరకు SOP వివరాలు ఇవ్వండి."""

initial_text = file_content if file_content else default_query
user_query = st.text_area("లేదా కేసు వివరాలు ఇక్కడ టైప్ చేయండి:", value=initial_text, height=150)

if st.button("మార్గదర్శకాలు రూపొందించు (Generate Report)"):
    if not GROQ_API_KEY:
        st.error("దయచేసి మీ Groq API Key ని సైడ్‌బార్‌లో ఎంటర్ చేయండి.")
    elif not user_query.strip():
        st.error("దయచేసి కేసు వివరాలు ఇవ్వండి లేదా డాక్యుమెంట్‌ను అప్‌లోడ్ చేయండి.")
    else:
        with st.spinner("విచారణ అధికారికి మార్గదర్శకాలు తయారు చేయబడుతున్నాయి..."):
            client = Groq(api_key=GROQ_API_KEY)
            report = investigate_case(user_query, client)
            st.success("నివేదిక విజయవంతంగా తయారైంది!")
            st.markdown("---")
            st.markdown(report)
