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

MODEL_NAME = "llama-3.3-70b-versatile"


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

    # Telugu month
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


    # English: 10 September 2026
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


    # English: September 10 2026
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


    # -----------------------------
    # TODAY
    # -----------------------------

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


    # -----------------------------
    # YESTERDAY
    # -----------------------------

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


    # -----------------------------
    # ENGLISH TODAY
    # -----------------------------

    if re.search(
        r"\btoday\b",
        text_lower
    ):

        return {
            "date": reference_date,
            "type": "exact",
            "description": "today"
        }


    # -----------------------------
    # ENGLISH YESTERDAY
    # -----------------------------

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


    # -----------------------------
    # LAST WEEK
    # -----------------------------

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
    # OLD PENDING
    # =====================================================

    if old_case_pending:

        return {

            "status": "OLD_PENDING",

            "framework":
                "IPC / CrPC / Indian Evidence Act",

            "reason":
                "01-07-2024కు ముందు proceeding pendingలో "
                "ఉందని పేర్కొనబడింది. Transitional / "
                "repeal-and-savings provisions కూడా పరిశీలించాలి."

        }


    # =====================================================
    # OLD LAW
    # =====================================================

    if incident_date < NEW_LAW_DATE:

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
సపోర్ట్ కోసం రూపొందించబడిన జాగ్రత్తగా పనిచేసే Legal Research
Assistant.

=========================================================
అత్యంత ముఖ్యమైన భాషా నియమం
=========================================================

ఈ నివేదికను పూర్తిగా తెలుగులో మాత్రమే తయారు చేయాలి.

⚠️ ENGLISH PROSE రాయకూడదు.

అంటే:

❌ Case Summary
❌ Applicable Offence
❌ Investigation Steps
❌ Arrest Analysis
❌ Legal Cautions

ఇలా English headings లేదా English paragraphs ఇవ్వకూడదు.

దానికి బదులుగా:

✅ కేసు సారాంశం
✅ వర్తించే నేరాలు
✅ దర్యాప్తు దశలు
✅ అరెస్ట్‌పై విశ్లేషణ
✅ చట్టపరమైన హెచ్చరికలు

వంటి తెలుగు headings ఉపయోగించాలి.

=========================================================
ఏవి ENGLISHలో ఉండవచ్చు?
=========================================================

కింది వాటిని అవసరమైనప్పుడు Englishలో అలాగే ఉంచవచ్చు:

- BNS
- BNSS
- BSA
- IPC
- CrPC
- Indian Evidence Act
- Section numbers
- CDR
- IMEI
- APK
- IP Address
- URL
- SHA-256
- Google Play Store
- Technical forensic terms

కానీ వాటి వివరణ మాత్రం తెలుగులో ఉండాలి.

ఉదాహరణ:

"BNS Section 318 ప్రకారం cheatingకు సంబంధించిన
అంశాలను పరిశీలించాలి."

ఇలా ఉండాలి.

=========================================================
ENGLISH WARNING WORDS ఉపయోగించకూడదు
=========================================================

"VERIFY FROM OFFICIAL TEXT"

అని రాయకూడదు.

దానికి బదులుగా:

"అధికారిక చట్ట పాఠ్యంతో నిర్ధారించాలి."

అని రాయాలి.

అలాగే:

"NOT PROVIDED"
బదులుగా:

"సమాచారం అందుబాటులో లేదు."

"UNKNOWN"
బదులుగా:

"తెలియదు / గుర్తించబడలేదు."

"DATE REQUIRED"
బదులుగా:

"సంఘటన తేదీ అవసరం."

=========================================================
చట్టపరమైన ఖచ్చితత్వం
=========================================================

ఎప్పుడూ ఊహించి BNS / BNSS / BSA section numbers
రాయకూడదు.

ఖచ్చితమైన Section number తెలియకపోతే:

"సంబంధిత అధికారిక చట్ట పాఠ్యంతో సెక్షన్‌ను
నిర్ధారించాలి."

అని స్పష్టంగా చెప్పాలి.

తప్పు Section number తయారు చేయకూడదు.

=========================================================
1. సంఘటన తేదీ మొదట గుర్తించాలి
=========================================================

మొదట:

- సంఘటన తేదీ
- నేరం జరిగిన తేదీ
- occurrence date
- incident date

గుర్తించాలి.

కొత్త క్రిమినల్ చట్టాలు 01-07-2024 నుంచి అమల్లోకి వచ్చాయి:

- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

01-07-2024కు ముందు జరిగిన నేరాలకు
IPC / CrPC / Indian Evidence Act వర్తించే అవకాశం ఉంది.

01-07-2024 లేదా ఆ తర్వాత జరిగిన నేరాలకు
BNS / BNSS / BSA వర్తించే అవకాశం ఉంది.

అయితే transitional provisions మరియు pending proceedings
ఉంటే వాటిని కూడా పరిశీలించాలి.

=========================================================
2. REPORT FORMAT
=========================================================

కింది headings తప్పనిసరిగా తెలుగులో ఇవ్వాలి:

1. సంఘటన తేదీ & వర్తించే చట్టం
2. కేసు సారాంశం
3. వర్తించే నేరాలు
4. సెక్షన్ల వారీగా చట్టపరమైన విశ్లేషణ
5. కాగ్నిజబుల్ / నాన్-కాగ్నిజబుల్
6. బెయిలబుల్ / నాన్-బెయిలబుల్
7. శిక్ష వివరాలు
8. ట్రయల్ కోర్టు
9. FIR / ఫిర్యాదు విధానం
10. దర్యాప్తు దశలు
11. అరెస్ట్‌పై విశ్లేషణ
12. సోదాలు / స్వాధీనం
13. సాక్షుల విధివిధానాలు
14. డిజిటల్ / ఎలక్ట్రానిక్ సాక్ష్యాలు
15. ఫోరెన్సిక్ అవసరాలు
16. ఆస్తి / డబ్బు రికవరీ
17. నిందితుడి గుర్తింపు
18. కేస్ డైరీ / దర్యాప్తు రికార్డు
19. తుది నివేదిక / చార్జ్ షీట్
20. దర్యాప్తు అధికారి చెక్‌లిస్ట్
21. చట్టపరమైన హెచ్చరికలు / నిర్ధారించాల్సిన అంశాలు

=========================================================
3. INVESTIGATION SUPPORT
=========================================================

పోలీస్ Investigating Officerకు ఉపయోగపడే విధంగా
ప్రాక్టికల్ investigation steps ఇవ్వాలి.

కానీ ఊహించి:

- అరెస్ట్ తప్పనిసరి
- FIR తప్పనిసరిగా ఈ Sectionలోనే
- Search warrant తప్పనిసరి
- Court jurisdiction ఖచ్చితంగా ఇదే

అని చెప్పకూడదు.

వాస్తవాలు మరియు అధికారిక చట్టపాఠ్యం ఆధారంగా
అవసరమైన verification సూచించాలి.

=========================================================
4. ELECTRONIC EVIDENCE
=========================================================

Digital evidence గురించి:

- Mobile phone
- Screenshots
- WhatsApp messages
- SMS
- Call records
- CDR
- Bank transaction records
- APK
- URL
- IP address
- Server logs
- CCTV
- Email

వంటి evidenceలను అవసరాన్ని బట్టి వివరించాలి.

BSA ప్రకారం certificate అవసరమా లేదా అనే విషయాన్ని
సంబంధిత electronic record మరియు అధికారిక చట్ట నిబంధనల
ఆధారంగా మాత్రమే చెప్పాలి.

=========================================================
5. FINAL LANGUAGE RULE
=========================================================

FINAL OUTPUT:

తెలుగు భాషలోనే ఉండాలి.

Englishలో పూర్తి sentence లేదా paragraph రాయకూడదు.

Official Act names, Section numbers మరియు technical
terms మాత్రమే Englishలో ఉండవచ్చు.

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
పూర్తి Legal Analysis Report తయారు చేయండి.

=========================================================
తేదీ సమాచారం
=========================================================

గుర్తించిన సంఘటన / నేరం తేదీ:
{incident_date_text}

ఫిర్యాదు / Reference Date:
{reference_text}

కొత్త క్రిమినల్ చట్టాలు అమల్లోకి వచ్చిన తేదీ:
01-07-2024

01-07-2024కి ముందు కేసు / proceeding pendingలో ఉందా?:
{pending_text}

ప్రాథమికంగా గుర్తించిన వర్తించే చట్టం:
{law_info["framework"]}

చట్టం ఎంపికకు కారణం:
{law_info["reason"]}


=========================================================
కేసు మెటీరియల్
=========================================================

{case_text}


=========================================================
చివరి సూచనలు
=========================================================

1. మొత్తం నివేదిక తెలుగులోనే ఇవ్వాలి.

2. Englishలో పూర్తి sentences లేదా paragraphs
   ఇవ్వకూడదు.

3. BNS / BNSS / BSA / IPC / CrPC వంటి
   అధికారిక చట్టాల పేర్లు Englishలో ఉండవచ్చు.

4. Section numbers మార్చకూడదు.

5. ఖచ్చితమైన Section number తెలియకపోతే
   ఊహించి రాయకూడదు.

6. "అధికారిక చట్ట పాఠ్యంతో నిర్ధారించాలి"
   అని పేర్కొనాలి.

7. Cognizable / Non-Cognizable,
   Bailable / Non-Bailable,
   Punishment, Trial Court వంటి అంశాలను
   సంబంధిత actual offence Section ఆధారంగా మాత్రమే
   విశ్లేషించాలి.

8. Digital evidenceకు సంబంధించిన BSA requirementsను
   అవసరాన్ని బట్టి వివరించాలి.

9. Investigation Officerకు ఉపయోగపడే practical
   investigation checklist ఇవ్వాలి.

10. తుది legal conclusion ఇవ్వడానికి ముందు
    case-specific facts మరియు official statute
    verify చేయాల్సి ఉంటే స్పష్టంగా సూచించాలి.

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
        "IPC / CrPC / Indian Evidence Act"

    )


elif law_info["status"] in [

    "NEW",
    "NEW_RANGE"

]:

    st.success(

        "✅ కొత్త చట్టాల వర్తింపు\n\n"

        "వర్తించే చట్టాలు: "
        "BNS / BNSS / BSA"

    )


elif law_info["status"] == "CROSS_TRANSITION":

    st.error(

        "⚠️ తేదీ పరివర్తన కేసు\n\n"

        "సంఘటన తేదీ 01-07-2024ను దాటుతోంది. "
        "Transitional provisions పరిశీలించాలి."

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
