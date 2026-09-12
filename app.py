import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="BNS FIR Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA FIR Legal Assistant")

st.warning(
    "AI ఇచ్చే output preliminary legal analysis మాత్రమే. "
    "FIR నమోదు ముందు అధికారిక BNS/BNSS/BSA text మరియు facts/evidence ఆధారంగా "
    "Investigating Officer / competent authority verification చేయాలి."
)


# ---------------------------------------------------------
# GROQ CLIENT
# ---------------------------------------------------------
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("GROQ_API_KEY Streamlit Secretsలో సరిగ్గా set చేయండి.")
    st.stop()


# ---------------------------------------------------------
# MODEL
# ---------------------------------------------------------
MODEL = "openai/gpt-oss-120b"


# ---------------------------------------------------------
# LEGAL ANALYSIS PROMPT
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are a careful Indian criminal-law FIR analysis assistant.

Your job is NOT to guess sections.

You must analyze the complaint facts under:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

STRICT RULES:

1. Never invent a BNS/BNSS/BSA section number.

2. Do not assume that an allegation automatically satisfies a legal section.

3. Separate:
   A. FACTS ALLEGED IN THE COMPLAINT
   B. POSSIBLE OFFENCE
   C. LEGAL INGREDIENTS REQUIRED
   D. FACTS PRESENT
   E. FACTS MISSING / NEED VERIFICATION
   F. EVIDENCE TO COLLECT
   G. FINAL PROVISIONAL VIEW

4. If facts are insufficient, explicitly say:
   "Further verification required."

5. Do not convert every marital dispute into cruelty.

6. For BNS Section 85, verify whether the facts satisfy the statutory meaning
   of cruelty under Section 86.

7. A demand relating to salary/money should NOT automatically be treated as
   unlawful property/valuable-security demand. Analyze the exact facts.

8. For criminal intimidation, verify:
   - threat
   - intention to cause alarm
   - nature of threat
   - whether the threat concerns death or grievous hurt
   before recommending the appropriate provision.

9. A statement that the husband is living with another woman is not by itself
   sufficient to create a criminal offence. Treat it separately and carefully.

10. Do not give a confident section merely because it appears plausible.

11. If there is uncertainty between two sections, explain the distinction.

12. Do not fabricate case law, FIR numbers, judgments, police circulars,
    government orders or citations.

13. Do not state that an offence is conclusively proved merely from a complaint.

14. Give the final result in Telugu.

15. Use exact BNS section numbers only when you are sufficiently confident
    about the statutory provision. If uncertain, write:
    "Section verification required."

16. The final FIR recommendation must be based ONLY on the facts supplied
    in the complaint.

OUTPUT FORMAT:

### 1. ఫిర్యాదులో ఉన్న ప్రధాన ఆరోపణలు

### 2. ప్రతి ఆరోపణకు సంబంధించిన చట్టపరమైన అంశం

Table:

| ఆరోపణ | అవసరమైన Legal Ingredients | ఫిర్యాదులో ఉన్న Facts | Missing Facts | Evidence |

### 3. పరిశీలించదగిన BNS Sections

For every section:

Section:
Offence:
Why it may apply:
What facts support it:
What facts are missing:
Confidence: HIGH / MEDIUM / LOW

### 4. FIRలో వెంటనే section పెట్టకూడని అంశాలు

Explain why.

### 5. Investigationలో నిర్ధారించాల్సిన అంశాలు

Give practical investigation checklist.

### 6. Provisional FIR view

Give:
- Recommended sections, if sufficiently supported
- Sections requiring verification
- If facts are insufficient, explicitly say so

IMPORTANT:
Do not add facts that are not in the complaint.
"""


# ---------------------------------------------------------
# TEXT EXTRACTION
# ---------------------------------------------------------
def extract_pdf(file):
    text = ""

    try:
        reader = PdfReader(file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        return f"PDF extraction error: {e}"

    return text


def extract_docx(file):
    try:
        document = Document(file)

        text = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)

        return "\n".join(text)

    except Exception as e:
        return f"DOCX extraction error: {e}"


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:

    st.header("📂 Complaint Input")

    uploaded_file = st.file_uploader(
        "Complaint / Report upload చేయండి",
        type=["txt", "pdf", "docx"]
    )

    st.markdown("---")

    st.info(
        "Accuracy కోసం complaintలో ఉన్న facts మాత్రమే ఉపయోగించండి. "
        "అనుమానం ఉన్న విషయాలను AIకి factగా ఇవ్వకండి."
    )


# ---------------------------------------------------------
# TEXT INPUT
# ---------------------------------------------------------
tab1, tab2 = st.tabs(
    ["📝 Complaint Text", "📂 Uploaded Document"]
)


complaint_text = ""


with tab1:

    complaint_text = st.text_area(
        "ఫిర్యాదు / రిపోర్టు వివరాలు ఇక్కడ paste చేయండి",
        height=350,
        placeholder="ఉదా: ఫిర్యాది తెలిపిన ప్రకారం..."
    )


with tab2:

    if uploaded_file:

        file_name = uploaded_file.name.lower()

        if file_name.endswith(".txt"):

            complaint_text = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

            st.text_area(
                "Extracted Complaint",
                complaint_text,
                height=350
            )

        elif file_name.endswith(".pdf"):

            complaint_text = extract_pdf(uploaded_file)

            st.text_area(
                "Extracted PDF Text",
                complaint_text,
                height=350
            )

        elif file_name.endswith(".docx"):

            complaint_text = extract_docx(uploaded_file)

            st.text_area(
                "Extracted DOCX Text",
                complaint_text,
                height=350
            )


# ---------------------------------------------------------
# ANALYSIS BUTTON
# ---------------------------------------------------------
st.markdown("---")

analyze = st.button(
    "⚖️ FIR Legal Analysis",
    type="primary",
    use_container_width=True
)


# ---------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------
if analyze:

    if not complaint_text.strip():

        st.error("ముందుగా Complaint / Report వివరాలు ఇవ్వండి.")

    else:

        # Limit excessively large input
        complaint_text = complaint_text[:60000]

        user_prompt = f"""
క్రింద ఇచ్చిన complaint/reportను మాత్రమే ఆధారంగా తీసుకుని
BNS/BNSS/BSA ప్రకారం preliminary FIR legal analysis చేయండి.

IMPORTANT:
Complaintలో లేని facts ఏవీ ఊహించవద్దు.

COMPLAINT / REPORT:

-------------------------
{complaint_text}
-------------------------

పైన ఇచ్చిన strict legal analysis formatను తప్పకుండా పాటించండి.
"""


        with st.spinner(
            "Complaint factsను analyze చేసి legal provisions verify చేస్తున్నాను..."
        ):

            try:

                response = client.chat.completions.create(
                    model=MODEL,

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

                    temperature=0.0,

                    max_tokens=6000
                )


                result = response.choices[0].message.content

                st.success("Analysis పూర్తయింది.")

                st.markdown(result)


                # -------------------------------------------------
                # DOWNLOAD
                # -------------------------------------------------
                st.download_button(
                    label="📥 Analysis TXT Download",
                    data=result,
                    file_name="FIR_Legal_Analysis.txt",
                    mime="text/plain"
                )


            except Exception as e:

                st.error(
                    f"Groq API Error: {str(e)}"
                )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown("---")

st.caption(
    "⚠️ This application provides AI-assisted preliminary legal analysis. "
    "Final FIR sections must be verified against the applicable statutory text "
    "and the facts/evidence available to the Investigating Officer."
)
