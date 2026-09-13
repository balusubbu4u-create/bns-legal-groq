import streamlit as st
from groq import Groq
from pypdf import PdfReader
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
    "BNS / IPC • BNSS / CrPC • BSA / IEA "
    "— చట్టపరమైన విశ్లేషణ మరియు దర్యాప్తు సహాయక సాధనం"
)

# =========================================================
# API KEY
# =========================================================

if "GROQ_API_KEY" not in st.secrets:
    st.error(
        "Streamlit Secrets లో GROQ_API_KEY కనిపించలేదు. "
        "App Settings → Secrets లో GROQ_API_KEY నమోదు చేయండి."
    )
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]

client = Groq(api_key=api_key)

# =========================================================
# MODEL SETTINGS
# =========================================================

st.sidebar.header("⚙️ AI Model")

# Text + image analysis కోసం current vision-capable model
DEFAULT_MODEL = "qwen/qwen3.6-27b"

selected_model = "qwen/qwen3.6-27b"

st.sidebar.success(
    f"✅ Active Model: {selected_model}"
)
    index=0
)

st.sidebar.info(
    "📌 Screenshot / JPG / PNG analysis కోసం "
    "vision-capable model అవసరం."
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
### 📚 Analysis Areas

- BNS ↔ IPC
- BNSS ↔ CrPC
- BSA ↔ IEA
- Cognizable / Non-Cognizable
- Bailable / Non-Bailable
- Punishment
- Investigation SOP
- Digital Evidence
- IO Checklist
"""
)

# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader("📂 Complaint / Evidence Upload")

uploaded_file = st.file_uploader(
    "PDF / TXT / JPG / JPEG / PNG / WEBP ఫైల్ ఎంచుకోండి",
    type=[
        "pdf",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
    help="Complaint PDF, text file లేదా screenshot/image upload చేయవచ్చు."
)

case_text = ""
image_data = None
image_mime = None

# =========================================================
# TEXT INPUT
# =========================================================

tab1, tab2 = st.tabs(
    ["📝 Text Details", "📁 File / Screenshot"]
)

with tab1:

    text_input = st.text_area(
        "ఫిర్యాదు / కేసు వివరాలు:",
        height=220,
        placeholder=(
            "ఉదాహరణ:\n"
            "అర్ధరాత్రి ఇంట్లోకి ప్రవేశించి వస్తువులు తీసుకెళ్లారు. "
            "బాధితుడిని కొట్టారు మరియు బెదిరించారు..."
        )
    )

    if text_input.strip():
        case_text = text_input.strip()


# =========================================================
# FILE PROCESSING
# =========================================================

with tab2:

    if uploaded_file:

        file_name = uploaded_file.name.lower()
        file_bytes = uploaded_file.getvalue()

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        if file_name.endswith(".pdf"):

            try:

                reader = PdfReader(
                    io.BytesIO(file_bytes)
                )

                extracted_pages = []

                for page in reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        extracted_pages.append(page_text)

                case_text = "\n\n".join(extracted_pages)

                if case_text.strip():

                    st.success(
                        f"✅ PDF చదవబడింది: {uploaded_file.name}"
                    )

                    with st.expander("📄 Extracted PDF Text"):
                        st.text(case_text[:10000])

                else:

                    st.warning(
                        "⚠️ ఈ PDFలో selectable text కనిపించలేదు. "
                        "ఇది scanned PDF అయితే screenshot/imageగా upload చేయండి."
                    )

            except Exception as e:

                st.error(
                    f"PDF చదవడంలో సమస్య: {e}"
                )

        # -------------------------------------------------
        # TXT
        # -------------------------------------------------

        elif file_name.endswith(".txt"):

            try:

                case_text = file_bytes.decode(
                    "utf-8",
                    errors="ignore"
                )

                st.success(
                    f"✅ Text file చదవబడింది: {uploaded_file.name}"
                )

                with st.expander("📝 Text Preview"):
                    st.text(case_text[:10000])

            except Exception as e:

                st.error(
                    f"TXT చదవడంలో సమస్య: {e}"
                )

        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        elif file_name.endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):

            image_data = base64.b64encode(
                file_bytes
            ).decode("utf-8")

            if file_name.endswith(".png"):
                image_mime = "image/png"

            elif file_name.endswith(".webp"):
                image_mime = "image/webp"

            else:
                image_mime = "image/jpeg"

            st.success(
                f"✅ Image loaded: {uploaded_file.name}"
            )

            st.image(
                file_bytes,
                caption="Uploaded Complaint / Screenshot",
                use_container_width=True
            )


# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

LEGAL_SYSTEM_PROMPT = r"""
మీరు భారతదేశ క్రిమినల్ చట్టాలపై సహాయక Legal & Investigation
Analysis Assistant.

మీరు BNS 2023, BNSS 2023, BSA 2023 మరియు పాత IPC 1860,
CrPC 1973, Indian Evidence Act 1872 మధ్య సంబంధాన్ని
చాలా జాగ్రత్తగా విశ్లేషించాలి.

============================================================
🚨 ABSOLUTE LEGAL ACCURACY RULES
============================================================

1. SECTION NUMBER ఎప్పుడూ ఊహించకూడదు.

2. Complaint factsలో లేని నేరాన్ని జోడించకూడదు.

3. BNS ↔ IPC correspondenceను section-number similarity
   ఆధారంగా తయారు చేయకూడదు.

4. Direct corresponding provision ఖచ్చితంగా తెలియకపోతే:

   "Direct correspondence not established —
    legal verification required"

   అని రాయాలి.

5. ఒక BNS sectionకు IPCలో direct equivalent లేకపోతే
   false equivalent ఇవ్వకూడదు.

6. ఒక IPC sectionకు BNSలో direct equivalent లేకపోతే
   false equivalent ఇవ్వకూడదు.

7. "No direct corresponding provision" అనేది valid answer.

8. Punishment, fine, cognizable/non-cognizable,
   bailable/non-bailable విషయాలను కూడా ఊహించకూడదు.

9. Investigation procedure sectionను offence sectionతో
   కలపకూడదు.

10. Arrest section, remand section, charge-sheet section,
    evidence section వేర్వేరు విషయాలు.

11. 60/90 days విషయాన్ని automatic "charge-sheet deadline"
    అని చెప్పకూడదు. అది statutory custody/default-bail
    frameworkతో సంబంధం ఉన్న విషయం కావచ్చు.

12. BNSS 193 మరియు BNSS 187 వంటి procedural provisionsను
    వేర్వేరుగా analyse చేయాలి.

13. BSA Section 63 electronic evidence విషయాన్ని
    fact-specificగా explain చేయాలి.

14. "BSA 63 = every electronic evidence automatically
    needs one identical certificate" అని blanket statement
    ఇవ్వకూడదు.

15. Legal uncertainty ఉంటే:

    ⚠️ LEGAL VERIFICATION REQUIRED

    అని స్పష్టంగా చూపించాలి.

============================================================
📚 CORRESPONDENCE RULE
============================================================

ప్రతి offenceకు ఈ format ఉపయోగించాలి:

OFFENCE
-------
Facts:

Possible BNS Section:
Possible IPC Section:

Direct Correspondence:
YES / NO / REQUIRES VERIFICATION

BNS Provision:
...

IPC Provision:
...

Punishment:
...

Cognizable:
...

Bailable:
...

Verification Status:
HIGH / MEDIUM / REQUIRES LEGAL VERIFICATION


============================================================
⚠️ IMPORTANT
============================================================

AI memory ద్వారా IPC → BNS mapping తయారు చేయకూడదు.

Known correspondence లేకపోతే guess చేయకూడదు.

ఉదాహరణకు:

❌ "IPC 454 కాబట్టి BNS 305"

అని number pattern ఆధారంగా నిర్ణయించకూడదు.

Facts మరియు statutory offence elements ఆధారంగా మాత్రమే
correspondence analyse చేయాలి.

============================================================
📋 REPORT FORMAT
============================================================

### 1. CASE FACTS

Complaintలో నిజంగా ఉన్న facts మాత్రమే.

### 2. POSSIBLE OFFENCES

ప్రతి offence విడిగా.

### 3. BNS ↔ IPC COMPARISON

Table format:

| Offence | BNS | IPC | Direct Correspondence | Verification |
|---|---|---|---|---|

### 4. PUNISHMENT & CLASSIFICATION

| Section | Punishment | Cognizable | Bailable |
|---|---|---|---|

### 5. BNSS INVESTIGATION PROCEDURE

FIR
↓
Scene preservation
↓
Witnesses
↓
Evidence
↓
Search / seizure
↓
Arrest if legally necessary
↓
Remand where applicable
↓
Forensic evidence
↓
Electronic evidence
↓
Police report / charge-sheet

ప్రతి stepకు సరైన BNSS provisionను మాత్రమే ఇవ్వాలి.

### 6. DIGITAL / ELECTRONIC EVIDENCE

CCTV
Mobile
CDR
GPS
WhatsApp
Photos
Videos
Computer records

వాటికి BSA applicabilityను explain చేయాలి.

### 7. IO CHECKLIST

[ ] FIR
[ ] Scene inspection
[ ] Photographs / video
[ ] Witness statements
[ ] Medical evidence where relevant
[ ] Search / seizure
[ ] Seizure mahazar
[ ] CCTV preservation
[ ] Digital evidence
[ ] FSL / forensic examination where applicable
[ ] Accused examination / arrest where legally necessary
[ ] Case diary
[ ] Final police report

### 8. IMPORTANT LEGAL WARNINGS

ఏ section / mapping / procedureపై uncertainty ఉందో
విడిగా చూపించాలి.

చివరగా:

"గమనిక: ఇది ప్రాథమిక legal information మరియు
investigation assistance కోసం మాత్రమే. తుది చట్టపరమైన
నిర్ణయం కోసం అధికారిక చట్ట పాఠ్యం, సంబంధిత Schedule/
Corresponding Table మరియు అవసరమైతే న్యాయ నిపుణుల
సలహాను పరిశీలించాలి."

============================================================
"""

# =========================================================
# IMAGE PROMPT
# =========================================================

IMAGE_INSTRUCTION = """
ఈ image/screenshotలో ఉన్న complaint లేదా document textను
ముందుగా జాగ్రత్తగా చదవండి.

1. కనిపించే textను తప్పుగా ఊహించకండి.
2. చదవలేని పదాలను [ILLEGIBLE]గా గుర్తించండి.
3. ముందుగా facts extract చేయండి.
4. తరువాత legal analysis చేయండి.
5. Imageలో లేని factsను కల్పించకండి.
"""


# =========================================================
# ANALYSIS FUNCTION
# =========================================================

def analyse_text(text):

    response = client.chat.completions.create(

        model=selected_model,

        temperature=0.0,

        max_completion_tokens=8000,

        messages=[
            {
                "role": "system",
                "content": LEGAL_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    "క్రింది complaint factsను మాత్రమే ఆధారంగా "
                    "legal analysis చేయండి.\n\n"
                    + text[:12000]
                )
            }
        ]
    )

    return response.choices[0].message.content


def analyse_image(image_b64, mime_type):

    response = client.chat.completions.create(

        model=selected_model,

        temperature=0.0,

        max_completion_tokens=8000,

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
                        "text": IMAGE_INSTRUCTION
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{image_b64}"
                            )
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content


# =========================================================
# ANALYSE BUTTON
# =========================================================

st.markdown("---")

if st.button(
    "🔍 కేస్ విశ్లేషించి దర్యాప్తు నివేదిక రూపొందించండి",
    type="primary",
    use_container_width=True
):

    if not case_text.strip() and not image_data:

        st.warning(
            "దయచేసి complaint text లేదా PDF/TXT/image upload చేయండి."
        )

        st.stop()

    try:

        with st.spinner(
            f"⚖️ {selected_model} ద్వారా analysis జరుగుతోంది..."
        ):

            # ---------------------------------------------
            # IMAGE
            # ---------------------------------------------

            if image_data:

                result = analyse_image(
                    image_data,
                    image_mime
                )

            # ---------------------------------------------
            # TEXT / PDF / TXT
            # ---------------------------------------------

            else:

                result = analyse_text(
                    case_text
                )

        # =================================================
        # RESULT
        # =================================================

        st.markdown("---")

        st.header(
            "📋 సమగ్ర దర్యాప్తు & చట్టపరమైన విశ్లేషణ"
        )

        st.markdown(result)

        # =================================================
        # DOWNLOAD
        # =================================================

        st.download_button(

            label="📥 నివేదికను TXTగా Download చేయండి",

            data=result,

            file_name="BNS_Legal_Investigation_Report.txt",

            mime="text/plain",

            use_container_width=True
        )

    except Exception as e:

        st.error(
            f"❌ Analysisలో error వచ్చింది:\n\n{e}"
        )

        st.info(
            "Model పేరు లేదా Groq API availabilityను "
            "చెక్ చేయండి."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "⚠️ Legal Disclaimer: ఈ application ప్రాథమిక legal "
    "information మరియు investigation assistance కోసం మాత్రమే. "
    "తుది నిర్ణయం కోసం అధికారిక statute, schedules, "
    "corresponding tables మరియు న్యాయ నిపుణుల సలహాను పరిశీలించాలి."
)
