import os
import re
from datetime import datetime, date, timedelta

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
st.caption(
    "BNS / BNSS / BSA + IPC / CrPC / Indian Evidence Act"
)


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
        "❌ GROQ_API_KEY కనబడలేదు.\n\n"
        "Streamlit → Settings → Secrets లో GROQ_API_KEY పెట్టండి."
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


# =========================================================
# MODEL
# =========================================================

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
# TELUGU MONTHS
# =========================================================

TELUGU_MONTHS = {

    "జనవరి": 1,

    "ఫిబ్రవరి": 2,

    "మార్చి": 3,

    "ఏప్రిల్": 4,

    "మే": 5,

    "జూన్": 6,

    "జూలై": 7,

    "ఆగస్టు": 8,

    "సెప్టెంబర్": 9,
    "సెప్టెంబరు": 9,

    "అక్టోబర్": 10,
    "అక్టోబరు": 10,

    "నవంబర్": 11,
    "నవంబరు": 11,

    "డిసెంబర్": 12,
    "డిసెంబరు": 12,
}


# =========================================================
# ENGLISH MONTHS
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
    "dec": 12,
}


# =========================================================
# NUMERIC DATE PARSER
# =========================================================

def parse_date_string(value):
    """
    Supports:

    10-09-2026
    10/09/2026
    10.09.2026
    2026-09-10
    10-09-26
    """

    if not value:
        return None

    value = str(value).strip()

    formats = [

        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",

        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",

        "%d-%m-%y",
        "%d/%m/%y",
        "%d.%m.%y",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt
            ).date()

        except ValueError:
            continue

    return None


# =========================================================
# NAMED MONTH DATE PARSER
# =========================================================

def parse_named_month_date(text):

    if not text:
        return None

    text = str(text).strip()


    # -----------------------------------------------------
    # TELUGU
    #
    # 10 సెప్టెంబర్ 2026
    # 10 సెప్టెంబరు 2026
    # -----------------------------------------------------

    for month_name, month_number in TELUGU_MONTHS.items():

        pattern = (
            rf"(\d{{1,2}})"
            rf"\s*"
            rf"{re.escape(month_name)}"
            rf"\s*"
            rf"(\d{{4}})"
        )

        match = re.search(
            pattern,
            text
        )

        if match:

            day = int(match.group(1))
            year = int(match.group(2))

            try:

                return date(
                    year,
                    month_number,
                    day
                )

            except ValueError:

                return None


    # -----------------------------------------------------
    # ENGLISH
    #
    # 10 September 2026
    # 10th September 2026
    # -----------------------------------------------------

    for month_name, month_number in ENGLISH_MONTHS.items():

        pattern = (
            rf"\b(\d{{1,2}})"
            rf"(?:st|nd|rd|th)?"
            rf"\s+"
            rf"{re.escape(month_name)}"
            rf"\s*,?\s*"
            rf"(\d{{4}})\b"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            day = int(match.group(1))
            year = int(match.group(2))

            try:

                return date(
                    year,
                    month_number,
                    day
                )

            except ValueError:

                return None


    # -----------------------------------------------------
    # ENGLISH
    #
    # September 10, 2026
    # -----------------------------------------------------

    for month_name, month_number in ENGLISH_MONTHS.items():

        pattern = (
            rf"\b{re.escape(month_name)}"
            rf"\s+"
            rf"(\d{{1,2}})"
            rf"(?:st|nd|rd|th)?"
            rf"\s*,?\s*"
            rf"(\d{{4}})\b"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            day = int(match.group(1))
            year = int(match.group(2))

            try:

                return date(
                    year,
                    month_number,
                    day
                )

            except ValueError:

                return None


    return None


# =========================================================
# RELATIVE DATE DETECTION
# =========================================================

def extract_relative_date(text, reference_date):

    if not text:
        return None

    if reference_date is None:
        return None

    text_lower = text.lower()


    # -----------------------------------------------------
    # TELUGU TODAY
    # -----------------------------------------------------

    today_words = [
        "నేడు",
        "ఈరోజు",
        "ఈ రోజు",
        "ఇవాళ",
    ]

    for word in today_words:

        if word in text:

            return {
                "date": reference_date,
                "type": "exact",
                "description": "ఈరోజు / నేడు"
            }


    # -----------------------------------------------------
    # TELUGU YESTERDAY
    # -----------------------------------------------------

    yesterday_words = [
        "నిన్న",
        "నిన్నటి రోజు",
    ]

    for word in yesterday_words:

        if word in text:

            result_date = (
                reference_date -
                timedelta(days=1)
            )

            return {
                "date": result_date,
                "type": "exact",
                "description": "నిన్న"
            }


    # -----------------------------------------------------
    # ENGLISH TODAY
    # -----------------------------------------------------

    if re.search(
        r"\btoday\b",
        text_lower
    ):

        return {
            "date": reference_date,
            "type": "exact",
            "description": "today"
        }


    # -----------------------------------------------------
    # ENGLISH YESTERDAY
    # -----------------------------------------------------

    if re.search(
        r"\byesterday\b",
        text_lower
    ):

        result_date = (
            reference_date -
            timedelta(days=1)
        )

        return {
            "date": result_date,
            "type": "exact",
            "description": "yesterday"
        }


    # -----------------------------------------------------
    # LAST WEEK
    #
    # DO NOT GUESS ONE PARTICULAR DAY.
    # Return a range.
    # -----------------------------------------------------

    last_week_words = [
        "గత వారం",
        "గత వారంలో",
        "last week"
    ]

    for word in last_week_words:

        if word.lower() in text_lower:

            current_week_start = (
                reference_date -
                timedelta(
                    days=reference_date.weekday()
                )
            )

            previous_week_start = (
                current_week_start -
                timedelta(days=7)
            )

            previous_week_end = (
                current_week_start -
                timedelta(days=1)
            )

            return {
                "date": None,
                "type": "range",
                "start": previous_week_start,
                "end": previous_week_end,
                "description": word
            }


    return None


# =========================================================
# MAIN INCIDENT DATE EXTRACTION
# =========================================================

def extract_incident_date(
    text,
    reference_date=None
):

    """
    Returns dictionary:

    {
        "date": date object,
        "type": "exact",
        "source": "..."
    }

    OR

    {
        "type": "range",
        "start": date,
        "end": date
    }

    IMPORTANT:

    FIR date / complaint date should NOT automatically
    become incident date.
    """

    if not text:
        return None

    text = str(text)

    lines = text.splitlines()


    # =====================================================
    # STEP 1
    # EXPLICIT INCIDENT/OCCURRENCE/OFFENCE DATE
    # =====================================================

    explicit_keywords = [

        "incident date",
        "date of incident",

        "offence date",
        "date of offence",

        "offense date",
        "date of offense",

        "occurrence date",
        "date of occurrence",

        "incident",
        "occurrence",

        "సంఘటన తేదీ",
        "సంఘటన జరిగిన తేదీ",

        "నేరం జరిగిన తేదీ",
        "నేర తేదీ",

        "ఘటన తేదీ",
        "ఘటన జరిగిన తేదీ",

        "జరిగిన తేదీ",
    ]


    for line in lines:

        lower_line = line.lower()

        found_keyword = False

        for keyword in explicit_keywords:

            if keyword.lower() in lower_line:

                found_keyword = True
                break


        if not found_keyword:
            continue


        # -------------------------------------------------
        # Telugu / English named month
        # -------------------------------------------------

        parsed = parse_named_month_date(line)

        if parsed:

            return {
                "date": parsed,
                "type": "exact",
                "source": "explicit incident date"
            }


        # -------------------------------------------------
        # Numeric date
        # -------------------------------------------------

        numeric_match = re.search(
            r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b",
            line
        )

        if numeric_match:

            parsed = parse_date_string(
                numeric_match.group(0)
            )

            if parsed:

                return {
                    "date": parsed,
                    "type": "exact",
                    "source": "explicit incident date"
                }


    # =====================================================
    # STEP 2
    # DATE RANGE
    #
    # 28-05-2017 23:30 to 29-05-2017 06:00
    # =====================================================

    range_pattern = (
        r"\b"
        r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})"
        r"(?:\s+\d{1,2}[:.]\d{2})?"
        r"\s*"
        r"(?:to|-|until|వరకు)"
        r"\s*"
        r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})"
    )

    range_match = re.search(
        range_pattern,
        text,
        re.IGNORECASE
    )

    if range_match:

        start_date = parse_date_string(
            range_match.group(1)
        )

        end_date = parse_date_string(
            range_match.group(2)
        )

        if start_date and end_date:

            return {
                "date": start_date,
                "type": "range",
                "start": start_date,
                "end": end_date,
                "source": "incident date range"
            }


    # =====================================================
    # STEP 3
    # NAMED MONTH DATE ANYWHERE
    # =====================================================

    parsed = parse_named_month_date(text)

    if parsed:

        return {
            "date": parsed,
            "type": "exact",
            "source": "named month date"
        }


    # =====================================================
    # STEP 4
    # INCIDENT-RELATED LINE + NUMERIC DATE
    # =====================================================

    incident_words = [

        "incident",
        "offence",
        "offense",
        "occurrence",
        "crime",

        "సంఘటన",
        "ఘటన",
        "నేరం",
        "జరిగిన",
    ]


    for line in lines:

        lower_line = line.lower()

        if any(
            word.lower() in lower_line
            for word in incident_words
        ):

            numeric_match = re.search(
                r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b",
                line
            )

            if numeric_match:

                parsed = parse_date_string(
                    numeric_match.group(0)
                )

                if parsed:

                    return {
                        "date": parsed,
                        "type": "exact",
                        "source": "incident-related line"
                    }


    # =====================================================
    # STEP 5
    # RELATIVE DATE
    # =====================================================

    relative_result = extract_relative_date(
        text,
        reference_date
    )

    if relative_result:

        return relative_result


    # =====================================================
    # STEP 6
    # NO DATE FOUND
    # =====================================================

    return None


# =========================================================
# LAW SELECTION
# =========================================================

def select_law(
    incident_info,
    old_case_pending=False
):

    if incident_info is None:

        return {
            "status": "UNKNOWN",
            "framework": "DATE_REQUIRED",
            "reason": (
                "Incident/offence date could not be identified."
            )
        }


    # -----------------------------------------------------
    # Relative range
    # -----------------------------------------------------

    if incident_info.get("type") == "range":

        start_date = incident_info["start"]
        end_date = incident_info["end"]

        if end_date < NEW_LAW_DATE:

            return {
                "status": "OLD_RANGE",
                "framework": (
                    "IPC / CrPC / "
                    "INDIAN EVIDENCE ACT"
                ),
                "reason": (
                    "The stated incident period is before "
                    "01-07-2024."
                )
            }

        elif start_date >= NEW_LAW_DATE:

            return {
                "status": "NEW_RANGE",
                "framework": "BNS / BNSS / BSA",
                "reason": (
                    "The stated incident period is on/after "
                    "01-07-2024."
                )
            }

        else:

            return {
                "status": "CROSS_TRANSITION",
                "framework": "DATE_REVIEW_REQUIRED",
                "reason": (
                    "The incident period crosses "
                    "01-07-2024. Exact dates and legal "
                    "transition provisions must be reviewed."
                )
            }


    # -----------------------------------------------------
    # Exact date
    # -----------------------------------------------------

    incident_date = incident_info["date"]


    # -----------------------------------------------------
    # Old pending proceeding
    # -----------------------------------------------------

    if old_case_pending:

        return {
            "status": "OLD_PENDING",
            "framework": (
                "IPC / CrPC / "
                "INDIAN EVIDENCE ACT"
            ),
            "reason": (
                "The proceeding is stated to have been "
                "pending before 01-07-2024. Repeal-and-"
                "savings / transitional provisions must "
                "also be considered."
            )
        }


    # -----------------------------------------------------
    # Before 01-07-2024
    # -----------------------------------------------------

    if incident_date < NEW_LAW_DATE:

        return {
            "status": "OLD",
            "framework": (
                "IPC / CrPC / "
                "INDIAN EVIDENCE ACT"
            ),
            "reason": (
                f"Incident date "
                f"{incident_date.strftime('%d-%m-%Y')} "
                f"is before 01-07-2024."
            )
        }


    # -----------------------------------------------------
    # On / after 01-07-2024
    # -----------------------------------------------------

    return {
        "status": "NEW",
        "framework": "BNS / BNSS / BSA",
        "reason": (
            f"Incident date "
            f"{incident_date.strftime('%d-%m-%Y')} "
            f"is on/after 01-07-2024."
        )
    }


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(uploaded_file):

    if not PDF_AVAILABLE:

        return (
            "PDF reader library (pypdf) installed లేదు. "
            "requirements.txtలో pypdf పెట్టండి."
        )


    try:

        uploaded_file.seek(0)

        reader = PdfReader(
            uploaded_file
        )

        pages = []


        for page in reader.pages:

            try:

                page_text = page.extract_text()

                if page_text:

                    pages.append(
                        page_text
                    )

            except Exception:

                continue


        text = "\n".join(
            pages
        ).strip()


        if text:

            return text


        return (
            "PDFలో selectable text కనిపించలేదు. "
            "ఇది scanned PDF కావచ్చు."
        )


    except Exception as e:

        return f"PDF చదవడంలో సమస్య: {e}"


# =========================================================
# IMAGE OCR
# =========================================================

def extract_image_text(uploaded_file):

    if not OCR_AVAILABLE:

        return (
            "OCR library (pytesseract) అందుబాటులో లేదు."
        )


    try:

        image = Image.open(
            uploaded_file
        )


        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )


        if text.strip():

            return text.strip()


        return (
            "Image నుంచి text గుర్తించలేకపోయింది. "
            "Telugu handwriting అయితే OCR accuracy "
            "తక్కువగా ఉండవచ్చు."
        )


    except Exception as e:

        return f"Image OCRలో సమస్య: {e}"


# =========================================================
# FILE EXTRACTION
# =========================================================

def extract_uploaded_file(
    uploaded_file
):

    if uploaded_file is None:

        return ""


    filename = (
        uploaded_file.name.lower()
    )


    # -----------------------------------------------------
    # TXT
    # -----------------------------------------------------

    if filename.endswith(".txt"):

        try:

            uploaded_file.seek(0)

            return uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

        except Exception as e:

            return f"TXT చదవడంలో సమస్య: {e}"


    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if filename.endswith(".pdf"):

        return extract_pdf_text(
            uploaded_file
        )


    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if filename.endswith(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp"
        )
    ):

        return extract_image_text(
            uploaded_file
        )


    return (
        "ఈ file format ప్రస్తుతం support చేయబడలేదు."
    )


# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = r"""
You are a careful Indian criminal-law research and investigation
assistant for police investigation support.

Your job is NOT to blindly assign BNS/BNSS/BSA sections.

=========================================================
1. DATE OF OFFENCE IS THE FIRST STEP
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
applicable when the offence was committed, subject to repeal,
savings and transitional provisions.

For an old proceeding already pending when the new laws came into
force, separately consider the applicable repeal-and-savings
provisions.

For an offence occurring ON or AFTER 01-07-2024:

Use:

- BNS for offences and punishments
- BNSS for criminal procedure
- BSA for evidence


=========================================================
2. DATE TYPES MUST BE DISTINGUISHED
=========================================================

Always distinguish:

- Incident / occurrence date
- Offence date
- Complaint date
- FIR date
- Investigation date
- Arrest date
- Charge-sheet date
- Trial date
- Date on which proceeding became pending

Never assume FIR date = incident date.

Never assume report-generation date = incident date.


=========================================================
3. TELUGU DATES
=========================================================

Understand Telugu date expressions such as:

- 10 సెప్టెంబర్ 2026
- 10 సెప్టెంబరు 2026
- 10 అక్టోబర్ 2026
- 10-09-2026
- 10/09/2026
- 10.09.2026
- నిన్న
- నేడు
- ఈరోజు
- ఇవాళ
- గత వారం

For relative dates, use the stated complaint/report reference date
when available.

Do NOT invent an exact day from "గత వారం".

If only "గత వారం" is stated, treat it as a date range and explain
that the exact occurrence date should be verified.


=========================================================
4. OLD CASES
=========================================================

For incidents before 01-07-2024:

Primary historical framework:

- Indian Penal Code, 1860 (IPC)
- Code of Criminal Procedure, 1973 (CrPC)
- Indian Evidence Act, 1872 (IEA)

Do NOT rewrite an old FIR into BNS/BNSS/BSA merely because the report
is being prepared today.

Example:

Incident Date: 28-05-2017

Do NOT say:

"BNS 305 applies."

Instead identify the applicable historical IPC provision and explain
the transition/repeal-and-savings issue where relevant.


=========================================================
5. NEW CASES
=========================================================

For incidents on or after 01-07-2024:

Use:

BNS = substantive offence and punishment

BNSS = FIR, investigation, arrest, search, seizure, witnesses,
       remand, case diary and final report

BSA = evidence and electronic/digital evidence


=========================================================
6. SECTION ACCURACY
=========================================================

NEVER invent section numbers.

Before mentioning a section:

1. Identify the Act.
2. Identify the exact section.
3. Explain what the section actually covers.
4. Do not use a section simply because it sounds relevant.

If uncertain:

"VERIFY FROM OFFICIAL TEXT."


=========================================================
7. SEARCH / SEIZURE
=========================================================

Do not confuse:

- investigation
- search
- search warrant
- seizure
- arrest
- notice to appear
- production before Magistrate
- remand

Do not automatically state that every police search requires a
Magistrate search warrant.

Identify the actual statutory basis.


=========================================================
8. WITNESSES
=========================================================

Do not invent a mandatory number of panch witnesses.

Do not say "exactly 2" or "exactly 3" unless the actual law requires
that number.

Distinguish:

- complainant
- eyewitness
- circumstantial witness
- seizure witness
- independent witness
- police witness
- expert witness


=========================================================
9. DIGITAL EVIDENCE
=========================================================

Do not automatically apply every BSA provision to every:

- mobile phone
- SIM
- CCTV
- screenshot
- WhatsApp message
- CDR
- photograph

First identify:

- What is the evidence?
- Physical or electronic?
- Who produced it?
- How was it obtained?
- Is authenticity disputed?
- What proof/admissibility requirement applies?

A mobile phone may be physical evidence.

CDR/CCTV/chat data may constitute electronic/digital records.

Do not automatically state that every screenshot requires the same
certificate.

Do not automatically state that only a forensic expert can issue an
electronic-record certificate.

Analyse the actual record and mode of production.


=========================================================
10. ARREST
=========================================================

Do not recommend arrest merely because an offence is cognizable.

Consider:

- cognizable/non-cognizable
- bailable/non-bailable
- necessity of arrest
- statutory conditions
- identification
- evidence
- absconding risk
- cooperation
- safeguards


=========================================================
11. BAIL
=========================================================

Clearly distinguish:

- bailable
- non-bailable
- regular bail
- anticipatory bail
- default/statutory bail where applicable

Do not guess.


=========================================================
12. PUNISHMENT
=========================================================

State punishment accurately.

Do not invent:

- minimum imprisonment
- maximum imprisonment
- fine
- classification
- trial court


=========================================================
13. TRIAL COURT
=========================================================

Do not automatically say Sessions Court.

Check the applicable classification and state the appropriate court.


=========================================================
14. NO FABRICATION
=========================================================

Never invent:

- FIR number
- police station
- officer name
- accused identity
- dates
- witnesses
- section numbers
- court orders
- forensic results
- recoveries

If missing:

"Not provided."


=========================================================
15. REPORT FORMAT
=========================================================

Generate:

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
17. IDENTIFICATION / TEST IDENTIFICATION
18. CASE DIARY / INVESTIGATION RECORD
19. FINAL REPORT / CHARGE SHEET
20. INVESTIGATION OFFICER CHECKLIST
21. LEGAL CAUTIONS / ITEMS TO VERIFY


=========================================================
16. DATE WARNING
=========================================================

If pre-01-07-2024:

"OLD-LAW CASE:
IPC / CrPC / Indian Evidence Act framework applies subject to
repeal-and-savings/transitional provisions."

If on/after 01-07-2024:

"NEW-LAW CASE:
BNS / BNSS / BSA framework applies."

If date is unclear:

"Incident/offence date must be verified before selecting the legal
framework."


=========================================================
17. FINAL LEGAL CAUTION
=========================================================

This is an investigation-support and legal research tool.

Final legal action must be verified against:

- official statute
- applicable notifications
- court orders
- prosecution/legal opinion
- actual case facts
"""


# =========================================================
# BUILD USER PROMPT
# =========================================================

def build_user_prompt(
    case_text,
    law_info,
    incident_info,
    reference_date,
    old_pending
):

    # -----------------------------------------------------
    # Incident date text
    # -----------------------------------------------------

    if incident_info is None:

        incident_date_text = "NOT IDENTIFIED"

    elif incident_info.get("type") == "range":

        incident_date_text = (
            f"{incident_info['start'].strftime('%d-%m-%Y')}"
            f" to "
            f"{incident_info['end'].strftime('%d-%m-%Y')}"
        )

    else:

        incident_date_text = (
            incident_info["date"].strftime(
                "%d-%m-%Y"
            )
        )


    # -----------------------------------------------------
    # Reference date
    # -----------------------------------------------------

    if reference_date:

        reference_text = (
            reference_date.strftime(
                "%d-%m-%Y"
            )
        )

    else:

        reference_text = "Not provided"


    # -----------------------------------------------------
    # Pending status
    # -----------------------------------------------------

    pending_text = (
        "Yes"
        if old_pending
        else
        "No / not stated"
    )


    return f"""
Analyse the following police complaint/case.

=========================================================
DATE INFORMATION
=========================================================

Detected Incident / Offence Date:
{incident_date_text}

Reference / Complaint Date:
{reference_text}

01-07-2024 Transition Date:
01-07-2024

Old proceeding pending before 01-07-2024:
{pending_text}

Selected Primary Legal Framework:
{law_info["framework"]}

Reason:
{law_info["reason"]}


=========================================================
CASE MATERIAL
=========================================================

{case_text}


=========================================================
MANDATORY INSTRUCTIONS
=========================================================

1. First state the incident/offence date.

2. State the applicable legal framework.

3. Explain why that framework applies.

4. Do not substitute BNS/BNSS/BSA for a pre-01-07-2024 occurrence.

5. If this is an old pending proceeding, separately discuss
   repeal-and-savings/transitional provisions.

6. Do not guess section numbers.

7. Do not fabricate facts.

8. Distinguish incident date from FIR/complaint date.

9. Distinguish physical evidence from electronic evidence.

10. Do not automatically require an electronic-record certificate
    for every digital item.

11. Give practical investigation steps.

12. Give an IO checklist.

13. Clearly identify assumptions.

14. If exact legal provision requires verification, mark it:
    "VERIFY FROM OFFICIAL TEXT."

15. For relative dates such as "గత వారం", do not invent an exact
    occurrence date. State the date range and request verification
    of the exact date.
"""


# =========================================================
# GROQ ANALYSIS
# =========================================================

def investigate_case(
    case_text,
    law_info,
    incident_info,
    reference_date,
    old_pending
):

    user_prompt = build_user_prompt(
        case_text,
        law_info,
        incident_info,
        reference_date,
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
            "❌ AI legal analysisలో error వచ్చింది.\n\n"
            f"Error: {e}"
        )


# =========================================================
# CASE DETAILS
# =========================================================

st.subheader("📝 కేసు / ఫిర్యాదు వివరాలు")


case_text = st.text_area(

    "కేసు వివరాలు / FIR / Complaint ఇక్కడ paste చేయండి",

    height=350,

    placeholder=(
        "ఉదాహరణ:\n\n"
        "నేను పైన పేర్కొన్న చిరునామాలో నివసిస్తున్నాను.\n"
        "10 సెప్టెంబర్ 2026న జరిగిన ఒక మోసం సంఘటనపై...\n"
        "మధ్యాహ్నం సుమారు 2:30 గంటలకు..."
    )
)


# =========================================================
# REFERENCE DATE
# =========================================================

st.subheader("📅 Complaint / Reference Date")

st.caption(
    "‘నిన్న’, ‘ఈరోజు’, ‘గత వారం’ వంటి relative dates ఉంటే "
    "ఈ తేదీని referenceగా ఉపయోగిస్తుంది."
)


reference_date = st.date_input(

    "ఫిర్యాదు / నివేదిక ఇచ్చిన తేదీ",

    value=date.today(),

    format="DD-MM-YYYY"
)


# =========================================================
# OLD PENDING OPTION
# =========================================================

st.subheader("⚖️ Old Pending Case Check")


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

    with st.spinner(
        "Document చదువుతోంది..."
    ):

        uploaded_text = extract_uploaded_file(
            uploaded_file
        )


    if uploaded_text:

        st.success(
            "✅ Document text తీసుకుంది."
        )


        with st.expander(
            "📄 Extracted Text చూడండి"
        ):

            st.text_area(
                "Extracted Text",
                uploaded_text,
                height=300
            )


# =========================================================
# COMBINE TEXT
# =========================================================

combined_text = (
    case_text.strip()
)


if uploaded_text.strip():

    if combined_text:

        combined_text += (
            "\n\n"
            "----- UPLOADED DOCUMENT -----"
            "\n\n"
        )


    combined_text += (
        uploaded_text.strip()
    )


# =========================================================
# DETECT INCIDENT DATE
# =========================================================

incident_info = extract_incident_date(

    combined_text,

    reference_date
)


# =========================================================
# LAW SELECTION
# =========================================================

law_info = select_law(

    incident_info,

    old_pending
)


# =========================================================
# SHOW DETECTED DATE
# =========================================================

if incident_info is None:

    st.warning(
        "⚠️ Incident / offence date గుర్తించబడలేదు."
    )

    st.info(
        "ఉదాహరణలు:\n"
        "• 10 సెప్టెంబర్ 2026న\n"
        "• 10 September 2026\n"
        "• 10-09-2026\n"
        "• 10/09/2026\n"
        "• నిన్న\n"
        "• ఈరోజు\n"
        "• గత వారం"
    )


elif incident_info.get("type") == "range":

    st.warning(
        "📅 Incident Date Range గుర్తించబడింది"
    )

    st.write(
        "**From:** "
        + incident_info["start"].strftime(
            "%d-%m-%Y"
        )
    )

    st.write(
        "**To:** "
        + incident_info["end"].strftime(
            "%d-%m-%Y"
        )
    )

    st.write(
        "**Source:** "
        + incident_info.get(
            "source",
            "date range"
        )
    )


else:

    detected_date = incident_info["date"]


    st.write(
        "**Detected Incident / Offence Date:** "
        + detected_date.strftime(
            "%d-%m-%Y"
        )
    )

    st.write(
        "**Date Source:** "
        + incident_info.get(
            "source",
            "detected date"
        )
    )


# =========================================================
# SHOW LAW
# =========================================================

if law_info["status"] in [
    "OLD",
    "OLD_RANGE",
    "OLD_PENDING"
]:

    st.warning(
        "⚠️ OLD-LAW CASE\n\n"
        "Applicable primary framework:\n"
        "IPC / CrPC / Indian Evidence Act"
    )


elif law_info["status"] in [
    "NEW",
    "NEW_RANGE"
]:

    st.success(
        "✅ NEW-LAW CASE\n\n"
        "Applicable primary framework:\n"
        "BNS / BNSS / BSA"
    )


elif law_info["status"] == "CROSS_TRANSITION":

    st.error(
        "⚠️ DATE TRANSITION CASE\n\n"
        "Incident period 01-07-2024ను cross చేస్తోంది. "
        "Exact occurrence date మరియు transitional provisions "
        "verify చేయాలి."
    )


# =========================================================
# ANALYSIS BUTTON
# =========================================================

if st.button(

    "⚖️ Legal Analysis ప్రారంభించండి",

    type="primary",

    use_container_width=True
):


    # -----------------------------------------------------
    # No input
    # -----------------------------------------------------

    if not combined_text.strip():

        st.error(
            "❌ ముందుగా case details లేదా document upload చేయండి."
        )


    # -----------------------------------------------------
    # No date
    # -----------------------------------------------------

    elif incident_info is None:

        st.error(
            "❌ Incident / offence date గుర్తించబడలేదు.\n\n"
            "దయచేసి complaintలో occurrence date స్పష్టంగా verify చేయండి."
        )


    # -----------------------------------------------------
    # Range crossing transition
    # -----------------------------------------------------

    elif law_info["status"] == "CROSS_TRANSITION":

        st.error(
            "❌ ఈ incident period 01-07-2024ను cross చేస్తోంది.\n\n"
            "Exact occurrence date లేకుండా automatic legal framework "
            "select చేయడం సురక్షితం కాదు."
        )


    # -----------------------------------------------------
    # START ANALYSIS
    # -----------------------------------------------------

    else:

        st.subheader(
            "🔎 Applicable Law"
        )


        if law_info["status"] in [
            "OLD",
            "OLD_RANGE",
            "OLD_PENDING"
        ]:

            st.warning(
                "IPC / CrPC / Indian Evidence Act"
            )


        elif law_info["status"] in [
            "NEW",
            "NEW_RANGE"
        ]:

            st.success(
                "BNS / BNSS / BSA"
            )


        st.write(
            "**Reason:** "
            + law_info["reason"]
        )


        with st.spinner(
            "⚖️ Legal analysis తయారు చేస్తోంది..."
        ):

            result = investigate_case(

                combined_text,

                law_info,

                incident_info,

                reference_date,

                old_pending
            )


        st.subheader(
            "📋 Legal Analysis Result"
        )


        st.markdown(
            result
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()


st.caption(
    "⚠️ ఈ tool investigation-support మరియు legal research కోసం మాత్రమే. "
    "Final legal actionకు ముందు official statute, notifications, "
    "court orders మరియు case-specific facts verify చేయాలి."
)
