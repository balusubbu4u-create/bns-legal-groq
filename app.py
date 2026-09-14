Police legal-research support tool.
Upgraded with Property/Theft rules, proper Date-Framework routing,
and structured BNS/BNSS/BSA & IPC/CrPC/IEA legal research guidelines.
"""
import io
import json
import os
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import streamlit as st
from groq import Groq
from PIL import Image

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

NEW_LAWS_START = date(2024, 7, 1)
MODEL_NAME = "llama-3.3-70b-versatile"
MAX_CHARS = 30_000
TELUGU_DIGITS = str.maketrans("౦౧౨౩౪౫౬౭౮౯", "0123456789")

ENGLISH_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
}
TELUGU_MONTHS = {
    "జనవరి": 1, "ఫిబ్రవరి": 2, "మార్చి": 3, "ఏప్రిల్": 4, "మే": 5, "జూన్": 6,
    "జులై": 7, "ఆగస్టు": 8, "సెప్టెంబర్": 9, "సెప్టెంబరు": 9, "అక్టోబర్": 10,
    "అక్టోబరు": 10, "నవంబర్": 11, "నవంబరు": 11, "డిసెంబర్": 12, "డిసెంబరు": 12
}

@dataclass(frozen=True)
class LegalRule:
    key: str
    statute: str
    section: str
    title: str
    ingredients: tuple[str, ...]
    fact_labels: dict[str, str]
    punishment: str
    cognizable: Optional[str] = None
    bailable: Optional[str] = None
    court: Optional[str] = None
    old_law_equivalent: str = ""
    official_source: str = ""
    notes: str = ""

BNS_SOURCE = "https://www.indiacode.nic.in/handle/123456789/20062"
BNSS_SOURCE = "https://www.indiacode.nic.in/handle/123456789/20099"
BSA_SOURCE = "https://www.indiacode.nic.in/handle/123456789/20063"
IT_SOURCE = "https://www.indiacode.nic.in/handle/123456789/15442"
RULESET_VERSION = "2026-09-14 / official-text baseline"

CASE_HEADS = (
    ("Theft_HouseBreaking", "Theft & House-Breaking / దొంగతనం & కన్నం వేయడం"),
    ("Property", "Property Offences / ఆస్తి నేరాలు"),
    ("Women", "Offences against Women / మహిళలపై నేరాలు"),
    ("Children", "Offences against Children / బాలలపై నేరాలు (including POCSO)"),
    ("Road", "Road Accidents & Motor-Vehicle Offences / రోడ్డు ప్రమాదాలు"),
    ("Body", "Offences against Human Body / వ్యక్తిపై నేరాలు"),
    ("Financial", "Cheating & Financial Fraud / మోసం మరియు ఆర్థిక నేరాలు"),
    ("Cyber", "Cybercrime / సైబర్ నేరాలు"),
    ("Arms", "Arms & Explosives / ఆయుధాలు మరియు పేలుడు పదార్థాలు"),
    ("Domestic", "Domestic Violence & Family Offences / కుటుంబ హింస"),
)

# విస్తరించిన లీగల్ రూల్స్ (Theft, House-breaking & Cheating)
LEGAL_RULES = (
    LegalRule(
        "bns_303_2", "BNS 2023", "303(2)", "Theft (సాధారణ దొంగతనం)",
        ("dishonest_intention", "movable_property", "taken_without_consent"),
        {
            "dishonest_intention": "Dishonest intention to take movable property is established",
            "movable_property": "Movable property is involved (gold, cash, mobile, etc.)",
            "taken_without_consent": "Property moved/taken out of possession without person's consent"
        },
        "Up to 3 years, or fine, or both.", "Cognizable", "Non-bailable", "Any Magistrate",
        "IPC 379", BNS_SOURCE, "Simple theft of movable property."
    ),
    LegalRule(
        "bns_305", "BNS 2023", "305", "Theft in dwelling house, etc. (నివాస గృహంలో దొంగతనం)",
        ("dishonest_intention", "movable_property", "taken_without_consent", "dwelling_house_or_building"),
        {
            "dishonest_intention": "Dishonest intention to take property",
            "movable_property": "Movable property is involved",
            "taken_without_consent": "Taken without consent",
            "dwelling_house_or_building": "Theft committed in any building, tent or vessel used as human dwelling or custody of property"
        },
        "Up to 7 years and fine.", "Cognizable", "Non-bailable", "Magistrate of the First Class",
        "IPC 380", BNS_SOURCE, "Theft inside residence/house."
    ),
    LegalRule(
        "bns_331_3", "BNS 2023", "331(3)", "Lurking house-trespass or house-breaking by night (రాత్రివేళ ఇంటిలోకి చొరబడటం/కన్నం వేయడం)",
        ("house_trespass", "by_night_or_concealment"),
        {
            "house_trespass": "House trespass or breaking open door/lock/bolt is verified",
            "by_night_or_concealment": "Committed after sunset and before sunrise, or having taken precautions of concealment"
        },
        "Up to 3 years and fine.", "Cognizable", "Non-bailable", "Any Magistrate",
        "IPC 456 / 457", BNS_SOURCE, "Entering dwelling house surreptitiously or by force at night."
    ),
    LegalRule(
        "bns_331_4", "BNS 2023", "331(4)", "House-breaking by night in order to commit offence (దొంగతనం కోసం రాత్రివేళ తాళాలు తీసి చొరబడటం)",
        ("house_trespass", "by_night_or_concealment", "intent_to_commit_theft"),
        {
            "house_trespass": "House trespass or house-breaking (e.g. back door bolt opened)",
            "by_night_or_concealment": "Committed by night",
            "intent_to_commit_theft": "Committed in order to the committing of any offence punishable with imprisonment (Theft)"
        },
        "Up to 14 years and fine (if theft).", "Cognizable", "Non-bailable", "Magistrate of the First Class",
        "IPC 457", BNS_SOURCE, "Lurking house-trespass/house-breaking by night with intent to commit theft."
    ),
    LegalRule(
        "bns_318_4", "BNS 2023", "318(4)", "Cheating & dishonestly inducing delivery of property",
        ("deception", "fraudulent_or_dishonest_inducement", "delivery_of_property_or_valuable_security"),
        {
            "deception": "A specific deception is verified",
            "fraudulent_or_dishonest_inducement": "Facts support fraudulent/dishonest inducement",
            "delivery_of_property_or_valuable_security": "Delivery of property induced"
        },
        "Up to 7 years and fine.", "Cognizable", "Non-bailable", "Magistrate of the First Class",
        "IPC 420", BNS_SOURCE, "Cheating with delivery of property."
    ),
    LegalRule(
        "it_66c", "IT Act 2000", "66C", "Identity theft (గుర్తింపు చోరీ / పాస్‌వర్డ్ / సిమ్ దుర్వినియోగం)",
        ("fraudulent_or_dishonest_use", "electronic_identifier_used"),
        {
            "fraudulent_or_dishonest_use": "Fraudulent or dishonest use is verified",
            "electronic_identifier_used": "Another person's electronic signature, password, SIM/unique identity used"
        },
        "Up to 3 years and fine up to 1 lakh.", "Cognizable", "Bailable", "Magistrate First Class",
        "IT Act 66C", IT_SOURCE, "Digital identity/credential theft."
    )
)

def framework_for(incident_date: Optional[date]) -> tuple[str, str]:
    if incident_date is None:
        return (
            "సంఘటన తేదీ ధృవీకరించబడలేదు — వర్తించే చట్టపరమైన ఫ్రేమ్‌వర్క్ పరిశీలనలో ఉంది.",
            "BOTH"
        )
    if incident_date >= NEW_LAWS_START:
        return (
            f"01-07-2024 తర్వాతి సంఘటన ({incident_date.strftime('%d-%m-%Y')}) -> వర్తించే చట్టాలు: BNS, 2023 + BNSS, 2023 + BSA, 2023.",
            "NEW"
        )
    return (
        f"01-07-2024 ముందరి సంఘటన ({incident_date.strftime('%d-%m-%Y')}) -> నిబంధనల ప్రకారం ప్రాథమికంగా IPC + CrPC + Indian Evidence Act వర్తిస్తాయి (పరిశీలనార్థం BNS/BNSS సమాన సెక్షన్లు ఇవ్వబడతాయి).",
        "OLD"
    )

def _valid_date(year: int, month: int, day: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None

def find_date_candidates(text: str, reference: date) -> list[tuple[date, str]]:
    text = (text or "").translate(TELUGU_DIGITS)
    found: list[tuple[date, str]] = []
    for matched in re.finditer(r"\b(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b", text):
        value = matched.group(0)
        parts = [int(x) for x in re.split(r"[-/.]", value)]
        parsed = _valid_date(*parts) if len(str(parts[0])) == 4 else _valid_date(parts[2], parts[1], parts[0])
        if parsed:
            found.append((parsed, f"Explicit date: {value}"))
    names = {**ENGLISH_MONTHS, **TELUGU_MONTHS}
    choices = "|".join(re.escape(x) for x in sorted(names, key=len, reverse=True))
    for pattern, month_first in ((rf"(?<!\d)(\d{{1,2}})\s+({choices})\s*,?\s*(\d{{4}})(?!\d)", False),
                                 (rf"({choices})\s+(\d{{1,2}})\s*,?\s*(\d{{4}})(?!\d)", True)):
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            a, b, year = match.groups()
            month_name, day = (a, b) if month_first else (b, a)
            month = names.get(month_name.lower()) or names.get(month_name)
            parsed = _valid_date(int(year), month, int(day)) if month else None
            if parsed:
                found.append((parsed, f"Explicit named-month date: {match.group(0)}"))
    return found

def text_limit(value: str) -> str:
    return value[:MAX_CHARS] + "\n[Truncated by application.]" if len(value) > MAX_CHARS else value

def extract_upload(uploaded) -> tuple[str, str]:
    if uploaded is None:
        return "", ""
    name, raw = uploaded.name.lower(), uploaded.getvalue()
    try:
        if name.endswith(".pdf"):
            if not PDF_AVAILABLE:
                return "", "PDF text extraction is unavailable (install pypdf)."
            result = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
            return (text_limit(result), "") if result.strip() else ("", "PDF has no selectable text.")
        if name.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):
            if not OCR_AVAILABLE:
                return "", "OCR is unavailable (install pytesseract)."
            image = Image.open(io.BytesIO(raw))
            for language in ("tel+eng", "eng"):
                try:
                    result = pytesseract.image_to_string(image, lang=language)
                    if result.strip():
                        return text_limit(result), ""
                except Exception:
                    continue
            return "", "OCR could not read this image."
        if name.endswith((".txt", ".csv", ".log")):
            for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
                try:
                    return text_limit(raw.decode(encoding)), ""
                except UnicodeDecodeError:
                    pass
        return "", "Unsupported file type."
    except Exception as exc:
        return "", f"Extraction failed: {exc}"

def rule_status(rule: LegalRule, facts: dict[str, bool]) -> tuple[str, list[str]]:
    missing = [rule.fact_labels[k] for k in rule.ingredients if not facts.get(k, False)]
    return ("PRIMA_FACIE_GATE_PASSED" if not missing else "REQUIRES_VERIFICATION", missing)

def assessment(facts: dict[str, bool], incident_date: Optional[date]) -> list[dict]:
    # 01-07-2024 ముందరైనా కాకపోయినా రూల్స్ ని అసెస్ చేసి పాత & కొత్త సెక్షన్లు రెండింటినీ చూపిస్తుంది
    rows = []
    for rule in LEGAL_RULES:
        status, missing = rule_status(rule, facts)
        rows.append({
            "rule": rule,
            "status": status,
            "missing": missing
        })
    return rows

def groq_client() -> Optional[Groq]:
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None
    key = key or os.getenv("GROQ_API_KEY")
    return Groq(api_key=key) if key else None

def extract_case_facts(material: str) -> tuple[Optional[dict], str]:
    client = groq_client()
    if not client:
        return None, "GROQ_API_KEY is not configured."
    fact_keys = {key: label for rule in LEGAL_RULES for key, label in rule.fact_labels.items()}
    schema = {key: {"supported": False, "quotes": []} for key in fact_keys}
    prompt = f"""You are a precise legal fact-extractor for Indian criminal investigations.
Extract facts from the untrusted material. Return JSON only, with no markdown.

Required JSON format:
{{
  "occurrence_date_iso": "YYYY-MM-DD or null",
  "occurrence_date_basis": "short note on date found",
  "case_heads": [{{"head": "head_key", "quotes": ["quote"]}}],
  "facts": {json.dumps(schema, ensure_ascii=False)},
  "missing_or_ambiguous": []
}}

Rules:
- Mark a fact true only if supported by the text directly or by prima-facie inference. Provide verbatim quotes.
- Date must be the incident occurrence date (not FIR date).
- If gold, money, mobile taken: mark movable_property=true, dishonest_intention=true, taken_without_consent=true.
- If house back door/lock opened: dwelling_house_or_building=true, house_trespass=true.
- If between 11 PM and 6 AM: by_night_or_concealment=true.

Fact definitions: {json.dumps(fact_keys, ensure_ascii=False)}
Allowed case heads: {json.dumps(dict(CASE_HEADS), ensure_ascii=False)}

<CASE_MATERIAL>
{material}
</CASE_MATERIAL>"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3500
        )
        content = response.choices[0].message.content or ""
        match = re.search(r"\{[\s\S]*\}", content)
        extracted = json.loads(match.group(0) if match else content)
        return extracted, ""
    except Exception as exc:
        return None, f"Fact extraction failed: {exc}"

def cited_facts(extracted: dict) -> tuple[dict[str, bool], list[dict]]:
    facts: dict[str, bool] = {}
    trace: list[dict] = []
    for rule in LEGAL_RULES:
        for key, label in rule.fact_labels.items():
            if key in facts:
                continue
            item = extracted.get("facts", {}).get(key, {})
            quotes = item.get("quotes", []) if isinstance(item, dict) else []
            supported = bool(item.get("supported")) and isinstance(quotes, list) and any(str(q).strip() for q in quotes)
            facts[key] = supported
            trace.append({
                "Statutory fact": label,
                "Machine assessment": "Directly supported by facts" if supported else "Not established in material",
                "Source quotation(s)": " | ".join(str(q) for q in quotes[:2]) if supported else "—"
            })
    return facts, trace

def extracted_occurrence_date(extracted: dict) -> Optional[date]:
    value = extracted.get("occurrence_date_iso")
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None

def safe_model_prompt(material: str, incident_date: Optional[date], results: list[dict]) -> str:
    framework_text, regime = framework_for(incident_date)
    
    passed_sections = []
    verify_sections = []
    for item in results:
        r = item["rule"]
        entry = f"{r.statute} Sec {r.section} (Equivalent: {r.old_law_equivalent}) - {r.title}"
        if item["status"] == "PRIMA_FACIE_GATE_PASSED":
            passed_sections.append(entry)
        else:
            verify_sections.append(entry)

    return f"""
మీరు భారతదేశంలో పనిచేస్తున్న ఒక అనుభవజ్ఞుడైన సీనియర్ పోలీస్ ఇన్వెస్టిగేషన్ ఆఫీసర్ మరియు లీగల్ ఎక్స్‌పర్ట్.
క్రింది కేసు దస్త్రాన్ని క్షుణ్ణంగా పరిశీలించి స్పష్టమైన, సాధికారిక తెలుగులో దర్యాప్తు నివేదికను రూపొందించండి.

సంఘటన వివరాలు:
- వర్కింగ్ సంఘటన తేదీ: {incident_date.strftime('%d-%m-%Y') if incident_date else 'ధృవీకరించబడలేదు'}
- వర్తించే చట్టం: {framework_text}
- పాలన విధానం (Regime): {regime} (సంఘటన 01-07-2024 ముందైతే FIR చట్టపరంగా IPC క్రింద నమోదు కావాలి, అయితే ప్రస్తుత తులనాత్మక అధ్యయనం కొరకు BNS సమాన సెక్షన్లను కూడా వివరించండి).

రూల్ ఇంజిన్ ఫలితాలు:
- PRIMA FACIE గా నిర్ధారించబడిన సెక్షన్లు: {', '.join(passed_sections) or 'None'}
- పరిశీలనలో ఉన్న సెక్షన్లు: {', '.join(verify_sections) or 'None'}

ముఖ్యమైన సూచన: 
BSA అంటే "భారతీయ సాక్ష్య అధినియం, 2023" (Bharatiya Sakshya Adhiniyam) మాత్రమే. ఎలక్ట్రానిక్ రికార్డులకు BSA Section 63 (పాత IEA 65B కి సమానం) నిబంధనలు వర్తిస్తాయి.

క్రింది శీర్షికలతో పూర్తి నివేదిక ఇవ్వండి:
1. సంఘటన సారాంశం (ఫిర్యాది, నిందితులు, పోయిన సొత్తు వివరాలు)
2. తేదీలు మరియు సమయ కాలవ్యవధి ధృవీకరణ (FIR నమోదులో జాప్యం ఉందా?)
3. వర్తించే చట్టపరమైన ఫ్రేమ్‌వర్క్ (IPC వర్సెస్ BNS మ్యాపింగ్)
4. ప్రాథమిక నేర విభాగాలు (Theft & Night House-breaking సెక్షన్ల పూర్తి విశ్లేషణ)
5. సెక్షన్ల వర్గీకరణ (Cognizable / Bailable / ఏ మెజిస్ట్రేట్ కోర్టు విచారిస్తుంది?)
6. ఎలక్ట్రానిక్ మరియు డిజిటల్ సాక్ష్యాలు (మొబైల్ ఫోన్, IMEI, CDR, టవర్ లొకేషన్)
7. BSA Section 63 / IEA Section 65B సర్టిఫికేషన్ మార్గదర్శకాలు
8. దర్యాప్తు అధికారికి (IO) సమగ్ర దర్యాప్తు ప్రణాళిక (Crime scene inspection, Fingerprints, Clues team, రికవరీ ప్రొసీజర్)
9. సంప్రదించాల్సిన రికార్డులు & నోటీసులు (BNSS Sec 94/CrPC Sec 91 క్రింద టెలికాం సర్వీస్ ప్రొవైడర్లకు నోటీసులు)
10. సాక్షుల విచారణ ప్రణాళిక (పంచనామా, రికవరీ పంచలు)
11. తక్షణ కార్యాచరణ సారాంశం (Final Legal & Investigation View)

<CASE_MATERIAL>
{material}
</CASE_MATERIAL>
"""

def run_analysis(material: str, prompt: str) -> str:
    client = groq_client()
    if not client:
        return "GROQ_API_KEY అమర్చబడలేదు."
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=5000
        )
        return response.choices[0].message.content or "సమాధానం లభించలేదు."
    except Exception as exc:
        return f"Groq API లోపం: {exc}"

# UI సెటప్
st.set_page_config(page_title="పోలీస్ లీగల్ రీసెర్చ్ సపోర్ట్", page_icon="⚖️", layout="wide")
st.title("⚖️ పోలీస్ లీగల్ రీసెర్చ్ & దర్యాప్తు మార్గదర్శక టూల్")
st.caption("BNS/BNSS/BSA & IPC/CrPC/IEA న్యాయ పరిశోధనా వేదిక — నిర్ణయాత్మక పోలీసు దర్యాప్తు సహకారం.")

complaint = st.text_area("ఫిర్యాదు వివరాలు / Complaint Text", height=200, max_chars=MAX_CHARS)
uploaded = st.file_uploader("ఫిర్యాదు కాపీ అప్‌లోడ్ చేయండి (PDF, Image, Text)", type=["jpg", "jpeg", "png", "webp", "pdf", "txt"])

extracted, extraction_error = extract_upload(uploaded)
if extraction_error:
    st.error(extraction_error)
elif uploaded:
    with st.expander("అప్‌లోడ్ చేసిన ఫైల్ నుండి సేకరించిన టెక్స్ట్ (Extracted / OCR)"):
        st.text_area("File Text", extracted, height=150, disabled=True)

consent = st.checkbox("ఈ కేసుకు సంబంధించిన వివరాలను AI ద్వారా విశ్లేషించడానికి మరియు పరిశోధించడానికి అంగీకరిస్తున్నాను.")

if st.button("⚖️ చట్టపరమైన విశ్లేషణ మరియు దర్యాప్తు మార్గదర్శకాలను రూపొందించండి", type="primary", use_container_width=True):
    material = "COMPLAINT:\n" + text_limit(complaint) + "\n\nEXTRACTED FILE TEXT:\n" + extracted
    if not (complaint.strip() or extracted.strip()):
        st.error("దయచేసి ఫిర్యాదు టెక్స్ట్‌ను నమోదు చేయండి లేదా సరైన ఫైల్‌ను అప్‌లోడ్ చేయండి.")
    elif not consent:
        st.error("దయచేసి విశ్లేషణ కోసం పై చెక్‌బాక్స్‌ను క్లిక్ చేసి అనుమతి ఇవ్వండి.")
    else:
        with st.spinner("సాక్ష్యాధారాలు, చట్టపరమైన సెక్షన్లు మరియు నిబంధనలు విశ్లేషించబడుతున్నాయి..."):
            extracted_facts, fact_error = extract_case_facts(material)

        if fact_error or extracted_facts is None:
            st.error(fact_error or "ఫ్యాక్ట్స్ సేకరించడం సాధ్యపడలేదు.")
        else:
            incident_date = extracted_occurrence_date(extracted_facts)
            facts, trace = cited_facts(extracted_facts)
            results = assessment(facts, incident_date)
            
            # 1. తారీఖు మరియు ఫ్రేమ్‌వర్క్ బ్యానర్
            framework_title, regime = framework_for(incident_date)
            st.subheader("📅 సంఘటన తేదీ & చట్టపరమైన పరిధి")
            if incident_date:
                st.info(f"గుర్తించిన సంఘటన తేదీ: **{incident_date:%d-%m-%Y}** ({framework_title})")
            else:
                st.warning(framework_title)

            # 2. రూల్ ఇంజిన్ టేబుల్
            st.subheader("📊 ఆటోమేటెడ్ రూల్ అసెస్‌మెంట్ (Sections Verified)")
            table = []
            for item in results:
                rule = item["rule"]
                status_label = "✅ Prima Facie వర్తిస్తుంది" if item["status"] == "PRIMA_FACIE_GATE_PASSED" else "⚠️ మరిన్ని వివరాలు అవసరం"
                table.append({
                    "చట్టం & సెక్షన్": f"{rule.statute} Sec {rule.section}",
                    "పాత చట్టం (IPC/IT)": rule.old_law_equivalent,
                    "నేర వివరణ": rule.title,
                    "పరిస్థితి": status_label,
                    "శిక్ష / క్లాసిఫికేషన్": f"{rule.punishment} ({rule.cognizable}, {rule.bailable})"
                })
            st.dataframe(table, use_container_width=True, hide_index=True)

            # 3. AI సమగ్ర ఇన్వెస్టిగేషన్ రిపోర్ట్
            with st.spinner("పూర్తి లీగల్ రిపోర్ట్ & దర్యాప్తు ఆదేశాలు రూపొందించబడుతున్నాయి..."):
                report = run_analysis(material, safe_model_prompt(material, incident_date, results))
            
            st.subheader("📋 పోలీసు దర్యాప్తు సమగ్ర నివేదిక & మార్గదర్శకాలు")
            st.markdown(report)
            st.download_button("రిపోర్ట్‌ను డౌన్‌లోడ్ చేసుకోండి (TXT)", data=report, file_name="police_investigation_report.txt", mime="text/plain", use_container_width=True)

st.caption("గమనిక: ఈ నివేదిక పోలీసు అధికారుల చట్టపరమైన పరిశోధన మరియు దర్యాప్తు మార్గదర్శకత్వం కొరకు మాత్రమే. తుది చార్జిషీట్/ఎఫ్ఐఆర్ నమోదులో చట్ట నిబంధనలను స్వతంత్రంగా పరిశీలించండి.")
