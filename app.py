import os
import re
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image
from groq import Groq


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Police Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్")
st.caption(
    "BNS • BNSS • BSA • IT Act ఆధారంగా preliminary legal & investigation assistance"
)


# =========================================================
# CONSTANTS
# =========================================================

NEW_LAW_DATE = date(2024, 7, 1)

MODEL_NAME = "openai/gpt-oss-120b"


# =========================================================
# API KEY
# =========================================================

def get_groq_client():
    api_key = None

    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        st.error(
            "❌ GROQ_API_KEY కనుగొనబడలేదు.\n\n"
            "Streamlit Cloud → Settings → Secrets లో GROQ_API_KEY ఇవ్వండి."
        )
        st.stop()

    return Groq(api_key=api_key)


client = get_groq_client()


# =========================================================
# MONTH DICTIONARIES
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
# TELUGU DIGITS → ENGLISH DIGITS
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
# DATE PARSING
# =========================================================

def safe_date(year, month, day):
    try:
        return date(int(year), int(month), int(day))
    except Exception:
        return None


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

    value = normalize_digits(value.strip())

    # YYYY-MM-DD
    m = re.search(
        r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b",
        value
    )

    if m:
        return safe_date(
            m.group(1),
            m.group(2),
            m.group(3)
        )

    # DD-MM-YYYY / DD/MM/YYYY / DD.MM.YYYY
    m = re.search(
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b",
        value
    )

    if m:
        return safe_date(
            m.group(3),
            m.group(2),
            m.group(1)
        )

    # DD-MM-YY
    m = re.search(
        r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})\b",
        value
    )

    if m:
        year = int(m.group(3))

        if year <= 49:
            year += 2000
        else:
            year += 1900

        return safe_date(
            year,
            m.group(2),
            m.group(1)
        )

    return None


def parse_named_month_date(text):
    """
    Examples:
    10 September 2026
    10 September, 2026
    10 సెప్టెంబర్ 2026
    10 సెప్టెంబర్ 2026న
    """

    if not text:
        return None

    text = normalize_digits(text)

    # English
    month_pattern_en = "|".join(
        sorted(
            [re.escape(x) for x in ENGLISH_MONTHS.keys()],
            key=len,
            reverse=True
        )
    )

    pattern_en = rf"\b(\d{{1,2}})\s+({month_pattern_en})[,\s]+(20\d{{2}})\b"

    m = re.search(
        pattern_en,
        text,
        flags=re.IGNORECASE
    )

    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))

        month = ENGLISH_MONTHS.get(month_name)

        if month:
            return safe_date(year, month, day)

    # Telugu
    month_pattern_te = "|".join(
        sorted(
            [re.escape(x) for x in TELUGU_MONTHS.keys()],
            key=len,
            reverse=True
        )
    )

    pattern_te = rf"(\d{{1,2}})\s*({month_pattern_te})\s*(20\d{{2}})"

    m = re.search(pattern_te, text)

    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        year = int(m.group(3))

        month = TELUGU_MONTHS.get(month_name)

        if month:
            return safe_date(year, month, day)

    return None


# =========================================================
# RELATIVE DATE
# =========================================================

def extract_relative_date(text, reference_date):
    if not text:
        return None, None

    lower = text.lower()

    # Telugu
    if "ఈ రోజు" in text or "ఈరోజు" in text:
        return reference_date, "ఈ రోజు"

    if "నిన్న" in text:
        return reference_date - timedelta(days=1), "నిన్న"

    if "మొన్న" in text:
        return reference_date - timedelta(days=2), "మొన్న"

    if "నిన్న మొన్న" in text:
        return reference_date - timedelta(days=2), "నిన్న మొన్న"

    # English
    if re.search(r"\btoday\b", lower):
        return reference_date, "today"

    if re.search(r"\byesterday\b", lower):
        return reference_date - timedelta(days=1), "yesterday"

    if re.search(r"\bday before yesterday\b", lower):
        return reference_date - timedelta(days=2), "day before yesterday"

    # Last week
    if "గత వారం" in text or "గతవారం" in text:
        return reference_date - timedelta(days=7), "గత వారం"

    if re.search(r"\blast week\b", lower):
        return reference_date - timedelta(days=7), "last week"

    return None, None


# =========================================================
# INCIDENT DATE EXTRACTION
# =========================================================

def extract_incident_date(text, reference_date):
    if not text:
        return None, None

    text = normalize_digits(text)

    # -----------------------------------------------------
    # 1. Relative dates
    # -----------------------------------------------------

    rel_date, rel_text = extract_relative_date(
        text,
        reference_date
    )

    if rel_date:
        return rel_date, rel_text

    # -----------------------------------------------------
    # 2. Explicit numeric date
    # -----------------------------------------------------

    date_keywords = [
        "సంఘటన తేదీ",
        "సంఘటన జరిగిన తేదీ",
        "ఘటన తేదీ",
        "ఘటన జరిగిన తేదీ",
        "నేరం జరిగిన తేదీ",
        "నేరం తేదీ",
        "ఘటన",
        "సంఘటన",
        "occurrence date",
        "incident date",
        "date of incident",
        "date of occurrence",
        "occurred on",
        "on"
    ]

    # First try dates near incident-related words
    for keyword in date_keywords:
        idx = text.lower().find(keyword.lower())

        if idx >= 0:
            nearby = text[idx:idx + 180]

            d = parse_date_string(nearby)

            if d:
                return d, nearby[:100]

            d = parse_named_month_date(nearby)

            if d:
                return d, nearby[:100]

    # -----------------------------------------------------
    # 3. Search all numeric dates
    # -----------------------------------------------------

    patterns = [
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]20\d{2}\b",
        r"\b20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}\b",
        r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2}\b",
    ]

    for pattern in patterns:
        m = re.search(pattern, text)

        if m:
            d = parse_date_string(m.group(0))

            if d:
                return d, m.group(0)

    # -----------------------------------------------------
    # 4. Named month dates
    # -----------------------------------------------------

    d = parse_named_month_date(text)

    if d:
        return d, str(d)

    return None, None


# =========================================================
# LAW SELECTION
# =========================================================

def select_law(incident_date, pending_case=False):
    if not incident_date:
        return {
            "framework": "UNKNOWN",
            "title": "చట్టాల framework నిర్ణయించడానికి సంఘటన తేదీ అవసరం",
            "reason": (
                "Incident/occurrence date నిర్ధారించబడలేదు. "
                "BNS/BNSS/BSA లేదా IPC/CrPC/IEA applicability "
                "fact-specificగా verify చేయాలి."
            )
        }

    if incident_date >= NEW_LAW_DATE:

        if pending_case:
            return {
                "framework": "NEW_LAW_WITH_TRANSITION_REVIEW",
                "title": "BNS / BNSS / BSA — transitional review required",
                "reason": (
                    f"సంఘటన తేదీ {incident_date.strftime('%d-%m-%Y')}. "
                    "01-07-2024 తర్వాతి సంఘటనగా కనిపిస్తోంది. "
                    "అయితే pending proceeding/savings issue ఉంటే separately verify చేయాలి."
                )
            }

        return {
            "framework": "NEW_LAW",
            "title": "BNS / BNSS / BSA",
            "reason": (
                f"సంఘటన తేదీ {incident_date.strftime('%d-%m-%Y')}. "
                "01-07-2024 నుంచి కొత్త criminal laws అమలులో ఉన్నాయి."
            )
        }

    return {
        "framework": "OLD_LAW",
        "title": "IPC / CrPC / Indian Evidence Act",
        "reason": (
            f"సంఘటన తేదీ {incident_date.strftime('%d-%m-%Y')}. "
            "సంఘటన 01-07-2024 కంటే ముందు జరిగినట్లు కనిపిస్తోంది. "
            "Savings/transitional provisionsను facts ప్రకారం verify చేయాలి."
        )
    }


# =========================================================
# FILE EXTRACTION
# =========================================================

def extract_pdf_text(uploaded_file):
    try:
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)

        pages = []

        for page in reader.pages:
            try:
                text = page.extract_text()
                if text:
                    pages.append(text)
            except Exception:
                continue

        return "\n\n".join(pages)

    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_image_text(uploaded_file):
    try:
        import pytesseract

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
            return f"[OCR error: {e}]"

    except Exception as e:
        return f"[Image OCR error: {e}]"


def extract_text_file(uploaded_file):
    try:
        raw = uploaded_file.read()

        for encoding in ["utf-8", "utf-16", "cp1252"]:
            try:
                return raw.decode(encoding)
            except Exception:
                continue

        return raw.decode("utf-8", errors="ignore")

    except Exception as e:
        return f"[Text extraction error: {e}]"


def extract_uploaded_file(uploaded_file):
    if not uploaded_file:
        return ""

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)

    if filename.endswith(
        (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")
    ):
        return extract_image_text(uploaded_file)

    if filename.endswith(
        (".txt", ".csv", ".log")
    ):
        return extract_text_file(uploaded_file)

    return (
        "[Unsupported file type. "
        "PDF/JPG/JPEG/PNG/WEBP/TXT files మాత్రమే support చేయండి.]"
    )


# =========================================================
# VERIFIED LEGAL ANCHORS
# =========================================================

LEGAL_REFERENCE = """

IMPORTANT VERIFIED LEGAL ANCHORS
--------------------------------

These are legal anchors. Do NOT automatically apply all of them.
Select only those supported by the facts.

BNS:
318(1) - Cheating definition.
318(2) - Cheating; punishment up to 3 years, or fine, or both.
318(3) - Cheating where offender was bound by law/legal contract to protect
         the victim's interest; punishment up to 5 years, or fine, or both.
318(4) - Cheating with dishonest inducement to deliver property or make,
         alter or destroy valuable security etc.; punishment up to 7 years
         and fine.
319(1) - Cheating by personation definition.
319(2) - Cheating by personation; punishment up to 5 years, or fine, or both.

IMPORTANT:
Do NOT use BNS 318(4) merely because money was lost.
The analysis must identify dishonest inducement and delivery of property.

Do NOT use BNS 319 merely because a fraud occurred online.
There must be personation / pretending to be another person / substitution
or representation that one person is another.

INFORMATION TECHNOLOGY ACT, 2000:
Section 66C - Identity theft.
Section 66D - Cheating by personation using computer resource or communication
device.

IMPORTANT:
Do NOT automatically apply IT Act 66C or 66D to every UPI/bank/cyber fraud.
66C requires facts supporting identity theft as defined by the provision.
66D requires cheating by personation using computer resource/communication
device.

BSA:
Section 61 - Electronic or digital record.
Section 62 - Special provisions relating to electronic records.
Section 63 - Admissibility of electronic records.
Section 63(4) - Certificate requirements where electronic record is sought
to be admitted by virtue of Section 63.

IMPORTANT:
Do NOT say "every electronic evidence always requires BSA 63 certificate"
as a blanket rule.
Instead determine whether the particular electronic record is being relied
upon under Section 63 and whether the statutory certificate requirement
applies.

BNSS:
Section 173 - Information in cognizable cases.
Section 174 - Information relating to non-cognizable cases.
Section 175 - Police officer's power to investigate cognizable case.
Section 176 - Procedure for investigation.
Section 179 - Police officer's power to require attendance of witnesses.
Section 180 - Examination of witnesses by police.
Section 181 - Statements to police and use thereof.
Section 185 - Search by police officer.
Section 193 - Report of police officer on completion of investigation.

OLD LAW FRAMEWORK:
For incidents before commencement of the new criminal laws, examine IPC,
CrPC and Indian Evidence Act applicability, subject to repeal/savings and
transitional provisions.
"""


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = f"""
You are an expert Indian criminal-law and police-investigation analysis
assistant.

Your job is NOT to blindly generate sections.

You must analyse the complaint facts and identify the most legally appropriate
provisions, while clearly distinguishing:
1. Strongly supported sections
2. Possible/additional sections
3. Sections NOT supported by the facts

The output must be in SIMPLE PROFESSIONAL TELUGU.
Legal section names may be written in English where useful.

{LEGAL_REFERENCE}

============================================================
CRITICAL LEGAL ANALYSIS RULES
============================================================

RULE 1:
Do not invent a section merely because a keyword appears in the complaint.

RULE 2:
For every proposed substantive offence, explain the factual ingredients
which are satisfied.

RULE 3:
If an exact section cannot be determined from the complaint, say:
"Facts ఆధారంగా verification అవసరం."

RULE 4:
Never present a doubtful section as definitely applicable.

RULE 5:
For cheating cases distinguish:
- BNS 318(2)
- BNS 318(3)
- BNS 318(4)
- BNS 319(2)

RULE 6:
For cyber cases distinguish:
- BNS cheating/personation
- IT Act 66C
- IT Act 66D
Only recommend the IT Act provision when its ingredients are present.

RULE 7:
For electronic evidence identify:
- WhatsApp chats
- SMS
- Email
- Call records
- CCTV
- Mobile phone data
- UPI transaction records
- Bank statements
- Device extraction
- Social media records
- IP/login records
- Cloud records
- Screenshots

Then explain whether BSA Section 63 is relevant and whether a certificate
should be considered.

RULE 8:
Do not claim that a screenshot alone proves the identity of the sender.
Identify what additional evidence is required.

RULE 9:
For cognizable/non-cognizable, bailable/non-bailable and court:
Use the applicable statutory classification where known.
Do not guess.

RULE 10:
BNSS procedural sections should be suggested only when relevant to the
investigation step.

RULE 11:
Incident date is important for selecting the broad legal framework.
However, do NOT state that date alone mechanically resolves every
transitional/savings issue.

RULE 12:
If the complaint contains insufficient facts, clearly identify the missing
facts required for legal conclusion.

============================================================
INVESTIGATION APPROACH
============================================================

Analyse:

A. Occurrence / incident
B. Accused role
C. Victim role
D. Mens rea / dishonest intention
E. Actus reus
F. Property / money / document involved
G. Digital elements
H. Identity/personation elements
I. Evidence available
J. Evidence still required
K. Witnesses
L. Bank / UPI / telecom / platform records
M. CCTV / device evidence
N. Search/seizure requirements
O. BSA electronic evidence requirements
P. Investigation steps
Q. Possible sections
R. Sections that should NOT be mechanically added
S. Further facts required

============================================================
OUTPUT FORMAT
============================================================

# ⚖️ LEGAL & INVESTIGATION ANALYSIS

## 1. సంఘటన సారాంశం
Complaint factsను conciseగా చెప్పాలి.

## 2. సంఘటన తేదీ
- Detected date:
- Source phrase:
- Confidence:
- Reference date:
- Date verification required? Yes/No

## 3. Applicable Legal Framework
- BNS / BNSS / BSA OR old framework
- Reason

## 4. Primary Offence
Table:

| Section | Offence | Why applicable | Confidence |
|---|---|---|---|

## 5. Additional / Alternative Sections
Table:

| Section | Provision | When applicable | Confidence |
|---|---|---|---|

## 6. Sections NOT automatically applicable
Especially explain if BNS 319 / IT Act 66C / 66D are not supported.

## 7. Cognizable / Bailable / Court
Only where statutory classification is confidently established.
Otherwise state "Official Schedule verification required."

## 8. Digital Evidence
List:
- Device
- Chats
- Screenshots
- Bank/UPI
- CCTV
- Call records
- Email
- IP/logs
- Cloud/platform data

## 9. BSA Section 63 Analysis
Clearly state:
- Is electronic record being relied upon?
- Why Section 63 may be relevant?
- Is certificate requirement relevant?
- What source/device details should be preserved?
- Hash value / forensic preservation if relevant
- Who is the person/entity capable of supplying the required certificate,
  based on the source and statutory schedule
- Do not invent a particular certificate issuer when facts are insufficient.

## 10. Investigation Plan
Numbered steps.

## 11. Documents / Records to Obtain
Separate:
- Victim
- Bank
- UPI/payment intermediary
- Telecom
- Platform/social media
- CCTV
- Device/forensic

## 12. Witnesses
Who should be examined and what fact they can establish.

## 13. Missing Facts
Questions that investigator should verify.

## 14. Final Legal View
Use one of:
- Strongly supported
- Prima facie supported
- Requires further verification
- Facts insufficient

Add:
"This is a preliminary analytical aid and final legal decision must be
based on the complete case record and applicable law."

============================================================
LANGUAGE
============================================================

Use professional Telugu.
Do not use unnecessary English.
Use English for legal section titles where precision is improved.
"""


# =========================================================
# USER PROMPT BUILDER
# =========================================================

def build_user_prompt(
    case_text,
    extracted_text,
    reference_date,
    incident_date,
    incident_source,
    law_info,
    pending_case
):

    combined = ""

    if case_text:
        combined += "\n--- USER ENTERED COMPLAINT ---\n"
        combined += case_text

    if extracted_text:
        combined += "\n--- UPLOADED DOCUMENT / OCR TEXT ---\n"
        combined += extracted_text

    return f"""
Analyse the following police complaint/case.

REFERENCE DATE:
{reference_date.strftime('%d-%m-%Y')}

DETECTED INCIDENT DATE:
{incident_date.strftime('%d-%m-%Y') if incident_date else "NOT DETECTED"}

DATE SOURCE:
{incident_source if incident_source else "NOT DETECTED"}

LEGAL FRAMEWORK:
{law_info["title"]}

FRAMEWORK REASON:
{law_info["reason"]}

PENDING / TRANSITIONAL CASE FLAG:
{"YES - transitional/savings issue must be reviewed" if pending_case else "NO"}

IMPORTANT:
Do not simply repeat the legal anchors.
Apply them to the facts.

If incident date is not detected:
- Do not invent a date.
- State that date verification is required.
- Still analyse the complaint facts provisionally where possible.

If a cyber fraud is present:
- identify exactly what the accused allegedly did;
- identify whether personation exists;
- identify whether another person's identity credential was used;
- identify whether computer/communication resource was used;
- distinguish BNS 318 / 319 from IT Act 66C / 66D.

If electronic evidence exists:
- identify the evidence;
- explain BSA Section 63 relevance;
- explain preservation/certificate considerations;
- do not overstate certificate requirements.

CASE MATERIAL:
{combined}
"""


# =========================================================
# GROQ CALL
# =========================================================

def investigate_case(
    case_text,
    extracted_text,
    reference_date,
    incident_date,
    incident_source,
    law_info,
    pending_case
):

    user_prompt = build_user_prompt(
        case_text=case_text,
        extracted_text=extracted_text,
        reference_date=reference_date,
        incident_date=incident_date,
        incident_source=incident_source,
        law_info=law_info,
        pending_case=pending_case
    )

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            max_tokens=7000,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return (
            "❌ AI analysis failed.\n\n"
            f"Error: {str(e)}"
        )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Settings")

    st.info(
        "ఈ application preliminary legal-analysis aid మాత్రమే. "
        "Final legal decision complete case record మరియు applicable law "
        "ఆధారంగా చేయాలి."
    )

    st.markdown("### Supported")

    st.write("✅ Telugu complaints")
    st.write("✅ English complaints")
    st.write("✅ Photo OCR")
    st.write("✅ PDF text")
    st.write("✅ TXT files")
    st.write("✅ BNS / BNSS / BSA")
    st.write("✅ IT Act cyber analysis")
    st.write("✅ Incident date detection")


# =========================================================
# CASE DETAILS
# =========================================================

st.subheader("📝 1. Case / Complaint Details")

case_text = st.text_area(
    "Complaint / Case Details",
    height=260,
    placeholder=(
        "ఉదాహరణ:\n"
        "10-09-2026న నిందితుడు ఫిర్యాదుదారుని ఫోన్ చేసి...\n"
        "లేదా\n"
        "10 సెప్టెంబర్ 2026న UPI ద్వారా డబ్బులు మోసం చేశాడు..."
    )
)


# =========================================================
# REFERENCE DATE
# =========================================================

st.subheader("📅 2. Date Reference")

default_reference_date = date.today()

reference_date = st.date_input(
    "Complaintలో 'నిన్న', 'గత వారం' వంటి పదాలు ఉంటే reference date",
    value=default_reference_date
)


# =========================================================
# PENDING CASE
# =========================================================

pending_case = st.checkbox(
    "⚠️ ఇది పాత / pending proceeding / transitional matter కావచ్చు"
)


# =========================================================
# FILE UPLOAD
# =========================================================

st.subheader("📷 3. Photo / PDF / Text Upload")

uploaded_file = st.file_uploader(
    "Complaint copy / Photo / PDF / TXT upload చేయండి",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp",
        "tiff",
        "pdf",
        "txt",
        "csv",
        "log"
    ]
)


# =========================================================
# FILE PROCESSING
# =========================================================

extracted_text = ""

if uploaded_file:

    with st.spinner("📄 File చదువుతోంది..."):

        extracted_text = extract_uploaded_file(
            uploaded_file
        )

    if extracted_text:

        st.success("✅ File processing completed.")

        with st.expander("📄 Extracted / OCR Text చూడండి"):

            st.text_area(
                "Extracted Text",
                extracted_text,
                height=300
            )

    else:

        st.warning(
            "⚠️ File నుంచి text పొందలేకపోయాం."
        )


# =========================================================
# COMBINED TEXT
# =========================================================

combined_text = ""

if case_text:
    combined_text += case_text

if extracted_text:
    combined_text += "\n\n" + extracted_text


# =========================================================
# INCIDENT DATE
# =========================================================

st.subheader("📅 4. Incident Date Detection")

incident_date, incident_source = extract_incident_date(
    combined_text,
    reference_date
)


if incident_date:

    st.success(
        f"✅ Incident Date: "
        f"{incident_date.strftime('%d-%m-%Y')}"
    )

    if incident_source:
        st.caption(
            f"Detected from: {incident_source}"
        )

else:

    st.warning(
        "⚠️ Incident / occurrence date గుర్తించబడలేదు."
    )

    st.info(
        "Complaintలో occurrence date స్పష్టంగా ఉంటే "
        "10-09-2026 / 10 సెప్టెంబర్ 2026 / నిన్న వంటి రూపంలో "
        "ఉండేలా verify చేయండి."
    )


# =========================================================
# LAW FRAMEWORK
# =========================================================

law_info = select_law(
    incident_date,
    pending_case
)


st.subheader("⚖️ 5. Legal Framework")

st.info(
    f"**{law_info['title']}**\n\n"
    f"{law_info['reason']}"
)


# =========================================================
# DATE DEBUG
# =========================================================

with st.expander("🔎 Date Detection Debug"):

    st.write(
        "Reference Date:",
        reference_date.strftime("%d-%m-%Y")
    )

    st.write(
        "Detected Incident Date:",
        incident_date.strftime("%d-%m-%Y")
        if incident_date
        else "Not detected"
    )

    st.write(
        "Detected Source:",
        incident_source
        if incident_source
        else "Not detected"
    )


# =========================================================
# ANALYSE BUTTON
# =========================================================

st.subheader("🔍 6. Legal Analysis")

analyse_button = st.button(
    "⚖️ Generate Legal & Investigation Report",
    type="primary",
    use_container_width=True
)


# =========================================================
# ANALYSIS
# =========================================================

if analyse_button:

    if not combined_text.strip():

        st.error(
            "❌ Complaint details లేదా file content ఇవ్వండి."
        )

        st.stop()

    # -----------------------------------------------------
    # DATE WARNING
    # -----------------------------------------------------

    if not incident_date:

        st.warning(
            "⚠️ Incident date detect కాలేదు. "
            "Analysis కొనసాగించవచ్చు, కానీ applicable legal framework "
            "date-basedగా finalise చేయకూడదు."
        )

    # -----------------------------------------------------
    # AI CALL
    # -----------------------------------------------------

    with st.spinner(
        "⚖️ BNS / BNSS / BSA / IT Act provisions analyse చేస్తున్నాను..."
    ):

        result = investigate_case(
            case_text=case_text,
            extracted_text=extracted_text,
            reference_date=reference_date,
            incident_date=incident_date,
            incident_source=incident_source,
            law_info=law_info,
            pending_case=pending_case
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    st.markdown("---")

    st.subheader(
        "📋 Legal & Investigation Analysis Result"
    )

    st.markdown(result)

    # -----------------------------------------------------
    # DOWNLOAD REPORT
    # -----------------------------------------------------

    report_text = f"""
POLICE LEGAL & INVESTIGATION ASSISTANT
======================================

Reference Date:
{reference_date.strftime('%d-%m-%Y')}

Incident Date:
{
    incident_date.strftime('%d-%m-%Y')
    if incident_date
    else "Not detected"
}

Legal Framework:
{law_info["title"]}

Framework Reason:
{law_info["reason"]}

--------------------------------------
ANALYSIS
--------------------------------------

{result}

--------------------------------------
DISCLAIMER
--------------------------------------

This report is a preliminary analytical aid.
Final legal decision must be based on the complete case record,
applicable statutory provisions, judicial interpretation and
competent legal authority.
"""

    st.download_button(
        label="⬇️ Download Report as TXT",
        data=report_text,
        file_name="legal_investigation_report.txt",
        mime="text/plain",
        use_container_width=True
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "⚖️ Police Legal & Investigation Assistant | "
    "Preliminary analytical assistance only"
)
