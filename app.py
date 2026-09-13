import streamlit as st
from groq import Groq
from pypdf import PdfReader
import io
import base64


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("⚖️ BNS, BNSS & BSA లీగల్ & దర్యాప్తు అసిస్టెంట్")

st.caption(
    "BNS, BNSS, BSA మరియు పాత IPC, CrPC, IEA చట్టాల ఆధారంగా "
    "కేసు వివరాల విశ్లేషణ"
)


# =========================================================
# GROQ API KEY CHECK
# =========================================================

if "GROQ_API_KEY" not in st.secrets:

    st.error(
        "❌ GROQ_API_KEY కనిపించలేదు.\n\n"
        "Streamlit → App Settings → Secrets లో "
        "GROQ_API_KEY నమోదు చేయండి."
    )

    st.stop()


api_key = st.secrets["GROQ_API_KEY"]


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(
    api_key=api_key
)


# =========================================================
# MODEL SETTINGS
# =========================================================

st.sidebar.header("⚙️ AI Model")

# ప్రస్తుతం పనిచేస్తున్న Qwen model
selected_model = "qwen/qwen3.6-27b"

st.sidebar.success(
    f"✅ Active Model:\n{selected_model}"
)


# =========================================================
# SIDEBAR INFORMATION
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader("📚 Laws Covered")

st.sidebar.write("• BNS – Bharatiya Nyaya Sanhita")
st.sidebar.write("• BNSS – Bharatiya Nagarik Suraksha Sanhita")
st.sidebar.write("• BSA – Bharatiya Sakshya Adhiniyam")

st.sidebar.markdown("---")

st.sidebar.info(
    "⚠️ AI ఇచ్చే legal analysis ను "
    "అధికారిక చట్ట గ్రంథం / అధికారిక నోటిఫికేషన్‌తో "
    "తప్పనిసరిగా verify చేయండి."
)


# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

LEGAL_SYSTEM_PROMPT = """

మీరు భారతదేశ క్రిమినల్ లా గురించి విశ్లేషించే Legal & Investigation Assistant.

ప్రధానంగా క్రింది చట్టాలను ఉపయోగించాలి:

1. Bharatiya Nyaya Sanhita, 2023 (BNS)
2. Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
3. Bharatiya Sakshya Adhiniyam, 2023 (BSA)

అవసరమైనప్పుడు పాత చట్టాలతో comparison ఇవ్వాలి:

4. Indian Penal Code, 1860 (IPC)
5. Code of Criminal Procedure, 1973 (CrPC)
6. Indian Evidence Act, 1872 (IEA)


==============================
VERY IMPORTANT ACCURACY RULES
==============================

• Section number ఊహించి చెప్పకూడదు.

• BNS section ను IPC section తో compare చేసేటప్పుడు
  exact correspondence లేకపోతే "exact equivalent కాదు" అని చెప్పాలి.

• ఒక offence పేరు చూసి section number guess చేయకూడదు.

• Facts ఆధారంగా offence elements ను ముందుగా గుర్తించాలి.

• Punishment, cognizable, non-cognizable, bailable,
  non-bailable వంటి విషయాలు చెప్పేటప్పుడు section
  applicability ని జాగ్రత్తగా పరిశీలించాలి.

• BNSS procedure sections ను BNS offence sections తో
  కలపకూడదు.

• BSA evidence sections ను BNS offence sections తో
  కలపకూడదు.

• ఏదైనా section గురించి ఖచ్చితంగా తెలియకపోతే
  తప్పు section చెప్పడం కంటే verification అవసరం అని చెప్పాలి.


==============================
LEGAL ANALYSIS FORMAT
==============================

కేసు వివరాలను ఈ క్రమంలో విశ్లేషించండి:

1. సంఘటన సారాంశం

2. ప్రధాన allegations

3. Possible offences

4. ప్రతి offence కు:
   - BNS Section
   - Offence name
   - ఎందుకు apply అవుతుంది
   - Punishment
   - Cognizable / Non-Cognizable
   - Bailable / Non-Bailable

5. Old IPC equivalent
   - Exact equivalent ఉంటే మాత్రమే చెప్పాలి
   - లేకపోతే "Exact equivalent కాదు" అని చెప్పాలి

6. BNSS procedural provisions

7. BSA evidence provisions

8. Investigation steps

9. IO Checklist

10. Digital Evidence

11. CCTV / Mobile / CDR / WhatsApp / Social Media evidence

12. అవసరమైన documents / witnesses

13. Final legal observations


==============================
INVESTIGATION GUIDANCE
==============================

అవసరమైనప్పుడు:

• FIR registration
• Preliminary enquiry
• Scene of offence
• Scene documentation
• Witness examination
• CCTV collection
• Electronic evidence preservation
• Mobile / digital evidence
• Seizure procedure
• Search procedure
• Arrest considerations
• Medical evidence
• Documentary evidence
• Case diary
• Final report / charge sheet

వంటి అంశాలను practical investigation checklist రూపంలో ఇవ్వండి.


==============================
ELECTRONIC EVIDENCE
==============================

Electronic evidence విషయంలో:

• CCTV
• Mobile phone
• Computer
• DVR/NVR
• Call records
• WhatsApp chats
• Emails
• Digital photographs
• Audio/video recordings
• GPS/location data

వంటి evidence గురించి చెప్పేటప్పుడు BSA provisions
మరియు certificate requirements ను facts ఆధారంగా వివరించాలి.

BSA Section 63 గురించి చెప్పేటప్పుడు:
ప్రతి electronic evidence కు ఒకే విధమైన blanket statement
ఇవ్వకూడదు.

Evidence source, device, lawful control, working condition,
hash/value మరియు applicable certificate requirements
వంటి అంశాలను context ప్రకారం వివరించాలి.


==============================
LANGUAGE
==============================

User Telugu లో అడిగితే Telugu లో సమాధానం ఇవ్వాలి.

Legal section names English లో ఉంచవచ్చు.

అవసరమైన చోట English + Telugu explanation ఇవ్వాలి.

చాలా technical legal terminology ఉంటే దాని simple Telugu meaning కూడా ఇవ్వాలి.


==============================
IMPORTANT DISCLAIMER
==============================

ఇది legal research / investigation assistance కోసం మాత్రమే.
Final legal decision కోసం official legislation, government
notifications, competent authority instructions మరియు
qualified legal professional verification అవసరం.
"""


# =========================================================
# FILE EXTRACTION FUNCTIONS
# =========================================================

def extract_pdf_text(file_bytes):

    try:

        pdf = PdfReader(
            io.BytesIO(file_bytes)
        )

        text = ""

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    except Exception as e:

        return f"PDF చదవడంలో error: {str(e)}"


def extract_text_file(file_bytes):

    try:

        return file_bytes.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception as e:

        return f"Text file చదవడంలో error: {str(e)}"


# =========================================================
# IMAGE ANALYSIS
# =========================================================

def analyze_image(
    image_bytes,
    mime_type,
    user_prompt
):

    try:

        encoded_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        response = client.chat.completions.create(

            model=selected_model,

            messages=[

                {
                    "role": "system",
                    "content": LEGAL_SYSTEM_PROMPT
                },

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",

                            "text": user_prompt
                        },

                        {
                            "type": "image_url",

                            "image_url": {

                                "url":
                                f"data:{mime_type};base64,{encoded_image}"

                            }
                        }

                    ]
                }

            ],

            temperature=0.1,

            max_tokens=6000

        )


        return response.choices[0].message.content


    except Exception as e:

        return f"""
❌ Image analysis error

{str(e)}
"""


# =========================================================
# TEXT ANALYSIS
# =========================================================

def analyze_text(user_prompt):

    try:

        response = client.chat.completions.create(

            model=selected_model,

            messages=[

                {
                    "role": "system",

                    "content": LEGAL_SYSTEM_PROMPT
                },

                {
                    "role": "user",

                    "content": user_prompt
                }

            ],

            temperature=0.1,

            max_tokens=6000

        )


        return response.choices[0].message.content


    except Exception as e:

        return f"""
❌ AI analysis error

{str(e)}
"""


# =========================================================
# MAIN TABS
# =========================================================

tab1, tab2 = st.tabs(
    [
        "📝 Text Details",
        "📷 Photo / Document"
    ]
)


# =========================================================
# TAB 1 - TEXT
# =========================================================

with tab1:

    st.subheader(
        "📝 కేసు వివరాలు నమోదు చేయండి"
    )

    case_text = st.text_area(

        "Case / Complaint Details",

        height=300,

        placeholder=(
            "ఉదాహరణ:\n"
            "సంఘటన తేదీ...\n"
            "సంఘటన జరిగిన ప్రదేశం...\n"
            "ఎవరెవరు పాల్గొన్నారు...\n"
            "ఏం జరిగింది...\n"
            "గాయాలు / నష్టం...\n"
            "CCTV / Mobile / ఇతర evidence..."
        )

    )


    if st.button(
        "⚖️ Legal Analysis",
        type="primary",
        key="text_analysis"
    ):

        if not case_text.strip():

            st.warning(
                "⚠️ ముందుగా కేసు వివరాలు నమోదు చేయండి."
            )

        else:

            with st.spinner(
                "🔎 Legal analysis జరుగుతోంది..."
            ):

                prompt = f"""

క్రింది కేసు వివరాలను పూర్తిగా విశ్లేషించండి.

CASE DETAILS:

{case_text}


క్రింది headings తప్పనిసరిగా ఉపయోగించండి:

## 1. సంఘటన సారాంశం

## 2. ప్రధాన Allegations

## 3. Possible BNS Offences

## 4. BNS Section-wise Analysis

## 5. IPC Comparison

## 6. Punishment

## 7. Cognizable / Non-Cognizable

## 8. Bailable / Non-Bailable

## 9. BNSS Procedure

## 10. BSA Evidence

## 11. Digital Evidence

## 12. Investigation Steps

## 13. IO Checklist

## 14. Documents / Witnesses Required

## 15. Final Legal Observations


IMPORTANT:

Section numbers guess చేయకండి.

Facts సరిపోకపోతే additional facts required అని చెప్పండి.

IPC equivalent exact కాకపోతే exact equivalent కాదు అని స్పష్టంగా చెప్పండి.
"""


                result = analyze_text(
                    prompt
                )


            st.markdown("---")

            st.subheader(
                "📋 Legal Analysis Result"
            )

            st.markdown(result)


            st.download_button(

                label="📥 Download Report",

                data=result,

                file_name="legal_analysis.txt",

                mime="text/plain",

                key="download_text_report"

            )


# =========================================================
# TAB 2 - PHOTO / DOCUMENT
# =========================================================

with tab2:

    st.subheader(
        "📷 Complaint / Document Upload"
    )

    uploaded_file = st.file_uploader(

        "PDF / TXT / JPG / JPEG / PNG / WEBP upload చేయండి",

        type=[
            "pdf",
            "txt",
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]

    )


    if uploaded_file is not None:

        file_bytes = uploaded_file.read()

        file_name = uploaded_file.name.lower()


        st.success(
            f"✅ File uploaded: {uploaded_file.name}"
        )


        # -------------------------------------------------
        # IMAGE FILE
        # -------------------------------------------------

        if file_name.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            )
        ):

            st.image(
                file_bytes,
                caption="Uploaded Image",
                use_container_width=True
            )


            if st.button(
                "🔎 Analyze Image",
                type="primary",
                key="image_analysis"
            ):

                with st.spinner(
                    "📷 Image చదివి legal analysis చేస్తున్నాను..."
                ):

                    mime_type = uploaded_file.type

                    prompt = """

ఈ uploaded complaint/document image ను చదవండి.

ముందుగా image లో ఉన్న text ను అర్థం చేసుకోండి.

తర్వాత క్రింది అంశాలను విశ్లేషించండి:

1. Complaint Summary
2. Allegations
3. Important Facts
4. Possible BNS Offences
5. Relevant BNS Sections
6. IPC Comparison
7. Punishment
8. Cognizable / Non-Cognizable
9. Bailable / Non-Bailable
10. BNSS Procedure
11. BSA Evidence
12. Digital Evidence
13. Investigation Steps
14. IO Checklist
15. Documents / Witnesses
16. Final Observations

IMPORTANT:

Image లో section number కనిపిస్తే దానిని blindly trust చేయకండి.

Facts ఆధారంగా section applicability verify చేయాలి.

Section number ఖచ్చితంగా తెలియకపోతే guess చేయకండి.
"""


                    result = analyze_image(

                        file_bytes,

                        mime_type,

                        prompt

                    )


                st.markdown("---")

                st.subheader(
                    "📋 Image Legal Analysis"
                )

                st.markdown(result)


                st.download_button(

                    label="📥 Download Report",

                    data=result,

                    file_name="image_legal_analysis.txt",

                    mime="text/plain",

                    key="download_image_report"

                )


        # -------------------------------------------------
        # PDF FILE
        # -------------------------------------------------

        elif file_name.endswith(".pdf"):

            if st.button(
                "📄 Analyze PDF",
                type="primary",
                key="pdf_analysis"
            ):

                with st.spinner(
                    "📄 PDF చదువుతున్నాను..."
                ):

                    pdf_text = extract_pdf_text(
                        file_bytes
                    )


                if not pdf_text.strip():

                    st.error(
                        "❌ PDF లో readable text కనిపించలేదు."
                    )

                    st.info(
                        "Scanned PDF అయితే PDF pages ను images గా upload చేయండి."
                    )

                else:

                    prompt = f"""

క్రింది PDF complaint/document text ను
legal investigation perspective నుండి విశ్లేషించండి.


DOCUMENT TEXT:

{pdf_text}


ఈ headings ఉపయోగించండి:

## 1. Complaint Summary

## 2. Important Facts

## 3. Allegations

## 4. Possible BNS Offences

## 5. BNS Sections

## 6. IPC Comparison

## 7. Punishment

## 8. Cognizable / Non-Cognizable

## 9. Bailable / Non-Bailable

## 10. BNSS Procedure

## 11. BSA Evidence

## 12. Digital Evidence

## 13. Investigation Steps

## 14. IO Checklist

## 15. Documents / Witnesses

## 16. Final Observations


IMPORTANT:

Section numbers guess చేయకండి.

Exact correspondence లేకపోతే
"Exact equivalent కాదు" అని చెప్పండి.
"""


                    with st.spinner(
                        "⚖️ Legal analysis జరుగుతోంది..."
                    ):

                        result = analyze_text(
                            prompt
                        )


                    st.markdown("---")

                    st.subheader(
                        "📋 PDF Legal Analysis"
                    )

                    st.markdown(result)


                    st.download_button(

                        label="📥 Download Report",

                        data=result,

                        file_name="pdf_legal_analysis.txt",

                        mime="text/plain",

                        key="download_pdf_report"

                    )


        # -------------------------------------------------
        # TXT FILE
        # -------------------------------------------------

        elif file_name.endswith(".txt"):

            text_content = extract_text_file(
                file_bytes
            )


            st.text_area(
                "📄 File Content",
                text_content,
                height=300
            )


            if st.button(
                "⚖️ Analyze TXT",
                type="primary",
                key="txt_analysis"
            ):

                prompt = f"""

క్రింది complaint/case text ను
BNS, BNSS, BSA perspective నుండి విశ్లేషించండి.


CASE TEXT:

{text_content}


క్రింది headings ఉపయోగించండి:

## 1. Summary

## 2. Allegations

## 3. Possible BNS Offences

## 4. Relevant BNS Sections

## 5. IPC Comparison

## 6. Punishment

## 7. Cognizable / Non-Cognizable

## 8. Bailable / Non-Bailable

## 9. BNSS Procedure

## 10. BSA Evidence

## 11. Investigation Steps

## 12. IO Checklist

## 13. Digital Evidence

## 14. Final Observations


Section numbers guess చేయకండి.
"""


                with st.spinner(
                    "⚖️ Analysis జరుగుతోంది..."
                ):

                    result = analyze_text(
                        prompt
                    )


                st.markdown("---")

                st.subheader(
                    "📋 TXT Legal Analysis"
                )

                st.markdown(result)


                st.download_button(

                    label="📥 Download Report",

                    data=result,

                    file_name="txt_legal_analysis.txt",

                    mime="text/plain",

                    key="download_txt_report"

                )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "⚖️ BNS, BNSS & BSA Legal & Investigation Assistant"
)

st.caption(
    "AI-generated analysis should be verified with the applicable official legislation and legal authorities."
)
