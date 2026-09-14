import os
import re
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image
from groq import Groq


# =========================================================
# OPTIONAL OCR / PDF LIBRARIES
# =========================================================

try:
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# =========================================================
# STREAMLIT PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Police Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్")
st.caption(
    "BNS • BNSS • BSA • IT Act | Complaint Analysis • OCR • Investigation Support"
)


# =========================================================
# CONSTANTS
# =========================================================

NEW_LAW_DATE = date(2024, 7, 1)

MODEL_NAME = "openai/gpt-oss-120b"


# =========================================================
# GROQ CLIENT
# =========================================================

def get_groq_client():

    api_key = None

    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        st.error(
            "❌ GROQ_API_KEY కనబడలేదు.\n\n"
            "Streamlit Cloud → Settings → Secrets లో "
            "GROQ_API_KEY add చేయండి."
        )
        st.stop()

    return Groq(api_key=api_key)


# =========================================================
# TELUGU DIGITS
# =========================================================

TELUGU_DIGITS = str.maketrans(
    "౦౧౨౩౪౫౬౭౮౯",
    "0123456789"
)


def normalize_digits(text):

    if not text:
        return ""

    return text.translate(TELUGU_DIGITS)


# =========================================================
# MONTH DICTIONARIES
# =========================================================

ENGLISH_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12
}


TELUGU_MONTHS = {
    "జనవరి": 1,
    "ఫిబ్రవరి": 2,
    "మార్చి": 3,
    "ఏప్రిల్": 4,
    "మే": 5,
    "జూన్": 6,
    "జులై": 7,
    "జూలై": 7,
    "ఆగస్టు": 8,
    "సెప్టెంబర్": 9,
    "సెప్టెంబరు": 9,
    "అక్టోబర్": 10,
    "అక్టోబరు": 10,
    "నవంబర్": 11,
    "నవంబరు": 11,
    "డిసెంబర్": 12,
    "డిసెంబరు": 12
}


# =========================================================
# SAFE DATE CREATION
# =========================================================

def safe_date(year, month, day):

    try:

        if year < 100:
            year += 2000

        return date(year, month, day)

    except Exception:
        return None


# =========================================================
# NUMERIC DATE PARSER
# =========================================================

def parse_date_string(value):

    if not value:
        return None

    value = normalize_digits(value.strip())

    patterns = [
        r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b",
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b",
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})\b",
    ]

    for pattern in patterns:

        match = re.search(pattern, value)

        if not match:
            continue

        groups = match.groups()

        try:

            if len(groups[0]) == 4:

                year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])

            else:

                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2])

                if year < 100:
                    year += 2000

            return safe_date(year, month, day)

        except Exception:
            continue

    return None


# =========================================================
# NAMED MONTH DATE PARSER
# =========================================================

def parse_named_month_date(text):

    if not text:
        return None

    normalized = normalize_digits(text)

    month_pattern = "|".join(
        sorted(
            list(ENGLISH_MONTHS.keys()) +
            list(TELUGU_MONTHS.keys()),
            key=len,
            reverse=True
        )
    )

    patterns = [

        # 10 September 2026
        rf"\b(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})\b",

        # September 10 2026
        rf"\b({month_pattern})\s+(\d{{1,2}})[,\s]+(\d{{4}})\b",

        # 10 సెప్టెంబర్ 2026
        rf"(\d{{1,2}})\s*({month_pattern})\s*(\d{{4}})",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE
        )

        if not match:
            continue

        groups = match.groups()

        try:

            if groups[0].isdigit():

                day = int(groups[0])
                month_name = groups[1].lower()
                year = int(groups[2])

            else:

                month_name = groups[0].lower()
                day = int(groups[1])
                year = int(groups[2])

            month = None

            for key, value in ENGLISH_MONTHS.items():

                if key.lower() == month_name.lower():
                    month = value
                    break

            if month is None:

                for key, value in TELUGU_MONTHS.items():

                    if key.lower() == month_name.lower():
                        month = value
                        break

            if month:
                return safe_date(year, month, day)

        except Exception:
            continue

    return None


# =========================================================
# RELATIVE DATE DETECTION
# =========================================================

def extract_relative_date(text, reference_date):

    if not text:
        return None, None

    lower = text.lower()

    # TODAY
    if re.search(r"\b(today)\b", lower) or "ఈ రోజు" in text or "ఈరోజు" in text:

        return reference_date, "Today / ఈ రోజు"

    # YESTERDAY
    if re.search(r"\b(yesterday)\b", lower) or "నిన్న" in text:

        return reference_date - timedelta(days=1), "Yesterday / నిన్న"

    # DAY BEFORE YESTERDAY
    if (
        "day before yesterday" in lower
        or "మొన్న" in text
    ):

        return reference_date - timedelta(days=2), "Day before yesterday / మొన్న"

    # LAST WEEK
    if (
        "last week" in lower
        or "గత వారం" in text
    ):

        return reference_date - timedelta(days=7), "Last week / గత వారం"

    # THIS WEEK
    if (
        "this week" in lower
        or "ఈ వారం" in text
    ):

        return reference_date, "This week / ఈ వారం"

    return None, None


# =========================================================
# INCIDENT DATE EXTRACTION
#
# IMPORTANT:
# EXPLICIT DATE ALWAYS HAS PRIORITY OVER
# RELATIVE DATE.
# =========================================================

def extract_incident_date(text, reference_date):

    if not text:
        return None, "Not detected"

    text = normalize_digits(text)

    # -----------------------------------------------------
    # PRIORITY 1:
    # NUMERIC EXPLICIT DATE
    # -----------------------------------------------------

    numeric_patterns = [
        r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b",
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b",
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2}\b"
    ]

    for pattern in numeric_patterns:

        match = re.search(pattern, text)

        if match:

            parsed = parse_date_string(match.group(0))

            if parsed:
                return parsed, f"Explicit numeric date: {match.group(0)}"

    # -----------------------------------------------------
    # PRIORITY 2:
    # NAMED MONTH DATE
    # -----------------------------------------------------

    named_date = parse_named_month_date(text)

    if named_date:

        return named_date, "Explicit named-month date"

    # -----------------------------------------------------
    # PRIORITY 3:
    # RELATIVE DATE
    # -----------------------------------------------------

    relative_date, source = extract_relative_date(
        text,
        reference_date
    )

    if relative_date:

        return relative_date, source

    return None, "Not detected"


# =========================================================
# LEGAL REFERENCE
# =========================================================

LEGAL_REFERENCE = r"""
STRICT LEGAL SECTION MAPPING

BNS = Bharatiya Nyaya Sanhita, 2023
BNSS = Bharatiya Nagarik Suraksha Sanhita, 2023
BSA = Bharatiya Sakshya Adhiniyam, 2023
IT Act = Information Technology Act, 2000


=========================================================
BNS 318 — CHEATING
=========================================================

BNS 318(1):
Definition / ingredients of cheating.

BNS 318(2):
Punishment for cheating:
Up to 3 years imprisonment, or fine, or both.

BNS 318(3):
Special form where offender was bound by law or legal contract
to protect the interests of the person concerned.

BNS 318(4):
Cheating + dishonest inducement to deliver property or valuable security.
Punishment up to 7 years and fine.

IMPORTANT:
DO NOT select BNS 318(4) merely because money was lost.

The facts must support:
1. deception,
2. dishonest/fraudulent inducement,
3. delivery of property/valuable security where applicable,
4. causal connection between deception and delivery.


=========================================================
BNS 319 — CHEATING BY PERSONATION
=========================================================

BNS 319(1):
Cheating by personation.

BNS 319(2):
Punishment up to 5 years, or fine, or both.

IMPORTANT:
Do NOT apply BNS 319 merely because:
- a phone was used,
- an app was used,
- an unknown person called,
- someone claimed to be a representative.

There must be facts supporting PERSONATION.


=========================================================
IT ACT 66C
=========================================================

Identity theft.

Apply only where there is fraudulent/dishonest use of:
- another person's electronic signature,
- password,
- or unique identification feature.


=========================================================
IT ACT 66D
=========================================================

Cheating by personation using:
- communication device, OR
- computer resource.

IMPORTANT:
Use only when BOTH are supported:
1. personation,
2. computer resource / communication device use.

Do not apply merely because the transaction occurred online.


=========================================================
BNSS
=========================================================

BNSS 173:
Information in cognizable cases.

BNSS 174:
Information as to non-cognizable cases.

BNSS 175:
Police officer's power to investigate cognizable case.

BNSS 176:
Procedure for investigation.

BNSS 179:
Police officer's power to require attendance of witnesses.

BNSS 180:
Examination of witnesses by police.

BNSS 181:
Statements to police and use thereof.

BNSS 185:
Search by police officer.

BNSS 193:
Report of police officer on completion of investigation.


IMPORTANT:
Do NOT describe BNSS 173 as a generic CDR request provision.

For CDR/IPDR/bank/app/platform records:
describe them as records to be obtained through the applicable
lawful investigative/requisition process.


=========================================================
BSA SECTION 63
=========================================================

BSA Section 63:
Admissibility of electronic records.

BSA 63(4):
Where a statement is desired to be given in evidence by virtue
of Section 63, the required certificate contains information
regarding:
- identification of electronic record,
- manner of production,
- device particulars,
- prescribed conditions.

IMPORTANT:
Do NOT say:
"Every electronic evidence automatically requires a BSA 63 certificate."

Instead:
Assess whether the particular electronic record is being
tendered in evidence under Section 63 and whether the statutory
certificate requirement applies.

Do NOT automatically name a certificate issuer.

Identify:
- source,
- device/system,
- person/entity in lawful control,
- manner of production,
- hash/details where applicable,
and state that certificate applicability/issuer requires
factual and legal verification.


=========================================================
BNSS FIRST SCHEDULE CLASSIFICATION
=========================================================

BNS 318(2):
Non-cognizable
Bailable
Any Magistrate

BNS 318(3):
Non-cognizable
Bailable
Any Magistrate

BNS 318(4):
Cognizable
Non-bailable
Magistrate of the First Class

BNS 319(2):
Cognizable
Bailable
Any Magistrate

IMPORTANT:
Only provide cognizable/bailable/court classification
when the exact subsection is selected.


=========================================================
LEGAL FRAMEWORK
=========================================================

For offences occurring on or after 01-07-2024:
Normally consider:
BNS + BNSS + BSA.

For offences occurring before 01-07-2024:
Normally consider the then-applicable:
IPC + CrPC + Indian Evidence Act,
subject to applicable savings/transitional provisions.

If date is uncertain:
DO NOT force a legal framework.
Mark it as requiring verification.
"""


# =========================================================
# DETERMINE LEGAL FRAMEWORK
# =========================================================

def determine_framework(incident_date):

    if not incident_date:

        return (
            "Incident date not established",
            False
        )

    if incident_date >= NEW_LAW_DATE:

        return (
            "BNS 2023 + BNSS 2023 + BSA 2023",
            False
        )

    return (
        "Pre-01-07-2024 framework: IPC + CrPC + Indian Evidence Act "
        "(subject to savings/transitional provisions)",
        True
    )


# =========================================================
# FILE TEXT EXTRACTION
# =========================================================

def extract_text_from_pdf(uploaded_file):

    if not PDF_AVAILABLE:

        return (
            "PDF extraction library 'pypdf' is not installed."
        )

    try:

        reader = PdfReader(uploaded_file)

        pages = []

        for index, page in enumerate(reader.pages):

            try:

                text = page.extract_text()

                if text:
                    pages.append(
                        f"\n--- PDF Page {index + 1} ---\n{text}"
                    )

            except Exception:
                continue

        result = "\n".join(pages)

        if result.strip():
            return result

        return (
            "PDF text could not be extracted. "
            "If this is a scanned PDF, OCR support may be required."
        )

    except Exception as e:

        return f"PDF extraction error: {str(e)}"


# =========================================================
# IMAGE OCR
# =========================================================

def extract_text_from_image(uploaded_file):

    if not OCR_AVAILABLE:

        return (
            "OCR library 'pytesseract' is not installed."
        )

    try:

        image = Image.open(uploaded_file)

        # First try Telugu + English
        try:

            text = pytesseract.image_to_string(
                image,
                lang="tel+eng"
            )

            if text and text.strip():
                return text

        except Exception:
            pass

        # Fallback English
        try:

            text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            return text

        except Exception as e:

            return f"OCR error: {str(e)}"

    except Exception as e:

        return f"Image processing error: {str(e)}"


# =========================================================
# GENERAL FILE EXTRACTION
# =========================================================

def extract_uploaded_text(uploaded_file):

    if not uploaded_file:
        return ""

    file_name = uploaded_file.name.lower()

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if file_name.endswith(".pdf"):

        return extract_text_from_pdf(uploaded_file)

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if file_name.endswith(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff"
        )
    ):

        return extract_text_from_image(uploaded_file)

    # -----------------------------------------------------
    # TEXT FILES
    # -----------------------------------------------------

    if file_name.endswith(
        (
            ".txt",
            ".csv",
            ".log"
        )
    ):

        try:

            raw = uploaded_file.read()

            for encoding in [
                "utf-8",
                "utf-8-sig",
                "cp1252",
                "latin-1"
            ]:

                try:
                    return raw.decode(encoding)
                except Exception:
                    continue

            return raw.decode("utf-8", errors="ignore")

        except Exception as e:

            return f"Text file extraction error: {str(e)}"

    return (
        "Unsupported file format. "
        "Use PDF, JPG, JPEG, PNG, WEBP, BMP, TIFF, TXT, CSV or LOG."
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
You are a senior Indian criminal-law research and investigation
assistant supporting police officers.

Your response MUST be in clear Telugu.

Use legal terminology accurately.

Do NOT hallucinate facts.

You must distinguish:
- facts stated in complaint,
- reasonable investigative possibilities,
- facts requiring verification.

Never present an unverified fact as established fact.

{LEGAL_REFERENCE}


=========================================================
DATE RULE
=========================================================

The incident/occurrence date must be identified carefully.

If the complaint contains both:
- an explicit date, and
- a relative expression such as "గత వారం", "నిన్న",
  "last week", "yesterday",

THE EXPLICIT DATE HAS PRIORITY.

Example:
"10 September 2026 జరిగిన విషయం, గత వారం..." 
=> occurrence date must be 10-09-2026 if context supports it.

Never allow "గత వారం" to override an explicit occurrence date.

Distinguish:
- occurrence date,
- complaint/report date,
- call date,
- payment date,
- discovery date.

Do not confuse them.


=========================================================
LEGAL SECTION RULES
=========================================================

BNS 318(4):
Do not select merely because money was lost.

BNS 319:
Do not select merely because a person called and claimed to be
a company/app/bank representative.
There must be personation facts.

IT Act 66C:
Require use of another person's electronic signature/password/
unique identification feature.

IT Act 66D:
Require personation + computer resource/communication device.

Do not automatically apply both 66C and 66D.

Do not invent sections merely because the incident involved
a mobile phone, internet, app, UPI or website.


=========================================================
COGNIZABLE / BAILABLE RULE
=========================================================

Use the exact BNSS First Schedule classification only.

Do not say:
"generally cognizable"
"generally bailable"
"may be non-bailable"

when an exact subsection has been selected.

For:
318(2) = Non-cognizable, Bailable, Any Magistrate
318(3) = Non-cognizable, Bailable, Any Magistrate
318(4) = Cognizable, Non-bailable, Magistrate First Class
319(2) = Cognizable, Bailable, Any Magistrate


=========================================================
EVIDENCE RULE
=========================================================

Do not invent evidence.

If complaint mentions:
- call,
- SMS,
- WhatsApp,
- bank transaction,
- UPI,
- app,
- email,
- CCTV,

then analyse it.

If it is NOT mentioned:
write:
"Complaintలో ఈ evidence ప్రస్తావన లేదు; availability ఉన్నదా
అని verify చేయాలి."

Do not state that CCTV/WhatsApp/GPS exists unless complaint says so.


=========================================================
BSA SECTION 63
=========================================================

Explain Section 63 as electronic-record admissibility provision.

Do not say every digital record automatically requires a certificate.

Explain that where electronic record is sought to be admitted
by virtue of Section 63, the statutory certificate requirement
under Section 63(4) must be considered.

Do not automatically say:
"Telecom officer will issue it"
or
"bank manager will issue it"
or
"forensic lab will issue it".

Instead identify:
source/device/system,
lawful control,
production method,
hash/details where relevant,
and state that the exact certificate source/issuer requires
verification based on the record and applicable law.


=========================================================
BNSS RULE
=========================================================

Do not use BNSS 173 as a generic CDR provision.

For CDR/IPDR:
say:
"CDR/IPDRను సంబంధిత telecom/service provider వద్ద applicable
lawful investigative/requisition process ద్వారా obtain చేయాలి."

For bank records:
identify bank transaction statement, beneficiary details,
UTR/RRN, account/KYC details subject to lawful process.

For app/platform records:
identify account/device/IP/login/payment records where relevant,
but do not claim they exist unless verified.


=========================================================
OUTPUT FORMAT
=========================================================

Use exactly these headings:

1. సంఘటన సారాంశం

2. సంఘటన తేదీ

3. Applicable Legal Framework

4. Primary Offence

5. Additional / Alternative Sections

6. Automatically NOT Applicable Sections

7. Cognizable / Bailable / Court Classification

8. Digital Evidence

9. BSA Section 63 Analysis

10. Investigation Plan

11. Documents / Records to Obtain

12. Witnesses

13. Missing Facts Requiring Verification

14. Final Legal View

15. Important Disclaimer


=========================================================
TABLE RULE
=========================================================

Where useful use markdown tables.

For legal sections include:
Section
Reason
Why applicable / not applicable
Classification if established


=========================================================
INVESTIGATION PLAN
=========================================================

Keep it practical.

Possible items may include, only when relevant:
- victim statement
- bank statement
- UTR/RRN
- beneficiary account details
- KYC details
- transaction timestamps
- mobile number details
- CDR/IPDR
- device information
- app/package information
- URLs/domains
- screenshots
- call recordings
- SMS
- WhatsApp/chat
- email headers
- CCTV
- platform records
- seizure/forensic preservation

But do not claim any item exists unless complaint confirms it.


=========================================================
STYLE
=========================================================

Use clear Telugu.

Keep English legal section names where useful.

Do not produce fake FIR numbers,
fake case numbers,
fake dates,
fake police station names,
fake accused names,
fake evidence,
fake court orders,
fake citations.

If information is insufficient, clearly say:
"ధృవీకరించాలి."

Do not overstate conclusions.
"""


# =========================================================
# BUILD USER PROMPT
# =========================================================

def build_user_prompt(
    complaint_text,
    extracted_text,
    reference_date,
    incident_date,
    date_source,
    framework,
    transitional
):

    combined_text = ""

    if complaint_text:
        combined_text += (
            "\n\n===== USER ENTERED COMPLAINT =====\n"
            + complaint_text
        )

    if extracted_text:
        combined_text += (
            "\n\n===== UPLOADED FILE / OCR TEXT =====\n"
            + extracted_text
        )

    if incident_date:

        detected_date_text = incident_date.strftime(
            "%d-%m-%Y"
        )

    else:

        detected_date_text = "Not detected"

    return f"""
Analyze the following police complaint/case information.

REFERENCE DATE:
{reference_date.strftime("%d-%m-%Y")}

PROGRAMMATICALLY DETECTED INCIDENT DATE:
{detected_date_text}

DATE SOURCE:
{date_source}

PROGRAMMATICALLY SELECTED LEGAL FRAMEWORK:
{framework}

TRANSITIONAL / PRE-01-07-2024 REVIEW:
{"YES" if transitional else "NO"}

IMPORTANT:
The programmatically detected explicit date should be respected
unless the complaint context clearly proves that the date refers
to some other event such as complaint date, call date, payment date,
or discovery date.

If multiple dates are present, distinguish each date.

{combined_text}

Now prepare the complete Telugu legal and investigation report
using the required 15-section format.

Do not invent facts.
Do not automatically apply BNS 318(4), BNS 319, IT Act 66C or
IT Act 66D.
"""


# =========================================================
# GROQ ANALYSIS
# =========================================================

def investigate_case(
    complaint_text,
    extracted_text,
    reference_date,
    incident_date,
    date_source,
    framework,
    transitional
):

    client = get_groq_client()

    user_prompt = build_user_prompt(
        complaint_text=complaint_text,
        extracted_text=extracted_text,
        reference_date=reference_date,
        incident_date=incident_date,
        date_source=date_source,
        framework=framework,
        transitional=transitional
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

            max_tokens=7000
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "❌ Groq API Error\n\n"
            + str(e)
        )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

def make_download_report(
    complaint,
    incident_date,
    framework,
    analysis
):

    date_text = (
        incident_date.strftime("%d-%m-%Y")
        if incident_date
        else "Not detected"
    )

    report = f"""
POLICE LEGAL & INVESTIGATION ASSISTANT
======================================

Incident Date:
{date_text}

Legal Framework:
{framework}

Complaint:
{complaint}

======================================
LEGAL ANALYSIS
======================================

{analysis}

======================================
DISCLAIMER
======================================

This report is an AI-assisted research/investigation support
document. It is not a substitute for statutory verification,
case-specific legal advice, supervisory review, or court
determination.
"""

    return report


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Settings")

    st.write(
        f"**Model:** `{MODEL_NAME}`"
    )

    st.write(
        "**Legal framework:** BNS / BNSS / BSA"
    )

    st.write(
        "**OCR:** "
        + ("Available" if OCR_AVAILABLE else "Not available")
    )

    st.write(
        "**PDF:** "
        + ("Available" if PDF_AVAILABLE else "Not available")
    )

    st.divider()

    st.info(
        "Explicit incident date is given priority over "
        "relative expressions such as 'గత వారం'."
    )


# =========================================================
# INPUT SECTION
# =========================================================

st.subheader("📝 Complaint / Case Details")

complaint_text = st.text_area(
    "Complaint వివరాలు ఇక్కడ paste చేయండి",
    height=260,
    placeholder=(
        "ఉదా:\n"
        "10 September 2026న ఒక వ్యక్తి phone చేసి...\n"
        "రూ.45,000 debit అయ్యింది..."
    )
)


# =========================================================
# REFERENCE DATE
# =========================================================

reference_date = st.date_input(
    "📅 Reference Date",
    value=date.today()
)


# =========================================================
# TRANSITIONAL CHECK
# =========================================================

transitional_review = st.checkbox(
    "⚠️ Transitional / savings provisions కూడా review చేయాలి",
    value=False
)


# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader("📷 Photo / 📄 PDF / Text Upload")

uploaded_file = st.file_uploader(
    "Complaint photo / PDF / text file upload చేయండి",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp",
        "tif",
        "tiff",
        "pdf",
        "txt",
        "csv",
        "log"
    ]
)


# =========================================================
# EXTRACT FILE TEXT
# =========================================================

extracted_text = ""

if uploaded_file:

    with st.spinner("📄 File / OCR text extract చేస్తున్నాను..."):

        extracted_text = extract_uploaded_text(
            uploaded_file
        )

    if extracted_text:

        with st.expander(
            "🔎 Extracted / OCR Text చూడండి",
            expanded=False
        ):

            st.text_area(
                "Extracted Text",
                extracted_text,
                height=300
            )


# =========================================================
# COMBINED TEXT FOR DATE DETECTION
# =========================================================

combined_input_text = ""

if complaint_text:
    combined_input_text += complaint_text

if extracted_text:
    combined_input_text += "\n\n" + extracted_text


# =========================================================
# INCIDENT DATE DETECTION
# =========================================================

incident_date, date_source = extract_incident_date(
    combined_input_text,
    reference_date
)


# =========================================================
# LEGAL FRAMEWORK
# =========================================================

framework, transitional = determine_framework(
    incident_date
)

if transitional_review:
    transitional = True


# =========================================================
# DATE DISPLAY
# =========================================================

st.subheader("📅 సంఘటన తేదీ గుర్తింపు")

if incident_date:

    st.success(
        f"✅ Incident / Occurrence Date: "
        f"**{incident_date.strftime('%d-%m-%Y')}**"
    )

    st.caption(
        f"Source: {date_source}"
    )

else:

    st.warning(
        "⚠️ Incident / occurrence date గుర్తించబడలేదు. "
        "Legal framework automaticగా fix చేయడం సాధ్యం కాదు."
    )


# =========================================================
# FRAMEWORK DISPLAY
# =========================================================

st.subheader("⚖️ Legal Framework")

if incident_date:

    if incident_date >= NEW_LAW_DATE:

        st.success(
            "BNS 2023 + BNSS 2023 + BSA 2023"
        )

    else:

        st.warning(
            "Pre-01-07-2024 framework: "
            "IPC + CrPC + Indian Evidence Act "
            "(savings/transitional provisions review required)"
        )

else:

    st.info(
        "Incident date verify చేసిన తర్వాత legal framework "
        "finalize చేయాలి."
    )


# =========================================================
# DEBUG INFORMATION
# =========================================================

with st.expander("🛠️ Debug / Date Detection Details"):

    st.write(
        "**Reference Date:**",
        reference_date.strftime("%d-%m-%Y")
    )

    st.write(
        "**Detected Incident Date:**",
        (
            incident_date.strftime("%d-%m-%Y")
            if incident_date
            else "Not detected"
        )
    )

    st.write(
        "**Detection Source:**",
        date_source
    )

    st.write(
        "**Framework:**",
        framework
    )

    st.write(
        "**Transitional Review:**",
        transitional
    )


# =========================================================
# ANALYZE BUTTON
# =========================================================

st.divider()

analyze_button = st.button(
    "⚖️ Legal Analysis Generate చేయండి",
    type="primary",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyze_button:

    if not complaint_text.strip() and not extracted_text.strip():

        st.error(
            "❌ Complaint text లేదా uploaded file అవసరం."
        )

        st.stop()

    if not incident_date:

        st.warning(
            "⚠️ Incident date automaticగా గుర్తించబడలేదు. "
            "AI analysis కొనసాగుతుంది, కానీ legal framework "
            "date-basedగా final చేయకుండా verificationగా చూపబడుతుంది."
        )

    with st.spinner(
        "⚖️ BNS / BNSS / BSA ఆధారంగా legal analysis చేస్తున్నాను..."
    ):

        analysis = investigate_case(

            complaint_text=complaint_text,

            extracted_text=extracted_text,

            reference_date=reference_date,

            incident_date=incident_date,

            date_source=date_source,

            framework=framework,

            transitional=transitional
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    st.subheader("📋 Legal Analysis Result")

    st.markdown(analysis)

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    report_text = make_download_report(

        complaint=(
            complaint_text
            if complaint_text
            else extracted_text
        ),

        incident_date=incident_date,

        framework=framework,

        analysis=analysis
    )

    st.download_button(

        label="📥 Report TXT Download",

        data=report_text,

        file_name=(
            "police_legal_investigation_report.txt"
        ),

        mime="text/plain",

        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "⚠️ AI-assisted legal/investigation support only. "
    "Statutory text, current amendments, case facts and "
    "supervisory/legal review must be independently verified."
)
