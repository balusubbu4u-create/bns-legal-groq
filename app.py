import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from docx.shared import Pt
from PIL import Image
import base64
import io


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="BNS Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS, BNSS & BSA లీగల్ & దర్యాప్తు అసిస్టెంట్")

st.caption(
    "భారతీయ క్రిమినల్ చట్టాలు (BNS, BNSS, BSA) "
    "& పాత చట్టాల (IPC, CrPC, IEA) సమగ్ర విశ్లేషణ"
)


# =========================================================
# GROQ API KEY
# =========================================================

if "GROQ_API_KEY" not in st.secrets:
    st.error(
        "❌ Streamlit Secrets లో GROQ_API_KEY కనిపించలేదు. "
        "App Settings → Secrets లో GROQ_API_KEY నమోదు చేయండి."
    )
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=api_key)


# =========================================================
# GET AVAILABLE GROQ MODELS
# =========================================================

@st.cache_data(ttl=3600)
def get_available_groq_models(key):

    try:
        temp_client = Groq(api_key=key)

        models_data = temp_client.models.list().data

        models = []

        for model in models_data:

            model_id = model.id.lower()

            # Audio / speech / guard models వద్దు
            if any(x in model_id for x in [
                "whisper",
                "guard",
                "tts",
                "speech"
            ]):
                continue

            models.append(model.id)

        return sorted(models)

    except Exception:
        return []


available_models = get_available_groq_models(api_key)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ మోడల్ సెట్టింగ్స్")


if available_models:

    preferred_models = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.6-27b",
        "qwen/qwen3.8-27b"
    ]

    sorted_models = []

    for model in preferred_models:

        if model in available_models:
            sorted_models.append(model)

    for model in available_models:

        if model not in sorted_models:
            sorted_models.append(model)

    selected_model = st.sidebar.selectbox(
        "🤖 Groq AI Model:",
        sorted_models,
        index=0
    )

else:

    st.error(
        "❌ Groq models list చేయలేకపోయాము. "
        "GROQ_API_KEYను check చేయండి."
    )

    st.stop()


# =========================================================
# VISION MODEL
# =========================================================

VISION_MODELS = [
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b"
]

available_vision_models = [
    model
    for model in VISION_MODELS
    if model in available_models
]

if available_vision_models:
    vision_model = available_vision_models[0]
else:
    vision_model = None


st.sidebar.markdown("---")

if vision_model:

    st.sidebar.success(
        f"🖼️ Image Model:\n{vision_model}"
    )

else:

    st.sidebar.warning(
        "🖼️ Vision model అందుబాటులో లేదు."
    )


st.sidebar.markdown("---")

st.sidebar.markdown(
    """
### ⚖️ ఈ Appలో

- 🔹 BNS vs IPC
- 🔹 BNSS vs CrPC
- 🔹 BSA vs IEA
- 🔹 FIR Analysis
- 🔹 Investigation Procedure
- 🔹 Digital Evidence
- 🔹 CCTV / CDR
- 🔹 Forensic Evidence
- 🔹 IO Checklist
- 🔹 BSA Section 63
"""
)


# =========================================================
# LEGAL SYSTEM INSTRUCTION
# =========================================================

legal_system_instruction = """

మీరు భారతీయ క్రిమినల్ చట్టాలపై నిపుణుడైన
Legal & Investigation Assistant.

ప్రధానంగా:

BNS - Bharatiya Nyaya Sanhita
BNSS - Bharatiya Nagarik Suraksha Sanhita
BSA - Bharatiya Sakshya Adhiniyam

మరియు అవసరమైనప్పుడు:

IPC
CrPC
Indian Evidence Act

తో పోల్చి విశ్లేషించాలి.

========================================================

ముఖ్యమైన ఖచ్చితత్వ నియమాలు:

1. కేసులో ఉన్న facts ఆధారంగానే section సూచించాలి.

2. ఊహించి section number చెప్పకూడదు.

3. Section numberపై సందేహం ఉంటే
   "ధృవీకరణ అవసరం" అని స్పష్టంగా చెప్పాలి.

4. కొత్త BNS/BNSS/BSA provisions మరియు
   పాత IPC/CrPC/IEA provisions మధ్య
   సరైన comparison ఇవ్వాలి.

5. శిక్ష, జరిమానా, Cognizable,
   Non-Cognizable, Bailable,
   Non-Bailable వివరాలను సాధ్యమైనంత
   స్పష్టంగా ఇవ్వాలి.

========================================================

### 1. CASE FACTS SUMMARY

ముందుగా:

- సంఘటన
- బాధితుడు
- నిందితుడి పాత్ర
- సంఘటన స్థలం
- సంఘటన సమయం
- గాయాలు / నష్టం
- అందుబాటులో ఉన్న ఆధారాలు

సంక్షిప్తంగా ఇవ్వాలి.

========================================================

### 2. వర్తించే సెక్షన్లు

టేబుల్ రూపంలో:

| నేరం | BNS | IPC | శిక్ష | Cognizable | Bailable |

కేసు factsకు వర్తించని sections పెట్టకూడదు.

========================================================

### 3. దర్యాప్తు విధానం

IO చేయాల్సిన చర్యలను క్రమంగా వివరించాలి:

1. FIR / information
2. Scene visit
3. Scene preservation
4. Photography
5. Videography
6. Witness identification
7. Statements
8. Search
9. Seizure
10. CCTV collection
11. CDR / technical evidence
12. Mobile / digital evidence
13. Medical examination
14. Forensic examination
15. Arrest / notice decision
16. Case diary
17. Final report / charge sheet

సంబంధిత BNSS provisions ఇవ్వాలి.

========================================================

### 4. ARREST / NOTICE

అరెస్ట్ అవసరమా?

Notice అవసరమా?

BNSS Section 35 వర్తిస్తుందా?

అరెస్ట్‌కు కారణాలు ఏమిటి?

24 గంటలలో Magistrate ముందు హాజరు,
remand మరియు custody provisions
స్పష్టంగా వివరించాలి.

========================================================

### 5. SEARCH & SEIZURE

సంబంధిత BNSS provisions ఆధారంగా:

- Search
- Seizure
- Panch witnesses
- Mahazar
- Audio / Video recording
- Chain of custody

వివరించాలి.

========================================================

### 6. DIGITAL / ELECTRONIC EVIDENCE

కేసులో digital evidence ఉంటే:

- CCTV
- Mobile phone
- Call records
- CDR
- WhatsApp / messages
- Photos
- Videos
- Email
- Computer
- GPS / location data

గుర్తించాలి.

BSA Section 63 certificate అవసరమా,
ఎప్పుడు అవసరం,
ఎలాంటి electronic recordకు వర్తిస్తుంది
అనే విషయాలను స్పష్టంగా వివరించాలి.

========================================================

### 7. FORENSIC EVIDENCE

అవసరమైతే:

- Fingerprints
- DNA
- Blood
- Biological samples
- Weapon
- Clothes
- Digital forensic
- Mobile forensic
- CCTV forensic

సూచించాలి.

========================================================

### 8. IO ACTION CHECKLIST

తప్పనిసరిగా:

[ ] FIR / complaint verification
[ ] Scene visit
[ ] Scene photographs
[ ] Scene videography
[ ] Witness statements
[ ] Search
[ ] Seizure
[ ] CCTV
[ ] CDR
[ ] Mobile data
[ ] Digital evidence
[ ] Forensic examination
[ ] Medical examination
[ ] Arrest / notice decision
[ ] Case diary
[ ] Final report / charge sheet

========================================================

### 9. ఇంకా సేకరించాల్సిన ఆధారాలు

ప్రస్తుత complaintలో లేని కానీ
దర్యాప్తుకు అవసరమైన evidenceను
ప్రత్యేకంగా సూచించాలి.

========================================================

### 10. LEGAL CAUTION

ప్రస్తుత facts ఆధారంగా మాత్రమే analysis చేయాలి.

తుది legal conclusion ఇవ్వకుండా,
అవసరమైన చోట verification సూచించాలి.

చివరలో తప్పనిసరిగా:

"గమనిక: ఇది ప్రాథమిక సమాచారం మరియు
దర్యాప్తు మార్గదర్శకత్వం కోసం మాత్రమే;
తుది చట్టపరమైన నిర్ణయాల కోసం
న్యాయ నిపుణులను సంప్రదించాలి."

అని రాయాలి.
"""


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    pages_text = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text)


# =========================================================
# TXT EXTRACTION
# =========================================================

def extract_txt_text(uploaded_file):

    return uploaded_file.getvalue().decode(
        "utf-8",
        errors="ignore"
    )


# =========================================================
# DOCX EXTRACTION
# =========================================================

def extract_docx_text(uploaded_file):

    document = Document(uploaded_file)

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():

            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


# =========================================================
# IMAGE BASE64
# =========================================================

def encode_image(uploaded_file):

    image_bytes = uploaded_file.getvalue()

    return base64.b64encode(
        image_bytes
    ).decode("utf-8")


# =========================================================
# CREATE DOCX REPORT
# =========================================================

def create_docx_report(report_text):

    document = Document()

    document.add_heading(
        "BNS, BNSS & BSA దర్యాప్తు నివేదిక",
        level=1
    )

    for line in report_text.split("\n"):

        paragraph = document.add_paragraph(
            line
        )

        for run in paragraph.runs:

            run.font.size = Pt(11)

    buffer = io.BytesIO()

    document.save(buffer)

    buffer.seek(0)

    return buffer


# =========================================================
# TABS
# =========================================================

tab1, tab2 = st.tabs(
    [
        "📝 టెక్స్ట్ వివరాలు",
        "📁 PDF / Word / Photo Upload"
    ]
)


case_text = ""

image_base64 = None
image_mime = None


# =========================================================
# TEXT TAB
# =========================================================

with tab1:

    text_input = st.text_area(
        "ఫిర్యాదు / FIR వివరాలు ఇక్కడ నమోదు చేయండి:",
        height=220,
        placeholder=(
            "ఉదాహరణ: అర్ధరాత్రి ఇంట్లోకి అక్రమంగా "
            "ప్రవేశించి బంగారు నగలు, నగదు దోచుకెళ్లారు..."
        )
    )

    if text_input.strip():

        case_text = text_input


# =========================================================
# FILE TAB
# =========================================================

with tab2:

    uploaded_file = st.file_uploader(
        "📂 FIR / Complaint / Document / Photo Upload చేయండి",
        type=[
            "pdf",
            "txt",
            "docx",
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file:

        file_name = uploaded_file.name.lower()

        st.success(
            f"✅ {uploaded_file.name} upload అయింది."
        )


        # =================================================
        # JPG / JPEG / PNG
        # =================================================

        if file_name.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            try:

                image = Image.open(
                    uploaded_file
                )

                st.image(
                    image,
                    caption=uploaded_file.name,
                    use_container_width=True
                )

                image_base64 = encode_image(
                    uploaded_file
                )

                if file_name.endswith(".png"):

                    image_mime = "image/png"

                else:

                    image_mime = "image/jpeg"

                if vision_model:

                    st.success(
                        f"🖼️ Image analysis ready: "
                        f"{vision_model}"
                    )

                else:

                    st.warning(
                        "⚠️ Vision model అందుబాటులో లేదు."
                    )

            except Exception as e:

                st.error(
                    f"Image చదవడంలో error: {e}"
                )


        # =================================================
        # PDF
        # =================================================

        elif file_name.endswith(".pdf"):

            try:

                case_text = extract_pdf_text(
                    uploaded_file
                )

                if case_text.strip():

                    st.success(
                        "✅ PDF text extract అయింది."
                    )

                    with st.expander(
                        "📄 PDF Text చూడండి"
                    ):

                        st.text(
                            case_text[:8000]
                        )

                else:

                    st.warning(
                        "⚠️ ఈ PDF scanned/image PDF "
                        "లా కనిపిస్తోంది. "
                        "అలాంటి PDFను JPG/PNGగా "
                        "upload చేయండి."
                    )

            except Exception as e:

                st.error(
                    f"PDF error: {e}"
                )


        # =================================================
        # TXT
        # =================================================

        elif file_name.endswith(".txt"):

            try:

                case_text = extract_txt_text(
                    uploaded_file
                )

                st.success(
                    "✅ TXT file చదవబడింది."
                )

            except Exception as e:

                st.error(
                    f"TXT error: {e}"
                )


        # =================================================
        # DOCX
        # =================================================

        elif file_name.endswith(".docx"):

            try:

                case_text = extract_docx_text(
                    uploaded_file
                )

                st.success(
                    "✅ Word document చదవబడింది."
                )

                with st.expander(
                    "📘 Word Text చూడండి"
                ):

                    st.text(
                        case_text[:8000]
                    )

            except Exception as e:

                st.error(
                    f"DOCX error: {e}"
                )


# =========================================================
# ANALYSIS BUTTON
# =========================================================

if st.button(
    "🔍 కేస్ విశ్లేషించి దర్యాప్తు నివేదిక రూపొందించండి",
    type="primary",
    use_container_width=True
):

    result = ""


    # =====================================================
    # IMAGE ANALYSIS
    # =====================================================

    if image_base64:

        if not vision_model:

            st.error(
                "❌ Image analysis కోసం "
                "Vision model అందుబాటులో లేదు."
            )

            st.stop()


        with st.spinner(
            "🖼️ Image చదివి "
            "Legal Analysis తయారు చేస్తోంది..."
        ):

            try:

                response = client.chat.completions.create(

                    model=vision_model,

                    temperature=0.1,

                    max_completion_tokens=7000,

                    messages=[

                        {
                            "role": "system",
                            "content":
                                legal_system_instruction
                        },

                        {
                            "role": "user",

                            "content": [

                                {
                                    "type": "text",

                                    "text":
                                        """
ఈ uploaded imageలో ఉన్న
FIR / Complaint / documentను
జాగ్రత్తగా చదవండి.

Imageలో స్పష్టంగా కనిపించే facts
మాత్రమే ఉపయోగించండి.

చదవలేని పదాలను ఊహించవద్దు.

తర్వాత Legal System Instructions
ప్రకారం BNS / BNSS / BSA
సమగ్ర దర్యాప్తు నివేదిక తయారు చేయండి.
"""
                                },

                                {
                                    "type": "image_url",

                                    "image_url": {
                                        "url":
                                            f"data:{image_mime};base64,{image_base64}"
                                    }
                                }

                            ]
                        }

                    ]
                )

                result = (
                    response
                    .choices[0]
                    .message
                    .content
                )

            except Exception as e:

                st.error(
                    f"Image analysis error: {e}"
                )


    # =====================================================
    # TEXT / PDF / DOCX ANALYSIS
    # =====================================================

    elif case_text.strip():

        # పెద్ద complaint అయితే beginning + ending
        # రెండూ పంపుతాం
        if len(case_text) > 12000:

            trimmed_case_text = (
                case_text[:9000]
                + "\n\n"
                + "[మధ్యలోని text పరిమితం చేయబడింది]"
                + "\n\n"
                + case_text[-3000:]
            )

        else:

            trimmed_case_text = case_text


        with st.spinner(
            f"🤖 {selected_model} ద్వారా "
            "Legal Analysis జరుగుతోంది..."
        ):

            try:

                response = client.chat.completions.create(

                    model=selected_model,

                    temperature=0.1,

                    max_completion_tokens=7000,

                    messages=[

                        {
                            "role": "system",
                            "content":
                                legal_system_instruction
                        },

                        {
                            "role": "user",

                            "content":
                                f"""
క్రింది FIR / Complaint / Case Details
ఆధారంగా పూర్తి Legal & Investigation
Report తయారు చేయండి.

----------------------------

{trimmed_case_text}

----------------------------

పైన ఇచ్చిన Legal System Instructions
ప్రకారం report తయారు చేయండి.
"""
                        }

                    ]
                )

                result = (
                    response
                    .choices[0]
                    .message
                    .content
                )

            except Exception as e:

                st.error(
                    f"Analysis error: {e}"
                )


    else:

        st.warning(
            "⚠️ Complaint text లేదా "
            "PDF / DOCX / JPG / PNG file upload చేయండి."
        )


    # =====================================================
    # DISPLAY RESULT
    # =====================================================

    if result:

        st.markdown("---")

        st.markdown(
            "## 📋 సమగ్ర దర్యాప్తు & "
            "చట్టపరమైన విశ్లేషణ నివేదిక"
        )

        st.markdown(result)


        # =================================================
        # TXT DOWNLOAD
        # =================================================

        st.download_button(
            label="📥 TXT Report Download",

            data=result,

            file_name=
                "BNS_Investigation_Report.txt",

            mime="text/plain",

            use_container_width=True
        )


        # =================================================
        # DOCX DOWNLOAD
        # =================================================

        docx_report = create_docx_report(
            result
        )

        st.download_button(
            label="📘 Word Report Download",

            data=docx_report,

            file_name=
                "BNS_Investigation_Report.docx",

            mime=
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

            use_container_width=True
    )
