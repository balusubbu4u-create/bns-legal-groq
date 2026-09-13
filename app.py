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
    client = Groq(
        api_key=GROQ_API_KEY
    )

except Exception as e:
    st.error(
        f"Groq client ప్రారంభించలేకపోయింది: {e}"
    )
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
    # Telugu month
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
    # English: 10 September 2026
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
    # English: September 10 2026
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

def extract_relative_date(
    text,
    reference_date
):

    if not text:
        return None

    if reference_date is None:
        return None

    text_lower = text.lower()


    # -----------------------------------------------------
    # TODAY
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
    # YESTERDAY
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

    if not text:
        return None

    text = str(text)

    lines = text.splitlines()


    # =====================================================
    # EXPLICIT INCIDENT DATE KEYWORDS
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


    # =====================================================
    # SEARCH LINE BY LINE
    # =====================================================

    for line in lines:

        lower_line = line.lower()

        found_keyword = False

        for keyword in explicit_keywords:

            if keyword.lower() in lower_line:

                found_keyword = True
                break

        if not found_keyword:
            continue


        # Named month
        parsed = parse_named_month_date(line)

        if parsed:

            return {
                "date": parsed,
                "type": "exact",
                "source": "explicit incident date"
            }


        # Numeric date
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
    # DATE RANGE
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
    # ANY NAMED MONTH DATE
    # =====================================================

    parsed = parse_named_month_date(text)

    if parsed:

        return {

            "date": parsed,

            "type": "exact",

            "source": "named month date"

        }


    # =====================================================
    # INCIDENT RELATED LINE
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
    # RELATIVE DATE
    # =====================================================

    relative_result = extract_relative_date(
        text,
        reference_date
    )

    if relative_result:
        return relative_result


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
                "సంఘటన / నేరం జరిగిన తేదీ గుర్తించబడలేదు."
            )

        }


    # =====================================================
    # DATE RANGE
    # =====================================================

    if incident_info.get("type") == "range":

        start_date = incident_info["start"]

        end_date = incident_info["end"]


        if end_date < NEW_LAW_DATE:

            return {

                "status": "OLD_RANGE",

                "framework":
                    "IPC / CrPC / Indian Evidence Act",

                "reason":
                    "సంఘటన కాలం 01-07-2024కు ముందు ఉంది."

            }


        elif start_date >= NEW_LAW_DATE:

            return {

                "status": "NEW_RANGE",

                "framework":
                    "BNS / BNSS / BSA",

                "reason":
                    "సంఘటన కాలం మొత్తం 01-07-2024 తర్వాత ఉంది."

            }


        else:

            return {

                "status": "CROSS_TRANSITION",

                "framework":
                    "DATE_REVIEW_REQUIRED",

                "reason":
                    "సంఘటన కాలం 01-07-2024ను దాటుతోంది. "
                    "ఖచ్చితమైన తేదీలు మరియు transitional provisions "
                    "పరిశీలించాలి."

            }


    # =====================================================
    # SINGLE DATE
    # =====================================================

    incident_date = incident_info["date"]


    # =====================================================
    # IMPORTANT:
    # PENDING CASE ALONE SHOULD NOT CHANGE OFFENCE DATE LAW
    # =====================================================

    if incident_date < NEW_LAW_DATE:

        if old_case_pending:

            return {

                "status": "OLD_PENDING",

                "framework":
                    "IPC / CrPC / Indian Evidence Act",

                "reason":
                    "సంఘటన తేదీ 01-07-2024కు ముందు ఉంది మరియు "
                    "కేసు / proceeding pendingలో ఉన్నట్లు పేర్కొనబడింది. "
                    "Repeal-and-savings / transitional provisions "
                    "కూడా పరిశీలించాలి."

            }

        return {

            "status": "OLD",

            "framework":
                "IPC / CrPC / Indian Evidence Act",

            "reason":
                f"సంఘటన తేదీ "
                f"{incident_date.strftime('%d-%m-%Y')} "
                f"01-07-2024కు ముందు ఉంది."

        }


    # =====================================================
    # NEW LAW
    # =====================================================

    if old_case_pending:

        return {

            "status": "NEW_PENDING_REVIEW",

            "framework":
                "BNS / BNSS / BSA",

            "reason":
                f"సంఘటన తేదీ "
                f"{incident_date.strftime('%d-%m-%Y')} "
                f"01-07-2024 తర్వాత ఉంది. "
                f"అయితే proceeding pendingగా పేర్కొనబడినందున "
                f"transitional / savings provisionsను వేరుగా పరిశీలించాలి."

        }


    return {

        "status": "NEW",

        "framework":
            "BNS / BNSS / BSA",

        "reason":
            f"సంఘటన తేదీ "
            f"{incident_date.strftime('%d-%m-%Y')} "
            f"01-07-2024 తర్వాత / అదే తేదీ నుంచి "
            f"కొత్త క్రిమినల్ చట్టాల పరిధిలోకి వస్తుంది."

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


    # TXT
    if filename.endswith(".txt"):

        try:

            uploaded_file.seek(0)

            return uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

        except Exception as e:

            return f"TXT చదవడంలో సమస్య: {e}"


    # PDF
    if filename.endswith(".pdf"):

        return extract_pdf_text(
            uploaded_file
        )


    # IMAGE
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

మీరు భారతదేశ క్రిమినల్ లా మరియు పోలీస్ ఇన్వెస్టిగేషన్
సపోర్ట్ కోసం రూపొందించబడిన Legal Research Assistant.

మీ పని కేవలం complaint summary ఇవ్వడం కాదు.

మీ ప్రధాన పని:

FACTS
→ LEGAL INGREDIENTS
→ EXACT APPLICABLE OFFENCE
→ EXACT SECTION
→ SECTION-WISE ANALYSIS
→ PROCEDURE
→ EVIDENCE
→ INVESTIGATION STEPS

అనే క్రమంలో case-specific legal analysis ఇవ్వడం.

=========================================================
అత్యంత ముఖ్యమైన భాషా నియమం
=========================================================

మొత్తం నివేదిక తెలుగులో ఉండాలి.

Englishలో పూర్తి paragraphs రాయకూడదు.

కానీ official legal names, Act names, Section numbers,
technical terms అవసరమైనప్పుడు Englishలో ఉండవచ్చు.

ఉదాహరణ:

"BNS Section 318"

"Information Technology Act, 2000"

"BSA Section 63"

"CDR"

"IMEI"

"IP Address"

"URL"

ఇవన్నీ Englishలో ఉండవచ్చు.

వాటి వివరణ మాత్రం తెలుగులో ఇవ్వాలి.

=========================================================
అత్యంత ముఖ్యమైన RULE:
EXACT APPLICABLE SECTION తప్పనిసరి
=========================================================

Complaint factsలో ఒక offence యొక్క legal ingredients
స్పష్టంగా కనిపిస్తే, ఆ offenceకు సంబంధించిన
ఖచ్చితమైన applicable Sectionను identify చేయాలి.

కేవలం:

"Cheating వర్తిస్తుంది"

"Cyber fraud వర్తిస్తుంది"

"సంబంధిత సెక్షన్ వర్తిస్తుంది"

అని చెప్పి ఆపకూడదు.

అదే విధంగా:

"Section verify చేయాలి"

అని మాత్రమే చెప్పకూడదు.

బదులుగా:

"వర్తించే Section: ______"

అని స్పష్టంగా ఇవ్వాలి.

=========================================================
SECTION IDENTIFICATION METHOD
=========================================================

ప్రతి offence కోసం ఈ క్రమాన్ని పాటించాలి:

1. Complaintలో జరిగిన actual act ఏమిటి?

2. Accused ఏ చర్య చేశాడు?

3. Victimను ఎలా deceive చేశాడు?

4. Victim ఏ information ఇచ్చాడు?

5. Property / money ఎలా transfer లేదా debit అయింది?

6. Dishonest intention ఎప్పుడు కనిపిస్తుంది?

7. Identity cheating / impersonation ఉందా?

8. Unauthorized access / computer resource misuse ఉందా?

9. Electronic record manipulation ఉందా?

10. Criminal intimidation / extortion / forgery వంటి
    ప్రత్యేక అంశాలు ఉన్నాయా?

11. Factsలో ఏ statutory ingredients పూర్తవుతున్నాయి?

12. ఆ ingredientsకు సరిపోయే exact statutory provision
    ఏది?

13. Primary offence ఏది?

14. Alternative / additional offence ఏది?

ఈ విశ్లేషణ తర్వాత exact Section ఇవ్వాలి.

=========================================================
ప్రతి OFFENCEకి తప్పనిసరిగా ఈ FORMAT
=========================================================

### నేరం 1

**నేరం:**
[నేరం పేరు]

**చట్టం:**
[BNS / IT Act / ఇతర వర్తించే Act]

**వర్తించే ఖచ్చితమైన Section:**
[Section number]

**చట్టపరమైన అంశాలు:**
- Ingredient 1
- Ingredient 2
- Ingredient 3

**ఫిర్యాదులో ఉన్న వాస్తవాలు:**
- Fact 1
- Fact 2
- Fact 3

**వాస్తవాలు మరియు Section అంశాల పోలిక:**
ప్రతి ingredient complaintలో ఎలా satisfy అవుతుందో
స్పష్టంగా వివరించాలి.

**తీర్మానం:**
Section వర్తిస్తుంది / అదనపు సమాచారం అవసరం.

=========================================================
PRIMARY VS ALTERNATIVE OFFENCE
=========================================================

ఒకటి కంటే ఎక్కువ offences కనిపిస్తే:

1. ప్రధానంగా వర్తించే నేరం
2. అదనంగా పరిశీలించాల్సిన నేరం
3. ప్రత్యామ్నాయంగా పరిశీలించాల్సిన నేరం

అని వేరు చేయాలి.

ఒకే actకు అనవసరంగా చాలా Sections ఇవ్వకూడదు.

Facts support చేయని Section ఇవ్వకూడదు.

=========================================================
SECTION INVENT చేయకూడదు
=========================================================

ఏ Section numberపై నమ్మకం లేకపోతే ఊహించి
Section number రాయకూడదు.

అప్పుడు:

"ఈ offenceకు సంబంధించిన ఖచ్చితమైన Sectionను
అధికారిక చట్ట పాఠ్యంతో నిర్ధారించాలి."

అని చెప్పాలి.

కానీ Section తెలిసినప్పుడు తప్పనిసరిగా Section number
ఇవ్వాలి.

=========================================================
BNS / BNSS / BSA ROLE
=========================================================

BNS:
ప్రధానంగా substantive offences / punishments.

BNSS:
FIR, investigation, arrest, search, seizure,
procedure, remand, bail procedure, final report
వంటి procedural matters.

BSA:
Evidence మరియు electronic evidence admissibility
సంబంధిత provisions.

BNSS లేదా BSAను సాధారణంగా "fraud offence section"
లాగా చూపకూడదు.

=========================================================
SPECIAL LAWS
=========================================================

Cyber / online / computer-related complaint అయితే
BNSతో పాటు అవసరాన్ని బట్టి:

Information Technology Act, 2000

లోని relevant provisionsను కూడా పరిశీలించాలి.

కానీ facts satisfy చేయని Sectionను ఇవ్వకూడదు.

=========================================================
COGNIZABLE / NON-COGNIZABLE
=========================================================

ప్రతి exact offence Section identify చేసిన తర్వాతే
Cognizable / Non-Cognizable classification ఇవ్వాలి.

Generic "cyber offence కాబట్టి cognizable" అని చెప్పకూడదు.

=========================================================
BAILABLE / NON-BAILABLE
=========================================================

Exact offence Section ఆధారంగా మాత్రమే
Bailable / Non-Bailable classification ఇవ్వాలి.

Non-bailable అంటే:

"అరెస్ట్ తప్పనిసరి"

అని అర్థం కాదు.

=========================================================
PUNISHMENT
=========================================================

Exact Section ఆధారంగా statutory punishment మాత్రమే ఇవ్వాలి.

ఊహించి:

"5 years"

"10 years"

వంటి punishment ఇవ్వకూడదు.

Exact statutory punishment తెలియకపోతే
అధికారిక చట్ట పాఠ్యంతో నిర్ధారించాలి.

=========================================================
TRIAL COURT
=========================================================

Trial Courtను exact offence classification మరియు
వర్తించే procedural law ఆధారంగా మాత్రమే చెప్పాలి.

Amount మాత్రమే చూసి:

"Sessions Court"

అని నిర్ణయించకూడదు.

=========================================================
ARREST ANALYSIS
=========================================================

అరెస్ట్ గురించి:

1. Arrest power ఉందా?
2. Arrest అవసరం ఎందుకు?
3. Arrest అవసరం లేకపోతే alternative procedure ఏమిటి?
4. Notice / appearance procedure అవసరమా?
5. Custodial interrogation అవసరమా?
6. Evidence destruction / tampering risk ఉందా?
7. Absconding risk ఉందా?

వంటి అంశాలను వేరు చేసి వివరించాలి.

"తప్పనిసరిగా అరెస్ట్ చేయాలి" అని facts support చేయకుండా
చెప్పకూడదు.

=========================================================
SEARCH / SEIZURE
=========================================================

Search మరియు seizureను arrestతో కలపకూడదు.

ప్రత్యేకంగా:

- Mobile phone
- SIM
- Laptop
- Bank documents
- Digital storage
- CCTV
- Devices

వంటి evidence seizure అవసరాన్ని వివరించాలి.

Search warrant / statutory power అవసరమా అనే విషయాన్ని
వర్తించే procedure ఆధారంగా మాత్రమే చెప్పాలి.

=========================================================
DIGITAL / ELECTRONIC EVIDENCE
=========================================================

కేసుకు అవసరమైన evidence:

- Screenshots
- WhatsApp chats
- SMS
- Call recordings
- Call detail records
- Bank transaction records
- UTR / transaction reference
- Beneficiary account
- Mobile number
- IMEI
- IP address
- URL
- App details
- APK
- Server logs
- Email
- CCTV
- Device data

వంటి వాటిని identify చేయాలి.

=========================================================
BSA ELECTRONIC EVIDENCE
=========================================================

Electronic recordకు certificate అవసరమా లేదా అనే విషయం
ఆ record యొక్క nature మరియు applicable BSA provision
ఆధారంగా case-specificగా చెప్పాలి.

ప్రతి digital evidenceకి ఒకే certificate తప్పనిసరి
అని blanket statement ఇవ్వకూడదు.

=========================================================
FINANCIAL FRAUD
=========================================================

Financial / cyber fraud complaint అయితే:

- Debit transaction
- Credit transaction
- UTR
- Transaction ID
- Beneficiary account
- Bank statement
- Account holder KYC
- Mobile number
- Device details
- IP logs
- ATM / POS / UPI details
- Bank freeze / lien
- Money trail
- Further transfer
- Recovery possibility

వంటి అంశాలను investigationలో గుర్తించాలి.

=========================================================
ACCUSED IDENTIFICATION
=========================================================

Phone number, Google Play developer details,
bank account, SIM, IP address, device details
వంటి వాటిని investigation leadsగా చూడాలి.

వాటిని ఒక్కటే ఆధారంగా accused identity conclusively
establish అయిందని చెప్పకూడదు.

=========================================================
FIR / COMPLAINT
=========================================================

FIR registrationకు applicable offence మరియు
procedural law ఆధారంగా analysis ఇవ్వాలి.

=========================================================
REPORT HEADINGS
=========================================================

కింది headings తప్పనిసరిగా ఉండాలి:

1. సంఘటన తేదీ & వర్తించే చట్టం

2. కేసు సారాంశం

3. వర్తించే నేరాలు

4. వర్తించే ఖచ్చితమైన సెక్షన్లు

5. సెక్షన్ల వారీగా చట్టపరమైన విశ్లేషణ

6. కాగ్నిజబుల్ / నాన్-కాగ్నిజబుల్

7. బెయిలబుల్ / నాన్-బెయిలబుల్

8. శిక్ష వివరాలు

9. ట్రయల్ కోర్టు

10. FIR / ఫిర్యాదు విధానం

11. దర్యాప్తు దశలు

12. అరెస్ట్‌పై విశ్లేషణ

13. సోదాలు / స్వాధీనం

14. సాక్షుల విధివిధానాలు

15. డిజిటల్ / ఎలక్ట్రానిక్ సాక్ష్యాలు

16. ఫోరెన్సిక్ అవసరాలు

17. ఆస్తి / డబ్బు రికవరీ

18. నిందితుడి గుర్తింపు

19. కేస్ డైరీ / దర్యాప్తు రికార్డు

20. తుది నివేదిక / చార్జ్ షీట్

21. దర్యాప్తు అధికారి చెక్‌లిస్ట్

22. చట్టపరమైన హెచ్చరికలు / నిర్ధారించాల్సిన అంశాలు

=========================================================
MANDATORY SECTION TABLE
=========================================================

Reportలో ఈ table తప్పనిసరిగా ఇవ్వాలి:

| నేరం | చట్టం | వర్తించే Section | ఎందుకు వర్తిస్తుంది | Cognizable | Bailable | Punishment | Trial Court |
|---|---|---|---|---|---|---|---|

Tableలో exact section identify చేయాలి.

Section factsకు సరిపోకపోతే tableలో
"అదనపు వాస్తవాలు అవసరం" అని పేర్కొనాలి.

=========================================================
CASE-SPECIFIC ANALYSIS
=========================================================

Complaintలో ఉన్న factsను మాత్రమే ఆధారంగా తీసుకోవాలి.

లేని factsను కల్పించకూడదు.

ఉదాహరణకు complaintలో:

"OTP ఇచ్చాడు"

అని లేకపోతే OTP ఇచ్చినట్లు assume చేయకూడదు.

"Password ఇచ్చాడు"

అని లేకపోతే password ఇచ్చినట్లు assume చేయకూడదు.

"Accused intentionally cheated"

అని complaintలో నిర్ధారించబడకపోతే,
facts ఆధారంగా dishonest intentionను analyse చేయాలి.

=========================================================
DATE
=========================================================

మొదట సంఘటన తేదీ identify చేయాలి.

01-07-2024:

BNS / BNSS / BSA commencement date.

01-07-2024కు ముందు జరిగిన offence అయితే
IPC / CrPC / Indian Evidence Act framework
వర్తించే అవకాశం ఉంది.

01-07-2024 లేదా ఆ తర్వాత జరిగిన offence అయితే
BNS / BNSS / BSA frameworkను పరిశీలించాలి.

Pending proceedings ఉంటే repeal-and-savings /
transitional provisionsను కూడా analyse చేయాలి.

=========================================================
IMPORTANT
=========================================================

మీకు exact Section తెలుసు మరియు facts satisfy చేస్తే
ఖచ్చితంగా Section number ఇవ్వాలి.

ప్రతి కేసులో generic disclaimerతో Section analysisను
తప్పించకూడదు.

=========================================================
FINAL OUTPUT
=========================================================

చివరలో:

"చట్టపరమైన హెచ్చరికలు / నిర్ధారించాల్సిన అంశాలు"

లో ఏ అంశాలు అధికారిక చట్టం, case diary, documentary
evidence లేదా court order ద్వారా verify చేయాలో మాత్రమే
స్పష్టంగా ఇవ్వాలి.

మొత్తం report తెలుగులో ఉండాలి.
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

    if incident_info is None:

        incident_date_text = (
            "గుర్తించబడలేదు"
        )

    elif incident_info.get("type") == "range":

        incident_date_text = (

            f"{incident_info['start'].strftime('%d-%m-%Y')}"

            f" నుండి "

            f"{incident_info['end'].strftime('%d-%m-%Y')}"

        )

    else:

        incident_date_text = (

            incident_info["date"].strftime(
                "%d-%m-%Y"
            )

        )


    if reference_date:

        reference_text = (
            reference_date.strftime(
                "%d-%m-%Y"
            )
        )

    else:

        reference_text = (
            "సమాచారం అందుబాటులో లేదు"
        )


    pending_text = (

        "అవును"

        if old_pending

        else

        "లేదు"

    )


    return f"""

క్రింది పోలీసు ఫిర్యాదు / కేసు వివరాలను పరిశీలించి
పూర్తి case-specific Legal Analysis Report తయారు చేయండి.

=========================================================
తేదీ సమాచారం
=========================================================

గుర్తించిన సంఘటన / నేరం తేదీ:
{incident_date_text}

ఫిర్యాదు / Reference Date:
{reference_text}

కొత్త క్రిమినల్ చట్టాల ప్రారంభ తేదీ:
01-07-2024

01-07-2024కి ముందు కేసు / proceeding pendingలో ఉందా?:
{pending_text}

ప్రాథమికంగా గుర్తించిన చట్ట framework:
{law_info["framework"]}

చట్ట framework ఎంపికకు కారణం:
{law_info["reason"]}


=========================================================
కేసు మెటీరియల్
=========================================================

{case_text}


=========================================================
చాలా ముఖ్యమైన ANALYSIS INSTRUCTIONS
=========================================================

ఈ complaintను కేవలం summary చేయకండి.

మొదట complaintలోని factsను విడదీయండి.

తర్వాత ప్రతి possible offence యొక్క legal ingredientsను
పరిశీలించండి.

ఆ ingredients factsతో match అయితే exact applicable
Section numberను తప్పనిసరిగా ఇవ్వండి.

ప్రతి offenceకు:

1. నేరం పేరు
2. చట్టం
3. ఖచ్చితమైన Section
4. Section legal ingredients
5. Complaintలో ఆ ingredientsకు support చేసే facts
6. Cognizable / Non-Cognizable
7. Bailable / Non-Bailable
8. Statutory punishment
9. Trial Court
10. Evidence

ఇవ్వాలి.

=========================================================
MANDATORY SECTION TABLE
=========================================================

కింది table తప్పనిసరిగా ఇవ్వాలి:

| నేరం | చట్టం | వర్తించే Section | ఎందుకు వర్తిస్తుంది | Cognizable | Bailable | Punishment | Trial Court |
|---|---|---|---|---|---|---|---|

=========================================================
PRIMARY / ALTERNATIVE
=========================================================

ఒకటి కంటే ఎక్కువ offences ఉంటే:

ప్రధాన నేరం

అదనపు నేరం

ప్రత్యామ్నాయంగా పరిశీలించాల్సిన నేరం

అని వేరు చేయండి.

Facts support చేయని Sectionలను చేర్చకండి.

=========================================================
NO INVENTION
=========================================================

Complaintలో లేని factsను assume చేయకండి.

తెలియని విషయం ఉంటే:

"అదనపు వాస్తవాలు అవసరం"

అని చెప్పండి.

Section numberపై నిజమైన certainty లేకపోతే
ఊహించి రాయకండి.

అధికారిక చట్ట పాఠ్యంతో నిర్ధారించాల్సిన అంశాన్ని
స్పష్టంగా గుర్తించండి.

=========================================================
CYBER / FINANCIAL FRAUD
=========================================================

Online / cyber / financial fraud అయితే:

- Bank transaction
- UTR
- Beneficiary account
- Mobile number
- SIM
- IMEI
- IP
- URL
- App details
- Developer details
- Device
- CCTV
- CDR
- Bank KYC
- Money trail
- Freeze / lien
- Recovery

వంటి investigation pointsను గుర్తించండి.

అవసరమైతే Information Technology Act, 2000లోని
relevant provisionsను కూడా పరిశీలించండి.

=========================================================
FINAL
=========================================================

మొత్తం report తెలుగులో ఉండాలి.

English official legal names, Section numbers,
technical terms మాత్రమే అవసరమైనప్పుడు ఉపయోగించండి.

Section analysisను generic disclaimerతో తప్పించకండి.
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


        result = (
            response
            .choices[0]
            .message
            .content
        )


        if not result:

            return (
                "❌ AI నుంచి లీగల్ అనాలిసిస్ రాలేదు."
            )


        return result


    except Exception as e:

        return (
            "❌ AI లీగల్ అనాలిసిస్‌లో ఎర్రర్ వచ్చింది.\n\n"
            f"Error: {e}"
        )


# =========================================================
# CASE DETAILS
# =========================================================

st.subheader(
    "📝 కేసు / ఫిర్యాదు వివరాలు"
)


case_text = st.text_area(

    "కేసు వివరాలు / FIR / Complaint ఇక్కడ paste చేయండి",

    height=350,

    placeholder=(

        "ఉదాహరణ:\n\n"

        "10 సెప్టెంబర్ 2026న జరిగిన సంఘటనపై...\n"

        "మధ్యాహ్నం సుమారు 2:30 గంటలకు...\n"

        "ఫిర్యాదుదారుడి బ్యాంక్ ఖాతా నుంచి డబ్బు డెబిట్ అయింది..."

    )

)


# =========================================================
# REFERENCE DATE
# =========================================================

st.subheader(
    "📅 Complaint / Reference Date"
)


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

st.subheader(
    "⚖️ పాత కేసు Pending Check"
)


old_pending = st.checkbox(

    "01-07-2024కి ముందు ఈ కేసు / proceeding ఇప్పటికే pendingలో ఉందా?"

)


# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader(
    "📎 FIR / Complaint / Document Upload"
)


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

combined_text = case_text.strip()


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

        "• నిన్న / ఈరోజు / గత వారం"

    )


elif incident_info.get("type") == "range":

    st.warning(
        "📅 సంఘటన తేదీల పరిధి గుర్తించబడింది"
    )


    st.write(

        "**ప్రారంభ తేదీ:** "

        + incident_info["start"].strftime(
            "%d-%m-%Y"
        )

    )


    st.write(

        "**ముగింపు తేదీ:** "

        + incident_info["end"].strftime(
            "%d-%m-%Y"
        )

    )


else:

    detected_date = (
        incident_info["date"]
    )


    st.write(

        "**గుర్తించిన సంఘటన తేదీ:** "

        + detected_date.strftime(
            "%d-%m-%Y"
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

        "⚠️ పాత చట్టాల వర్తింపు\n\n"

        "వర్తించే చట్టాలు: "
        "IPC / CrPC / Indian Evidence Act\n\n"

        + law_info["reason"]

    )


elif law_info["status"] in [

    "NEW",
    "NEW_RANGE",
    "NEW_PENDING_REVIEW"

]:

    st.success(

        "✅ కొత్త చట్టాల వర్తింపు\n\n"

        "వర్తించే చట్టాలు: "
        "BNS / BNSS / BSA\n\n"

        + law_info["reason"]

    )


elif law_info["status"] == "CROSS_TRANSITION":

    st.error(

        "⚠️ తేదీ పరివర్తన కేసు\n\n"

        "సంఘటన తేదీ 01-07-2024ను దాటుతోంది. "
        "Transitional provisions పరిశీలించాలి.\n\n"

        + law_info["reason"]

    )


# =========================================================
# ANALYSIS BUTTON
# =========================================================

if st.button(

    "⚖️ లీగల్ అనాలిసిస్ ప్రారంభించండి",

    type="primary",

    use_container_width=True

):

    if not combined_text.strip():

        st.error(

            "❌ ముందుగా కేసు వివరాలు లేదా డాక్యుమెంట్ ఇవ్వండి."

        )


    elif incident_info is None:

        st.error(

            "❌ సంఘటన తేదీని గుర్తించలేకపోయాము."

        )


    else:

        with st.spinner(

            "⚖️ పూర్తి తెలుగులో లీగల్ అనాలిసిస్ "
            "రిపోర్ట్ తయారు చేస్తోంది..."

        ):

            result = investigate_case(

                combined_text,

                law_info,

                incident_info,

                reference_date,

                old_pending

            )


        st.subheader(

            "📋 లీగల్ అనాలిసిస్ నివేదిక"

        )


        st.markdown(
            result
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()


st.caption(

    "⚠️ ఈ టూల్ కేవలం ఇన్వెస్టిగేషన్ సపోర్ట్ మరియు "
    "లీగల్ రీసెర్చ్ కోసం మాత్రమే. "
    "అధికారిక చట్టాలు, నిబంధనలు మరియు కోర్టు "
    "ఆదేశాల ప్రకారం తుది చర్యలు తీసుకోవాలి."

)
