import streamlit as st
from groq import Groq
from pypdf import PdfReader
import io
import base64
import fitz


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

మీరు భారతదేశ క్రిమినల్ లా గురించి విశ్లేషించే
Legal & Investigation Assistant.

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

• Facts ఆధారంగా offence elements ను గుర్తించాలి.

• BNS section ను IPC section తో compare చేసేటప్పుడు
  exact correspondence లేకపోతే
  "Exact equivalent కాదు" అని చెప్పాలి.

• ఒక offence పేరు చూసి section number guess చేయకూడదు.

• Punishment, Cognizable / Non-Cognizable,
  Bailable / Non-Bailable వంటి విషయాలు చెప్పేటప్పుడు
  applicability ని జాగ్రత్తగా పరిశీలించాలి.

• BNSS procedure sections ను
  BNS offence sections తో కలపకూడదు.

• BSA evidence sections ను
  BNS offence sections తో కలపకూడదు.

• Section ఖచ్చితంగా తెలియకపోతే
  తప్పు section చెప్పడం కంటే
  verification అవసరం అని చెప్పాలి.


==============================
ELECTRONIC EVIDENCE
==============================

Electronic evidence విషయంలో:

• CCTV
• Mobile Phone
• Computer
• DVR / NVR
• Call Records
• WhatsApp Chats
• Emails
• Digital Photographs
• Audio / Video Recordings
• GPS / Location Data

వంటి evidence గురించి చెప్పేటప్పుడు
BSA provisions మరియు applicable certificate
requirements ను facts ఆధారంగా వివరించాలి.


==============================
LANGUAGE
==============================

User Telugu లో అడిగితే Telugu లో సమాధానం ఇవ్వాలి.

Legal Section names English లో ఉంచవచ్చు.

అవసరమైన చోట English + Telugu explanation ఇవ్వాలి.

Technical legal terminology కి
simple Telugu meaning ఇవ్వాలి.


==============================
DISCLAIMER
==============================

ఇది legal research / investigation assistance కోసం మాత్రమే.

Final legal decision కోసం official legislation,
government notifications,
competent authority instructions మరియు
qualified legal professional verification అవసరం.
"""


# =========================================================
# PDF TEXT EXTRACTION
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


        return text.strip()


    except Exception:

        return ""


# =========================================================
# TXT FILE EXTRACTION
# =========================================================

def extract_text_file(file_bytes):

    try:

        return file_bytes.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception as e:

        return f"Text file చదవడంలో error: {str(e)}"


# =========================================================
# PDF TO IMAGES
# =========================================================

def pdf_to_images(
    file_bytes,
    max_pages=20
):

    try:

        pdf_document = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )

        images = []

        total_pages = min(
            len(pdf_document),
            max_pages
        )


        for page_number in range(total_pages):

            page = pdf_document.load_page(
                page_number
            )


            # High resolution for OCR

            matrix = fitz.Matrix(
                2,
                2
            )


            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )


            image_bytes = pix.tobytes(
                "png"
            )


            images.append(
                image_bytes
            )


        pdf_document.close()


        return images


    except Exception as e:

        st.error(
            f"PDF conversion error: {str(e)}"
        )

        return []


# =========================================================
# OCR - IMAGE TO TEXT
# =========================================================

def extract_text_from_image(
    image_bytes,
    mime_type
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

                    "content": """

You are a high accuracy OCR assistant.

Your ONLY job is to read and extract
all visible text from the image.

IMPORTANT RULES:

1. Telugu handwritten text must be read carefully.

2. Preserve original words as much as possible.

3. Do NOT summarize.

4. Do NOT perform legal analysis.

5. Do NOT guess missing text.

6. If a word is unclear write:

[UNCLEAR]

7. Preserve paragraphs and line structure.

8. Return ONLY extracted text.

9. Do not add explanations.

"""
                },


                {
                    "role": "user",

                    "content": [


                        {
                            "type": "text",

                            "text": """

Read this uploaded image carefully.

It may contain Telugu handwritten complaint,
case facts or official documents.

Extract all visible text.

Do NOT summarize.

Do NOT analyze.

Do NOT identify legal sections.

Return ONLY the OCR text.

"""
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


            temperature=0,


            max_tokens=6000

        )


        return response.choices[0].message.content


    except Exception as e:

        return f"OCR Error: {str(e)}"


# =========================================================
# TEXT LEGAL ANALYSIS
# =========================================================

def analyze_text(
    user_prompt
):

    try:

        response = client.chat.completions.create(

            model=selected_model,


            messages=[


                {
                    "role": "system",

                    "content":
                    LEGAL_SYSTEM_PROMPT
                },


                {
                    "role": "user",

                    "content":
                    user_prompt
                }

            ],


            temperature=0.1,


            max_tokens=6000

        )


        return response.choices[0].message.content


    except Exception as e:

        return f"""

❌ AI Analysis Error

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
# TAB 1 - TEXT ANALYSIS
# =========================================================

with tab1:


    st.subheader(
        "📝 కేసు వివరాలు నమోదు చేయండి"
    )


    case_text = st.text_area(

        "Case / Complaint Details",

        height=350,


        placeholder=(

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

క్రింది కేసు వివరాలను పూర్తిగా
BNS, BNSS మరియు BSA ప్రకారం విశ్లేషించండి.

CASE DETAILS:

{case_text}


ఈ headings ఉపయోగించండి:

## 1. సంఘటన సారాంశం

## 2. ప్రధాన Allegations

## 3. ముఖ్యమైన Facts

## 4. Possible BNS Offences

## 5. BNS Section-wise Analysis

## 6. IPC Comparison

## 7. Punishment

## 8. Cognizable / Non-Cognizable

## 9. Bailable / Non-Bailable

## 10. BNSS Procedure

## 11. BSA Evidence

## 12. Digital Evidence

## 13. Investigation Steps

## 14. IO Checklist

## 15. Documents / Witnesses Required

## 16. Final Legal Observations


IMPORTANT:

Section numbers guess చేయకండి.

Facts సరిపోకపోతే
additional facts required అని చెప్పండి.

IPC equivalent exact కాకపోతే
Exact equivalent కాదు అని చెప్పండి.

"""


                result = analyze_text(
                    prompt
                )


            st.markdown("---")


            st.subheader(
                "📋 Legal Analysis Result"
            )


            st.markdown(
                result
            )


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


    # =====================================================
    # FILE UPLOAD
    # =====================================================

    if uploaded_file is not None:


        file_bytes = uploaded_file.read()


        file_name = uploaded_file.name.lower()


        st.success(
            f"✅ File uploaded: {uploaded_file.name}"
        )


        # =================================================
        # IMAGE FILE
        # =================================================

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


            # ---------------------------------------------

            # IMAGE OCR

            # ---------------------------------------------

            if st.button(

                "🔎 Read Image / OCR",

                type="primary",

                key="image_ocr"

            ):


                with st.spinner(
                    "📷 Image నుండి Telugu text చదువుతున్నాను..."
                ):


                    mime_type = uploaded_file.type


                    ocr_text = extract_text_from_image(

                        file_bytes,

                        mime_type

                    )


                st.session_state[
                    "image_ocr_result"
                ] = ocr_text


            # ---------------------------------------------

            # SHOW OCR TEXT

            # ---------------------------------------------

            if "image_ocr_result" in st.session_state:


                st.subheader(
                    "📝 Extracted OCR Text"
                )


                edited_text = st.text_area(

                    "OCR Text ని చదివి అవసరమైతే సరిచేయండి",

                    value=st.session_state[
                        "image_ocr_result"
                    ],

                    height=450,

                    key="image_ocr_editor"

                )


                st.session_state[
                    "image_ocr_result"
                ] = edited_text


                # -----------------------------------------

                # LEGAL ANALYSIS

                # -----------------------------------------

                if st.button(

                    "⚖️ Analyze Extracted Text",

                    type="primary",

                    key="analyze_image_text"

                ):


                    with st.spinner(
                        "⚖️ Legal analysis జరుగుతోంది..."
                    ):


                        prompt = f"""

క్రింది OCR ద్వారా తీసుకున్న
complaint/document text ను

BNS, BNSS మరియు BSA ప్రకారం
legal investigation perspective నుండి
విశ్లేషించండి.


IMPORTANT:

OCR వల్ల spelling mistakes ఉండవచ్చు.

అస్పష్టమైన facts ఆధారంగా
section numbers guess చేయకండి.

Facts స్పష్టంగా లేకపోతే
additional facts required అని చెప్పండి.


CASE TEXT:

{st.session_state["image_ocr_result"]}


ఈ headings ఉపయోగించండి:


## 1. సంఘటన సారాంశం

## 2. ప్రధాన Allegations

## 3. ముఖ్యమైన Facts

## 4. Possible BNS Offences

## 5. BNS Section-wise Analysis

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

## 16. Final Legal Observations

"""


                        result = analyze_text(
                            prompt
                        )


                    st.markdown("---")


                    st.subheader(
                        "📋 Legal Analysis Result"
                    )


                    st.markdown(
                        result
                    )


                    st.download_button(

                        label="📥 Download Report",

                        data=result,

                        file_name="image_legal_analysis.txt",

                        mime="text/plain",

                        key="download_image_report"

                    )


        # =================================================
        # PDF FILE
        # =================================================

        elif file_name.endswith(".pdf"):


            st.info(

                "📄 PDF లో text ఉంటే direct గా చదువుతుంది. "
                "Scanned PDF అయితే OCR ద్వారా చదువుతుంది."

            )


            if st.button(

                "📄 Read PDF",

                type="primary",

                key="read_pdf"

            ):


                with st.spinner(
                    "📄 PDF చదువుతున్నాను..."
                ):


                    pdf_text = extract_pdf_text(
                        file_bytes
                    )


                # -----------------------------------------

                # NORMAL TEXT PDF

                # -----------------------------------------

                if pdf_text and len(pdf_text) > 30:


                    st.success(
                        "✅ PDF లో readable text కనుగొనబడింది."
                    )


                    st.session_state[
                        "pdf_ocr_result"
                    ] = pdf_text


                # -----------------------------------------

                # SCANNED PDF

                # -----------------------------------------

                else:


                    st.info(
                        "📷 ఇది scanned/image PDF లాగా ఉంది. "
                        "OCR చేస్తున్నాను..."
                    )


                    pdf_images = pdf_to_images(
                        file_bytes
                    )


                    if not pdf_images:


                        st.error(
                            "❌ PDF pages ను images గా మార్చలేకపోయాము."
                        )


                    else:


                        all_text = ""


                        for i, image_bytes in enumerate(
                            pdf_images
                        ):


                            with st.spinner(

                                f"📷 Page {i + 1} OCR జరుగుతోంది..."

                            ):


                                page_text = extract_text_from_image(

                                    image_bytes,

                                    "image/png"

                                )


                            all_text += (
                                f"\n\n===== PAGE {i + 1} =====\n\n"
                            )


                            all_text += page_text


                        st.session_state[
                            "pdf_ocr_result"
                        ] = all_text


            # ---------------------------------------------

            # SHOW PDF TEXT

            # ---------------------------------------------

            if "pdf_ocr_result" in st.session_state:


                st.subheader(
                    "📝 PDF Extracted Text"
                )


                edited_pdf_text = st.text_area(

                    "OCR / Extracted Text",

                    value=st.session_state[
                        "pdf_ocr_result"
                    ],

                    height=500,

                    key="pdf_text_editor"

                )


                st.session_state[
                    "pdf_ocr_result"
                ] = edited_pdf_text


                # -----------------------------------------

                # ANALYZE PDF TEXT

                # -----------------------------------------

                if st.button(

                    "⚖️ Analyze PDF Text",

                    type="primary",

                    key="analyze_pdf_text"

                ):


                    with st.spinner(
                        "⚖️ Legal analysis జరుగుతోంది..."
                    ):


                        prompt = f"""

క్రింది PDF complaint/document text ను

BNS, BNSS మరియు BSA ప్రకారం
legal investigation perspective నుండి
విశ్లేషించండి.


DOCUMENT TEXT:

{st.session_state["pdf_ocr_result"]}


IMPORTANT:

OCR వల్ల spelling mistakes ఉండవచ్చు.

Facts స్పష్టంగా లేకపోతే
assumptions చేయకండి.

Section numbers guess చేయకండి.

Exact IPC equivalent లేకపోతే
"Exact equivalent కాదు" అని చెప్పండి.


ఈ headings ఉపయోగించండి:


## 1. Complaint Summary

## 2. Important Facts

## 3. Allegations

## 4. Possible BNS Offences

## 5. BNS Section-wise Analysis

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

## 16. Final Legal Observations

"""


                        result = analyze_text(
                            prompt
                        )


                    st.markdown("---")


                    st.subheader(
                        "📋 PDF Legal Analysis"
                    )


                    st.markdown(
                        result
                    )


                    st.download_button(

                        label="📥 Download Report",

                        data=result,

                        file_name="pdf_legal_analysis.txt",

                        mime="text/plain",

                        key="download_pdf_report"

                    )


        # =================================================
        # TXT FILE
        # =================================================

        elif file_name.endswith(".txt"):


            text_content = extract_text_file(
                file_bytes
            )


            edited_txt = st.text_area(

                "📄 File Content",

                value=text_content,

                height=400

            )


            if st.button(

                "⚖️ Analyze TXT",

                type="primary",

                key="txt_analysis"

            ):


                with st.spinner(
                    "⚖️ Analysis జరుగుతోంది..."
                ):


                    prompt = f"""

క్రింది complaint/case text ను

BNS, BNSS మరియు BSA perspective నుండి
విశ్లేషించండి.


CASE TEXT:

{edited_txt}


ఈ headings ఉపయోగించండి:


## 1. Summary

## 2. Allegations

## 3. Important Facts

## 4. Possible BNS Offences

## 5. Relevant BNS Sections

## 6. IPC Comparison

## 7. Punishment

## 8. Cognizable / Non-Cognizable

## 9. Bailable / Non-Bailable

## 10. BNSS Procedure

## 11. BSA Evidence

## 12. Digital Evidence

## 13. Investigation Steps

## 14. IO Checklist

## 15. Final Observations


Section numbers guess చేయకండి.

"""


                    result = analyze_text(
                        prompt
                    )


                st.markdown("---")


                st.subheader(
                    "📋 TXT Legal Analysis"
                )


                st.markdown(
                    result
                )


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
    "AI-generated analysis should be verified with the "
    "applicable official legislation and legal authorities."
)
