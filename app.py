import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from PIL import Image
import base64


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="BNS FIR Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA FIR Legal Assistant")

st.caption(
    "Complaint facts ఆధారంగా preliminary legal analysis కోసం."
)

st.warning(
    "⚠️ ఇది AI-assisted preliminary analysis మాత్రమే. "
    "FIRలో sections నమోదు చేసే ముందు అధికారిక BNS/BNSS/BSA text, "
    "complaint facts మరియు evidence ఆధారంగా verification చేయాలి."
)


# =========================================================
# GROQ API
# =========================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)

except Exception:
    st.error(
        "GROQ_API_KEY కనిపించలేదు. "
        "Streamlit → Settings → Secretsలో GROQ_API_KEY set చేయండి."
    )
    st.stop()


# =========================================================
# MODELS
# =========================================================

TEXT_MODEL = "openai/gpt-oss-120b"

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are a highly cautious Indian criminal-law FIR analysis assistant.

Analyze complaints under:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

VERY IMPORTANT:

1. NEVER invent a section number.

2. Do not assume that every allegation automatically constitutes an offence.

3. Use ONLY facts present in the complaint.

4. Do not add facts which are not stated.

5. Separate:
   - Alleged facts
   - Legal ingredients
   - Facts supporting the ingredient
   - Missing facts
   - Evidence required
   - Possible section
   - Verification required

6. If the facts are insufficient, clearly say:
   "Further verification required."

7. For BNS Section 85, carefully check whether the facts satisfy
   the statutory meaning of cruelty under Section 86.

8. A salary/money dispute should NOT automatically be treated as
   dowry/property demand or cruelty.

9. A threat to kill should be examined separately as criminal intimidation.
   Verify the exact threat, circumstances and intention to cause alarm.

10. A husband living with another woman should not automatically be
    treated as a criminal offence. Analyze only what is actually alleged.

11. Do not fabricate judgments, case laws, circulars or government orders.

12. If there is uncertainty between sections, explain the distinction.

13. Give the final analysis in Telugu.

14. Never claim that an offence is conclusively proved merely from a complaint.

15. If a section number cannot be reliably verified, write:
    "Section verification required."

OUTPUT:

## 1. ఫిర్యాదులోని ప్రధాన ఆరోపణలు

## 2. Legal Ingredient Analysis

Use a table:

| ఆరోపణ | అవసరమైన Legal Ingredients | Complaintలో ఉన్న Facts | Missing Facts | Evidence |

## 3. పరిశీలించదగిన BNS Sections

For every possible section:

Section:
Offence:
Why it may apply:
Supporting facts:
Missing facts:
Confidence: HIGH / MEDIUM / LOW

## 4. వెంటనే section పెట్టకూడని అంశాలు

Explain why.

## 5. Investigation Checklist

Give practical points for the Investigating Officer.

## 6. Final Provisional FIR View

Clearly separate:

A. Sections reasonably supported by supplied facts
B. Sections requiring further verification
C. Allegations which are presently insufficient

Do NOT guess.
"""


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf(file):

    text = ""

    try:
        reader = PdfReader(file)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text.strip()

    except Exception as e:

        return f"PDF extraction error: {e}"


# =========================================================
# DOCX TEXT EXTRACTION
# =========================================================

def extract_docx(file):

    try:

        document = Document(file)

        paragraphs = []

        for paragraph in document.paragraphs:

            if paragraph.text.strip():

                paragraphs.append(paragraph.text)

        return "\n".join(paragraphs)

    except Exception as e:

        return f"DOCX extraction error: {e}"


# =========================================================
# IMAGE → BASE64
# =========================================================

def image_to_base64(uploaded_file):

    image = Image.open(uploaded_file)

    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    from io import BytesIO

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=90
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


# =========================================================
# IMAGE OCR USING GROQ VISION
# =========================================================

def extract_image_text(uploaded_file):

    try:

        image_base64 = image_to_base64(
            uploaded_file
        )

        response = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[

                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",

                            "text": """
ఈ complaint/report imageలో ఉన్న textను
సాధ్యమైనంత ఖచ్చితంగా చదివి type చేయండి.

IMPORTANT:
- Textను summarize చేయవద్దు.
- మీకు కనిపించిన text మాత్రమే ఇవ్వండి.
- కనిపించని words ఊహించవద్దు.
- Names, dates, places, section numbers, amounts
  ఉన్నట్లయితే వాటిని మార్చవద్దు.
- Telugu text అయితే Teluguలోనే ఇవ్వండి.
"""
                        },

                        {
                            "type": "image_url",

                            "image_url": {
                                "url":
                                f"data:image/jpeg;base64,{image_base64}"
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

        return f"Image OCR error: {e}"


# =========================================================
# TABS
# =========================================================

tab1, tab2 = st.tabs(
    [
        "📝 Complaint Text",
        "📂 Upload Document"
    ]
)


complaint_text = ""


# =========================================================
# TAB 1 - TEXT
# =========================================================

with tab1:

    st.subheader("📝 Complaint / Report Text")

    text_input = st.text_area(
        "Complaint details ఇక్కడ paste చేయండి",
        height=350,
        placeholder="ఫిర్యాదు / రిపోర్టు వివరాలను ఇక్కడ paste చేయండి..."
    )

    if text_input.strip():

        complaint_text = text_input


# =========================================================
# TAB 2 - DOCUMENT UPLOAD
# =========================================================

with tab2:

    st.subheader("📂 Upload Complaint / Report")

    st.write(
        "క్రింది boxపై click చేసి complaint file select చేయండి."
    )

    uploaded_file = st.file_uploader(

        "Upload Document",

        type=[
            "pdf",
            "docx",
            "txt",
            "jpg",
            "jpeg",
            "png"
        ],

        key="complaint_upload"
    )


    if uploaded_file is not None:

        st.success(
            f"✅ Uploaded: {uploaded_file.name}"
        )


        file_name = uploaded_file.name.lower()


        # -------------------------------------------------
        # TXT
        # -------------------------------------------------

        if file_name.endswith(".txt"):

            try:

                complaint_text = (
                    uploaded_file
                    .read()
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

                st.text_area(
                    "Extracted Text",
                    complaint_text,
                    height=350
                )

            except Exception as e:

                st.error(
                    f"TXT reading error: {e}"
                )


        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        elif file_name.endswith(".pdf"):

            complaint_text = extract_pdf(
                uploaded_file
            )

            if complaint_text:

                st.text_area(
                    "Extracted PDF Text",
                    complaint_text,
                    height=350
                )

            else:

                st.warning(
                    "PDFలో selectable text కనిపించలేదు. "
                    "ఇది scanned PDF అయితే JPG/PNGగా upload చేయండి."
                )


        # -------------------------------------------------
        # DOCX
        # -------------------------------------------------

        elif file_name.endswith(".docx"):

            complaint_text = extract_docx(
                uploaded_file
            )

            st.text_area(
                "Extracted DOCX Text",
                complaint_text,
                height=350
            )


        # -------------------------------------------------
        # JPG / JPEG / PNG
        # -------------------------------------------------

        elif file_name.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            st.image(
                uploaded_file,
                caption="Uploaded Complaint",
                use_container_width=True
            )

            with st.spinner(
                "Imageలో ఉన్న complaint text చదువుతున్నాను..."
            ):

                complaint_text = extract_image_text(
                    uploaded_file
                )

            st.subheader(
                "📝 Extracted Complaint Text"
            )

            st.text_area(
                "OCR Text",
                complaint_text,
                height=350
            )


# =========================================================
# ANALYZE BUTTON
# =========================================================

st.markdown("---")

analyze_button = st.button(
    "⚖️ FIR Legal Analysis",
    type="primary",
    use_container_width=True
)


# =========================================================
# LEGAL ANALYSIS
# =========================================================

if analyze_button:

    if not complaint_text.strip():

        st.error(
            "ముందుగా Complaint Text ఇవ్వండి లేదా Document upload చేయండి."
        )

    else:

        complaint_text = complaint_text[:60000]


        user_prompt = f"""

క్రింద ఉన్న complaint/report ఆధారంగా మాత్రమే
FIR legal analysis చేయండి.

Complaintలో లేని facts ఏవీ ఊహించకండి.

========================
COMPLAINT / REPORT
========================

{complaint_text}

========================

పై system instructions ప్రకారం
Teluguలో detailed preliminary FIR analysis ఇవ్వండి.
"""


        with st.spinner(
            "⚖️ Legal ingredients మరియు possible BNS sections పరిశీలిస్తున్నాను..."
        ):

            try:

                response = client.chat.completions.create(

                    model=TEXT_MODEL,

                    messages=[

                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT
                        },

                        {
                            "role": "user",
                            "content": user_prompt
                        }

                    ],

                    temperature=0,

                    max_tokens=7000
                )


                result = (
                    response
                    .choices[0]
                    .message
                    .content
                )


                st.success(
                    "✅ Legal analysis పూర్తయింది."
                )


                st.markdown(result)


                # -------------------------------------------------
                # DOWNLOAD RESULT
                # -------------------------------------------------

                st.download_button(

                    "📥 Download Analysis",

                    data=result,

                    file_name="FIR_Legal_Analysis.txt",

                    mime="text/plain"
                )


            except Exception as e:

                st.error(
                    f"Groq API Error: {str(e)}"
                )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "⚠️ AI-assisted preliminary legal analysis only. "
    "Final FIR registration and applicable sections must be "
    "verified with the current statutory text and case facts."
        ) deenilo screen shots , covert pdf lu kuda read cheyagalagali,
