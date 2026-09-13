import io
import os
import re
from datetime import datetime, date

import streamlit as st
from PIL import Image
from groq import Groq


# =========================================================
# STREAMLIT PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Police Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్")
st.caption("BNS / BNSS / BSA + IPC / CrPC / Indian Evidence Act – Date Based Legal Analysis")


# =========================================================
# CONSTANTS
# =========================================================

NEW_LAW_DATE = date(2024, 7, 1)


# =========================================================
# GROQ API KEY
# =========================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error(
        "GROQ_API_KEY కనబడలేదు.\n\n"
        "Streamlit → Settings / Secrets లో GROQ_API_KEY పెట్టండి."
    )
    st.stop()


# =========================================================
# GROQ CLIENT
# =========================================================

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Groq client ప్రారంభించలేకపోయింది: {e}")
    st.stop()


MODEL_NAME = "openai/gpt-oss-120b"


# =========================================================
# OPTIONAL PDF SUPPORT
# =========================================================

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# =========================================================
# OPTIONAL OCR SUPPORT
# =========================================================

try:
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


# =========================================================
# DATE EXTRACTION FUNCTIONS
# =========================================================

def parse_date_string(value):
    """
    Convert common Indian date formats into datetime.date.
    """

    if not value:
        return None

    value = value.strip()

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d.%m.%y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    return None


def extract_incident_date(text):
    """
    Try to identify incident/offence date from user-provided text.
    """

    if not text:
        return None

    patterns = [
        r"(?:incident date|date of incident|offence date|date of offence)"
        r"\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",

        r"(?:occurrence date|date of occurrence)"
        r"\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",

        r"(?:incident|offence|occurrence)"
        r".{0,40}?"
        r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            parsed = parse_date_string(match.group(1))

            if parsed:
                return parsed

    # General date search as fallback
    general_pattern = r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b"

    matches = re.findall(general_pattern, text)

    for item in matches:
        parsed = parse_date_string(item)

        if parsed:
            return parsed

    return None


# =========================================================
# LAW SELECTION
# =========================================================

def select_law(incident_date, old_case_pending=False):
    """
    Decide which criminal-law framework should primarily be used.

    IMPORTANT:
    - Before 01-07-2024 -> old law framework
    - On/after 01-07-2024 -> new law framework
    - Old proceedings pending at commencement may continue under old law
      because of repeal-and-savings provisions.
    """

    if incident_date is None:
        return {
            "status": "UNKNOWN",
            "framework": "DATE_REQUIRED",
            "reason": (
                "Incident/offence date could not be identified. "
                "Do not guess BNS/IPC. Ask for the date of occurrence."
            )
        }

    if old_case_pending:
        return {
            "status": "OLD_PENDING",
            "framework": "IPC / CrPC / INDIAN EVIDENCE ACT",
            "reason": (
                "The case/proceeding was already pending before "
                "01-07-2024. Repeal-and-savings provisions may preserve "
                "the old-law framework for the pending proceeding."
            )
        }

    if incident_date < NEW_LAW_DATE:
        return {
            "status": "OLD",
            "framework": "IPC / CrPC / INDIAN EVIDENCE ACT",
            "reason": (
                f"Incident date {incident_date.strftime('%d-%m-%Y')} "
                "is before 01-07-2024."
            )
        }

    return {
        "status": "NEW",
        "framework": "BNS / BNSS / BSA",
        "reason": (
            f"Incident date {incident_date.strftime('%d-%m-%Y')} "
            "is on/after 01-07-2024."
        )
    }


# =========================================================
# TEXT EXTRACTION FROM PDF
# =========================================================

def extract_pdf_text(uploaded_file):

    if not PDF_AVAILABLE:
        return (
            "PDF reader library (pypdf) is not installed. "
            "Please add pypdf to requirements.txt."
        )

    try:
        uploaded_file.seek(0)

        reader = PdfReader(uploaded_file)

        pages = []

        for page in reader.pages:
            try:
                page_text = page.extract_text()

                if page_text:
                    pages.append(page_text)

            except Exception:
                continue

        text = "\n".join(pages).strip()

        if text:
            return text

        return (
            "PDFలో selectable text కనిపించలేదు. "
            "ఇది scanned PDF కావచ్చు. PDF pagesను imagesగా OCR చేయాల్సి ఉంటుంది."
        )

    except Exception as e:
        return f"PDF చదవడంలో సమస్య: {e}"


# =========================================================
# IMAGE OCR
# =========================================================

def extract_image_text(uploaded_file):

    if not OCR_AVAILABLE:
        return (
            "OCR library (pytesseract) అందుబాటులో లేదు. "
            "requirements.txtలో pytesseract పెట్టండి."
        )

    try:
        image = Image.open(uploaded_file)

        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        if text.strip():
            return text.strip()

        return (
            "Image నుంచి text గుర్తించలేకపోయింది. "
            "Handwriting లేదా Telugu text అయితే OCR accuracy తక్కువగా ఉండవచ్చు."
        )

    except Exception as e:
        return f"Image OCRలో సమస్య: {e}"


# =========================================================
# FILE EXTRACTION
# =========================================================

def extract_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        try:
            uploaded_file.seek(0)
            return uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )
        except Exception as e:
            return f"TXT చదవడంలో సమస్య: {e}"

    if filename.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)

    if filename.endswith(
        (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    ):
        return extract_image_text(uploaded_file)

    return "ఈ file format ప్రస్తుతం support చేయబడలేదు."


# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = r"""
You are a careful Indian criminal-law research and investigation assistant
for police investigation work.

Your job is NOT to blindly assign BNS/BNSS/BSA sections.

=========================================================
1. MOST IMPORTANT RULE — DATE OF OFFENCE
=========================================================

First identify the INCIDENT / OFFENCE / OCCURRENCE DATE.

The new criminal-law framework came into force from 01-07-2024:

- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

For an offence occurring BEFORE 01-07-2024:

Do NOT automatically apply:
- BNS
- BNSS
- BSA

The substantive offence should ordinarily be analysed under the law
applicable when the offence was committed, subject to repeal/savings
and any other applicable transitional law.

For old cases/proceedings that were already pending when the new laws
came into force, carefully consider the relevant repeal-and-savings
provisions before suggesting procedural/evidentiary provisions.

For an offence occurring ON or AFTER 01-07-2024:

Use:
- BNS for offences/punishments
- BNSS for criminal procedure
- BSA for evidence

=========================================================
2. NEVER GUESS THE DATE
=========================================================

If the incident/offence date is not available:

Say clearly:

"Incident/offence date is required to select the applicable criminal-law
framework."

Do NOT guess BNS or IPC.

Distinguish between:

- date of occurrence
- date of complaint
- FIR date
- investigation date
- arrest date
- charge-sheet date
- trial date
- date on which proceeding became pending

Do not confuse FIR date with offence date.

=========================================================
3. OLD-LAW CASES
=========================================================

For incidents before 01-07-2024, use the historical framework where
appropriate:

SUBSTANTIVE LAW:
Indian Penal Code, 1860 (IPC)

PROCEDURE:
Code of Criminal Procedure, 1973 (CrPC)

EVIDENCE:
Indian Evidence Act, 1872 (IEA)

Do not convert an old FIR's historical IPC/CrPC/IEA provisions into
BNS/BNSS/BSA merely because the report is being generated today.

If discussing a historical 2017 theft case, for example, do not say:

"BNS 305 is the offence."

Instead identify the applicable IPC provision and explain that
the incident predates 01-07-2024.

=========================================================
4. NEW-LAW CASES
=========================================================

For incidents on/after 01-07-2024:

Use:

BNS = substantive offences and punishments

BNSS = FIR, investigation, arrest, search, seizure, remand,
       witness procedure, case diary, final report, etc.

BSA = relevancy/admissibility/proof of evidence, including electronic
      records where applicable.

=========================================================
5. SECTION ACCURACY
=========================================================

NEVER invent section numbers.

Before mentioning a section:

1. Identify the Act.
2. Identify the exact section.
3. State what that section actually covers.
4. Do not assign a section merely because it sounds related.

If uncertain, say:

"Section should be verified from the official text before use."

=========================================================
6. IMPORTANT PROCEDURAL DISTINCTIONS
=========================================================

Do NOT confuse:

- FIR registration
- investigation
- search
- search warrant
- seizure
- arrest
- notice to appear
- production before Magistrate
- remand
- case diary
- final police report

For example, do not automatically describe the general investigation
section as the search section.

=========================================================
7. SEARCH
=========================================================

Distinguish:

A. Search by police officer under statutory police powers.

B. Search pursuant to a warrant / judicial process.

Do not automatically say that every police search requires a Magistrate's
search warrant.

State the factual and legal basis for the particular search.

=========================================================
8. WITNESSES
=========================================================

Do not invent a mandatory number of panch witnesses.

Do not state "exactly 2 witnesses" or "exactly 3 witnesses" unless the
specific legal provision actually requires that number.

Distinguish:

- complainant
- eyewitness
- circumstantial witness
- seizure/panch witness
- independent witness
- police witness
- expert/forensic witness

=========================================================
9. DIGITAL / ELECTRONIC EVIDENCE
=========================================================

Do not automatically apply every electronic-evidence section to every
mobile phone, SIM, CCTV, screenshot, WhatsApp message, call detail
record, or photograph.

First identify:

- What is the actual evidence?
- Is it a physical object?
- Is it an electronic/digital record?
- Who produced it?
- How was it obtained?
- Is authenticity disputed?
- What statutory proof/admissibility requirement applies?

Distinguish:

- mobile phone as physical property/evidence
- SIM card as physical item
- CDR as electronic record/data
- CCTV footage as electronic/digital record
- WhatsApp/chat export as electronic record
- screenshot as a copy/representation of digital information
- original device/data source
- forensic extraction/report

Do NOT automatically say:

"BSA Section 63 certificate is required for every mobile phone."

Analyse the actual evidence and applicable statutory requirements.

Similarly, do not automatically describe BSA Section 64 as a
"CDR notice section". Explain the actual provision and the actual
procedure applicable to obtaining the record.

=========================================================
10. BSA CERTIFICATE
=========================================================

If an electronic-record certificate is relevant, explain:

- what electronic record is being relied upon
- what statutory provision applies
- who is in a position to provide the required certificate/details
- what device/source information is relevant
- whether the evidence is primary/original or a reproduced/derived record

Do not automatically say:

"Only a forensic expert can issue the certificate."

Do not automatically say:

"Every screenshot requires a certificate."

The conclusion must depend on the nature and mode of production of
the electronic record.

=========================================================
11. ARREST
=========================================================

Do not recommend arrest merely because an offence is cognizable.

Analyse:

- cognizable/non-cognizable
- bailable/non-bailable
- necessity of arrest
- statutory conditions
- identification of accused
- evidence available
- risk of absconding
- cooperation with investigation
- applicable safeguards

If the accused is unknown, do not write as if the accused has already
been identified.

=========================================================
12. BAIL
=========================================================

Clearly distinguish:

- bailable
- non-bailable
- anticipatory bail
- regular bail
- statutory/default bail where relevant

Do not write "generally bailable" or "generally non-bailable" when the
official classification can be identified.

=========================================================
13. PUNISHMENT
=========================================================

State punishment accurately.

Do not invent:

- minimum imprisonment
- maximum imprisonment
- fine
- classification
- trial court

If classification is uncertain, say so and recommend verification.

=========================================================
14. TRIAL COURT
=========================================================

Do not automatically say "Sessions Court" merely because punishment is
high.

Check the applicable schedule/classification and state the appropriate
court.

=========================================================
15. OLD CASE EXAMPLE
=========================================================

If the user provides:

Incident date: 28-05-2017

Then the report must NOT say:

"BNS 305 applies because theft in dwelling house."

Instead it must recognize that the occurrence predates 01-07-2024 and
analyse the offence under the law applicable at that time, subject to
the applicable savings/transitional provisions.

For a 2017 house-theft case, the model should consider the relevant
IPC provision rather than automatically substituting BNS 305.

=========================================================
16. REPORT FORMAT
=========================================================

Always generate the report in this order:

1. CASE DATE & APPLICABLE LAW
2. CASE SUMMARY
3. APPLICABLE OFFENCE(S)
4. SECTION-WISE LEGAL ANALYSIS
5. COGNIZABLE / NON-COGNIZABLE
6. BAILABLE / NON-BAILABLE
7. PUNISHMENT
8. TRIAL COURT
9. FIR / COMPLAINT PROCEDURE
10. INVESTIGATION STEPS
11. ARREST ANALYSIS
12. SEARCH / SEIZURE
13. WITNESS PROCEDURE
14. DIGITAL / ELECTRONIC EVIDENCE
15. FORENSIC REQUIREMENTS
16. RECOVERY OF PROPERTY
17. IDENTIFICATION / TEST IDENTIFICATION IF RELEVANT
18. CASE DIARY / INVESTIGATION RECORD
19. FINAL REPORT / CHARGE SHEET
20. INVESTIGATION OFFICER CHECKLIST
21. LEGAL CAUTIONS / ITEMS TO VERIFY

=========================================================
17. DATE WARNING
=========================================================

At the top of every report include:

"Applicable-law determination is based primarily on the stated
occurrence/offence date and must be checked against the relevant
repeal-and-savings/transitional provisions and the actual procedural
history of the case."

If the case is pre-01-07-2024, visibly display:

"⚠️ OLD-LAW CASE:
IPC / CrPC / Indian Evidence Act framework applies subject to
repeal-and-savings/transitional provisions."

If the case is on/after 01-07-2024, display:

"✅ NEW-LAW CASE:
BNS / BNSS / BSA framework applies."

=========================================================
18. NO FABRICATION
=========================================================

Never invent:

- FIR number
- police station
- officer name
- accused identity
- dates
- witness names
- section numbers
- court orders
- forensic results
- recoveries
- case-diary entries

If information is missing, say:

"Not provided."

=========================================================
19. LEGAL DISCLAIMER
=========================================================

This is an investigation-support tool and not a substitute for the
official statute, notification, court order, prosecutor's opinion,
or legal advice.

For operational use, verify the final section numbers and procedure
against the official current statute and applicable case-specific
orders/notifications.
"""


# =========================================================
# BUILD USER PROMPT
# =========================================================

def build_user_prompt(case_text, law_info, old_pending):

    incident_date_text = "Not identified"

    incident_date = extract_incident_date(case_text)

    if incident_date:
        incident_date_text = incident_date.strftime("%d-%m-%Y")

    pending_text = "Yes" if old_pending else "No / not stated"

    return f"""
Analyse the following police case carefully.

IMPORTANT DATE INFORMATION
--------------------------
Incident / offence date detected:
{incident_date_text}

01-07-2024 transition date:
01-07-2024

Old proceeding pending before 01-07-2024:
{pending_text}

Selected primary framework:
{law_info["framework"]}

Reason:
{law_info["reason"]}

CASE MATERIAL
-------------
{case_text}

MANDATORY INSTRUCTIONS
----------------------

1. First state the incident/offence date.
2. State which legal framework applies.
3. Explain why that framework applies.
4. Do not substitute BNS/BNSS/BSA for a pre-01-07-2024 occurrence.
5. If this is an old pending proceeding, separately explain the
   repeal-and-savings issue.
6. Do not guess sections.
7. Do not fabricate facts.
8. If an exact section needs verification, clearly mark it as
   "VERIFY".
9. Distinguish physical evidence from electronic evidence.
10. Do not automatically require a BSA electronic-record certificate
    for every digital item.
11. Give practical investigation steps.
12. Give a final IO checklist.
13. Mention all assumptions separately.
"""


# =========================================================
# CALL GROQ
# =========================================================

def investigate_case(case_text, law_info, old_pending):

    user_prompt = build_user_prompt(
        case_text,
        law_info,
        old_pending
    )

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
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
            temperature=0.1,
            max_tokens=12000
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "AI legal analysisలో error వచ్చింది.\n\n"
            f"Error: {e}"
        )


# =========================================================
# CASE DETAILS
# =========================================================

st.subheader("📝 కేసు వివరాలు")

case_text = st.text_area(
    "కేసు వివరాలు / FIR / Complaint వివరాలు ఇక్కడ paste చేయండి",
    height=300,
    placeholder=(
        "ఉదాహరణ:\n"
        "Incident Date: 28-05-2017\n"
        "FIR Date: 29-05-2017\n"
        "Unknown persons entered the house..."
    )
)


# =========================================================
# OLD PENDING CASE OPTION
# =========================================================

st.subheader("⚖️ Applicable Law Selection")

st.info(
    "Incident date 01-07-2024 కంటే ముందు ఉంటే old-law framework "
    "(IPC / CrPC / IEA)ను ప్రధానంగా ఉపయోగిస్తుంది."
)

old_pending = st.checkbox(
    "01-07-2024కి ముందు ఈ కేసు / proceeding ఇప్పటికే pendingలో ఉందా?"
)


# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader("📎 FIR / Complaint / Document Upload")

uploaded_file = st.file_uploader(
    "PDF / TXT / Image upload చేయండి",
    type=[
        "pdf",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp"
    ]
)


# =========================================================
# EXTRACT FILE
# =========================================================

uploaded_text = ""

if uploaded_file is not None:

    with st.spinner("Document చదువుతోంది..."):
        uploaded_text = extract_uploaded_file(uploaded_file)

    if uploaded_text:

        st.success("Document text తీసుకుంది.")

        with st.expander("📄 Extracted Text చూడండి"):
            st.text_area(
                "Extracted Text",
                uploaded_text,
                height=250
            )


# =========================================================
# COMBINE INPUT
# =========================================================

combined_text = case_text.strip()

if uploaded_text.strip():

    if combined_text:
        combined_text += "\n\n"
        combined_text += "----- UPLOADED DOCUMENT -----\n\n"

    combined_text += uploaded_text.strip()


# =========================================================
# DETECT DATE
# =========================================================

incident_date = extract_incident_date(combined_text)


if incident_date:

    law_info = select_law(
        incident_date,
        old_pending
    )

    if law_info["status"] == "OLD_PENDING":

        st.warning(
            "⚠️ OLD PENDING CASE\n\n"
            "Primary framework: IPC / CrPC / Indian Evidence Act\n\n"
            "01-07-2024కి ముందు pending proceeding కావడంతో "
            "repeal-and-savings provisions కూడా పరిగణించాలి."
        )

    elif law_info["status"] == "OLD":

        st.warning(
            f"⚠️ OLD-LAW CASE\n\n"
            f"Incident Date: {incident_date.strftime('%d-%m-%Y')}\n\n"
            "Applicable primary framework:\n"
            "IPC / CrPC / Indian Evidence Act"
        )

    elif law_info["status"] == "NEW":

        st.success(
            f"✅ NEW-LAW CASE\n\n"
            f"Incident Date: {incident_date.strftime('%d-%m-%Y')}\n\n"
            "Applicable primary framework:\n"
            "BNS / BNSS / BSA"
        )

else:

    law_info = {
        "status": "UNKNOWN",
        "framework": "DATE_REQUIRED",
        "reason": "Incident/offence date not detected."
    }

    st.warning(
        "⚠️ Incident / offence date గుర్తించబడలేదు. "
        "Analysis చేయడానికి ముందు date verify చేయండి."
    )


# =========================================================
# ANALYZE BUTTON
# =========================================================

if st.button(
    "⚖️ Legal Analysis ప్రారంభించండి",
    type="primary",
    use_container_width=True
):

    if not combined_text.strip():

        st.error(
            "ముందుగా case details లేదా document upload చేయండి."
        )

    elif incident_date is None:

        st.error(
            "❌ Incident / offence date కనిపించలేదు.\n\n"
            "ఉదాహరణగా ఇలా ఇవ్వండి:\n"
            "Incident Date: 28-05-2017"
        )

    else:

        st.subheader("🔎 Applicable Law")

        if law_info["status"] == "OLD_PENDING":

            st.warning(
                "IPC / CrPC / Indian Evidence Act\n"
                "Old pending proceeding – savings/transitional provisions apply."
            )

        elif law_info["status"] == "OLD":

            st.warning(
                "IPC / CrPC / Indian Evidence Act"
            )

        else:

            st.success(
                "BNS / BNSS / BSA"
            )

        st.write(
            f"**Incident Date:** "
            f"{incident_date.strftime('%d-%m-%Y')}"
        )

        st.write(
            f"**Reason:** {law_info['reason']}"
        )

        with st.spinner(
            "Legal analysis తయారు చేస్తోంది... "
        ):

            result = investigate_case(
                combined_text,
                law_info,
                old_pending
            )

        st.subheader("📋 Legal Analysis Result")

        st.markdown(result)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "⚠️ This tool is for investigation-support and legal research only. "
    "Final legal action should be verified against the official statute, "
    "notifications, court orders and case-specific facts."
)
