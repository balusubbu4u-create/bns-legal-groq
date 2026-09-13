
import streamlit as st
from groq import Groq
from PIL import Image
import io

# PDF కోసం
try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR కోసం
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# =========================================================
# 1. STREAMLIT PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="Police Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్")
st.subheader("BNS, BNSS & BSA ఆధారంగా Investigation Guidance")

st.write(
    "దర్యాప్తు అధికారులు (IO) కేసు వివరాలు లేదా ఫిర్యాదు ఆధారంగా "
    "చట్టపరమైన మరియు దర్యాప్తు మార్గదర్శకాలను పొందవచ్చు."
)


# =========================================================
# 2. GROQ API KEY
# =========================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error(
        "⚠️ GROQ_API_KEY కనుగొనబడలేదు. "
        "Streamlit Secrets లో API Key సెట్ చేయండి."
    )
    st.stop()


# =========================================================
# 3. GROQ CLIENT
# =========================================================

client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# 4. SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
మీరు భారతదేశంలోని నూతన క్రిమినల్ చట్టాలపై అవగాహన ఉన్న
Police Legal & Investigation Assistant.

మీ ప్రధాన చట్టాలు:

1. Bharatiya Nyaya Sanhita, 2023 (BNS)
2. Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
3. Bharatiya Sakshya Adhiniyam, 2023 (BSA)

మీరు ముఖ్యంగా పోలీస్ అధికారులు మరియు Investigation Officers (IO)
కోసం తెలుగులో స్పష్టమైన, ఆచరణాత్మకమైన మార్గదర్శకాలు ఇవ్వాలి.

చట్టపరమైన సెక్షన్ లేదా procedural detail పై సందేహం ఉంటే
ఖచ్చితంగా నిర్ధారించని విషయాన్ని ఖచ్చితమైన చట్టంగా చూపకండి.
అవసరమైతే "చట్టపుస్తకం/తాజా అధికారిక నోటిఫికేషన్‌తో నిర్ధారించాలి"
అని పేర్కొనండి.

ప్రతి కేసు విశ్లేషణను సాధ్యమైనంత వరకు క్రింది ఫార్మాట్‌లో ఇవ్వండి:


================================================
1. కేసు సంక్షిప్త వివరాలు
================================================

• ఫిర్యాదు యొక్క ముఖ్యాంశాలు
• జరిగిన నేరం యొక్క స్వభావం
• అవసరమైతే ప్రధాన నిందితుల చర్యలు


================================================
2. వర్తించే చట్టాలు మరియు సెక్షన్లు
================================================

ప్రతి సంబంధిత నేరానికి:

• Offence Name
• BNS Section
• సంబంధిత పాత IPC Section
• BNSS procedural provisions
• అవసరమైతే BSA provisions

సెక్షన్లు అనిశ్చితంగా ఉంటే వాటిని స్పష్టంగా పేర్కొనండి.


================================================
3. శిక్ష మరియు బెయిల్
================================================

ప్రతి ముఖ్య నేరానికి:

• Punishment
• Cognizable / Non-Cognizable
• Bailable / Non-Bailable
• Triable by which Court


================================================
4. FIR నమోదు విధానం
================================================

వివరించవలసిన అంశాలు:

• Cognizable offence అయితే FIR నమోదు
• Oral complaint అయితే విధానం
• Written complaint అయితే విధానం
• Electronic communication ద్వారా complaint వచ్చినప్పుడు
  చట్టపరమైన చర్యలు
• Zero FIR అవసరమైతే దాని ప్రక్రియ
• Preliminary Enquiry అవసరమా లేదా
• సంబంధిత BNSS provisions

ఏ సమయ పరిమితి లేదా సంతకం నిబంధనను పేర్కొన్నప్పుడు
అది సంబంధిత చట్ట provision తో సరిపోతుందో జాగ్రత్తగా చూడాలి.


================================================
5. Investigation SOP
================================================

దర్యాప్తు దశలను వరుసగా ఇవ్వండి:

1. FIR నమోదు
2. Crime Scene Protection
3. Scene Inspection
4. Photography
5. Videography
6. Panchanama / Mahazar
7. Witness Examination
8. Accused Identification
9. Arrest / Notice procedure
10. Search and Seizure
11. Recovery
12. Medical / Forensic Evidence
13. CCTV Evidence
14. Mobile Phone Evidence
15. WhatsApp / Digital Evidence
16. FSL / CFSL పంపే విధానం


================================================
6. Arrest Guidelines
================================================

అవసరమైతే వివరించండి:

• Arrest అవసరమా?
• Notice of appearance సరిపోతుందా?
• Arrest memo
• Grounds of arrest
• కుటుంబ సభ్యులకు సమాచారం
• మహిళలు / పిల్లలు / ప్రత్యేక వర్గాల విషయంలో
  ప్రత్యేక చట్టపరమైన నిబంధనలు


================================================
7. Digital Evidence - BSA
================================================

ఈ evidence ఉంటే వివరించండి:

• CCTV
• Mobile Phone
• WhatsApp
• Call Records
• SMS
• Email
• Social Media

Digital evidence కోసం:

• Original device preservation
• Hash value
• Forensic extraction
• Chain of custody
• Seizure Panchanama
• BSA electronic evidence provisions
• BSA Section 63 certificate అవసరమైతే దాని విధానం


================================================
8. Recovery Procedure
================================================

దొంగిలించిన property లేదా ఇతర material వస్తువులు ఉంటే:

• Recovery memo
• Panch witnesses
• Seizure procedure
• Identification
• Property preservation
• Court property procedure


================================================
9. Forensic Requirements
================================================

అవసరమైతే:

• Fingerprints
• DNA
• Blood samples
• Weapon examination
• CCTV forensic copy
• Mobile forensic examination
• FSL report


================================================
10. Charge Sheet / Final Report
================================================

చార్జిషీట్‌కు ముందు చేయవలసినవి:

• అన్ని witness statements
• Documentary evidence
• Material Objects
• FSL reports
• Medical reports
• Digital evidence certificate
• Case diary completeness
• అవసరమైన approvals

అవసరమైనప్పుడు BNSS Section 193 ప్రకారం
Police Report / Final Report requirements వివరించండి.


================================================
11. IO Checklist
================================================

చివరిగా చిన్న checklist ఇవ్వండి:

☐ FIR
☐ Crime Scene
☐ Witnesses
☐ CCTV
☐ Digital Evidence
☐ Seizures
☐ Arrest / Notice
☐ Recovery
☐ Forensic Evidence
☐ FSL
☐ BSA Certificate
☐ Case Diary
☐ Charge Sheet


================================================

ముఖ్య సూచన:

మీరు పోలీస్ అధికారికి ఉపయోగపడే విధంగా
చట్టపరమైన మార్గదర్శకాలు ఇవ్వాలి.

కానీ ప్రతి కేసు facts ఆధారంగా sections మారవచ్చు.

ఖచ్చితమైన సెక్షన్ తెలియకపోతే ఊహించవద్దు.

సమాధానం తెలుగులో ఇవ్వండి.
అవసరమైన చోట English Legal Terms ఉపయోగించవచ్చు.
"""


# =========================================================
# 5. PDF TEXT EXTRACTION
# =========================================================

def extract_text_from_pdf(uploaded_file):

    if not PDF_AVAILABLE:
        return "PDF reader library అందుబాటులో లేదు."

    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)

        text = ""

        for page in pdf_reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    except Exception as e:
        return f"PDF చదవడంలో లోపం: {str(e)}"


# =========================================================
# 6. TXT TEXT EXTRACTION
# =========================================================

def extract_text_from_txt(uploaded_file):

    try:
        return uploaded_file.read().decode("utf-8")

    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return uploaded_file.read().decode("latin-1")

    except Exception as e:
        return f"TXT చదవడంలో లోపం: {str(e)}"


# =========================================================
# 7. IMAGE OCR
# =========================================================

def extract_text_from_image(uploaded_file):

    try:

        image = Image.open(uploaded_file)

        if not OCR_AVAILABLE:
            return (
                "Image OCR ప్రస్తుతం అందుబాటులో లేదు. "
                "ఈ image లో ఉన్న complaint వివరాలను manual గా "
                "text box లో టైప్ చేయండి."
            )

        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        return text

    except Exception as e:
        return f"Image OCR లో లోపం: {str(e)}"


# =========================================================
# 8. FILE CONTENT EXTRACTION
# =========================================================

def extract_file_content(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return extract_text_from_txt(uploaded_file)

    elif file_name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    elif file_name.endswith(
        (
            ".jpg",
            ".jpeg",
            ".png"
        )
    ):
        return extract_text_from_image(uploaded_file)

    else:
        return ""


# =========================================================
# 9. GROQ INVESTIGATION FUNCTION
# =========================================================

def investigate_case(police_query: str):

    try:

        chat_completion = client.chat.completions.create(

            messages=[

                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },

                {
                    "role": "user",
                    "content": police_query
                }

            ],

            # పాత llama3-70b-8192 తొలగించబడింది
            model="openai/gpt-oss-120b",

            temperature=0.2,

            max_tokens=3000

        )

        return chat_completion.choices[0].message.content

    except Exception as e:

        return (
            "లోపం సంభవించింది:\n\n"
            + str(e)
        )


# =========================================================
# 10. STREAMLIT FILE UPLOAD UI
# =========================================================

st.markdown("---")

st.subheader(
    "📁 కేసు డాక్యుమెంట్ లేదా ఫిర్యాదు అప్‌లోడ్ చేయండి"
)

uploaded_file = st.file_uploader(

    "PDF, TXT, JPG లేదా PNG ఫైల్‌ను ఎంచుకోండి",

    type=[
        "pdf",
        "txt",
        "jpg",
        "jpeg",
        "png"
    ]

)


file_content = ""


if uploaded_file is not None:

    st.success(
        f"ఫైల్ విజయవంతంగా అప్‌లోడ్ అయింది: "
        f"{uploaded_file.name}"
    )

    with st.spinner(
        "ఫైల్ నుండి వివరాలు చదువుతున్నాము..."
    ):

        file_content = extract_file_content(
            uploaded_file
        )


# =========================================================
# 11. DEFAULT CASE
# =========================================================

default_query = """
బాధితుడి ఇంటి తాళాలు పగలగొట్టి రాత్రి పూట
10 తులాల బంగారం దొంగిలించారు.

బాధితుడు ఊర్లో లేడు.

వాట్సాప్ ద్వారా కుటుంబ సభ్యులకు
సమాచారం ఇచ్చారు.

దీనికి:

1. వర్తించే BNS సెక్షన్లు
2. పాత IPC సెక్షన్లు
3. శిక్ష
4. బెయిల్ స్వభావం
5. FIR విధానం
6. Crime Scene SOP
7. Recovery Procedure
8. Digital Evidence
9. CCTV Evidence
10. Arrest Procedure
11. BSA Section 63 Certificate
12. Charge Sheet వరకు పూర్తి SOP

వివరించండి.
"""


# =========================================================
# 12. TEXT AREA
# =========================================================

initial_text = (
    file_content
    if file_content.strip()
    else default_query
)


user_query = st.text_area(

    "లేదా కేసు వివరాలను ఇక్కడ టైప్ చేయండి:",

    value=initial_text,

    height=250

)


# =========================================================
# 13. GENERATE REPORT BUTTON
# =========================================================

if st.button(
    "⚖️ మార్గదర్శకాలు రూపొందించు",
    use_container_width=True
):

    if not user_query.strip():

        st.error(
            "దయచేసి కేసు వివరాలు ఇవ్వండి "
            "లేదా డాక్యుమెంట్‌ను అప్‌లోడ్ చేయండి."
        )

    else:

        with st.spinner(
            "విచారణ అధికారికి చట్టపరమైన మార్గదర్శకాలు "
            "తయారు చేయబడుతున్నాయి..."
        ):

            report = investigate_case(
                user_query
            )


        if report.startswith(
            "లోపం సంభవించింది"
        ):

            st.error(report)

        else:

            st.success(
                "నివేదిక విజయవంతంగా తయారైంది!"
            )

            st.markdown("---")

            st.markdown(report)


# =========================================================
# 14. FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "⚖️ Police Legal & Investigation Assistant | "
    "BNS | BNSS | BSA"
)
```
