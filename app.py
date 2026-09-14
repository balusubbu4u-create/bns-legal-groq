Comprehensive Police Legal Research & Investigation Support Tool.
Supports all criminal offence categories under BNS, BNSS, BSA and IPC, CrPC, IEA.
Handles PDF, JPG, PNG, Screenshots, and plain-text complaint sources.
"""
import io
import json
import os
import re
from dataclasses import dataclass
from datetime import date
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

@dataclass(frozen=True)
class LegalRule:
    key: str
    statute: str
    section: str
    title: str
    ingredients: tuple[str, ...]
    fact_labels: dict[str, str]
    punishment: str
    cognizable: str
    bailable: str
    court: str
    old_law_equivalent: str

LEGAL_RULES = (
    LegalRule(
        "bns_303_2", "BNS 2023", "303(2)", "సాధారణ దొంగతనం (Theft)",
        ("dishonest_intention", "movable_property", "taken_without_consent"),
        {"dishonest_intention": "దురుద్దేశం ధృవీకరించబడింది", "movable_property": "చరాస్తి", "taken_without_consent": "సమ్మతి లేకుండా తీసుకున్నారు"},
        "3 సంవత్సరాల వరకు జైలు, లేదా జరిమానా, లేదా రెండూ.", "Cognizable", "Non-bailable", "Any Magistrate", "IPC 379"
    ),
    LegalRule(
        "bns_305", "BNS 2023", "305", "నివాస గృహంలో దొంగతనం (Theft in dwelling house)",
        ("dishonest_intention", "movable_property", "taken_without_consent", "dwelling_house"),
        {"dishonest_intention": "దురుద్దేశం ధృవీకరించబడింది", "movable_property": "చరాస్తి ఉంది", "taken_without_consent": "సమ్మతి లేకుండా", "dwelling_house": "నివాస గృహంలో జరిగింది"},
        "7 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 380"
    ),
    LegalRule(
        "bns_331_4", "BNS 2023", "331(4)", "రాత్రివేళ తాళాలు తీసి/కన్నం వేసి దొంగతనానికి చొరబడటం (House-breaking by night)",
        ("house_trespass", "by_night", "intent_to_theft"),
        {"house_trespass": "గృహ ప్రవేశం", "by_night": "రాత్రివేళ జరిగింది", "intent_to_theft": "దొంగతనం ఉద్దేశం"},
        "14 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 457"
    ),
    LegalRule(
        "bns_318_4", "BNS 2023", "318(4)", "మోసగించి ఆస్తి డెలివరీ చేయించడం (Cheating)",
        ("deception", "fraudulent_inducement", "property_delivered"),
        {"deception": "వంచన/మోసం రుజువైంది", "fraudulent_inducement": "ప్రేరేపించడం", "property_delivered": "ఆస్తి డెలివరీ"},
        "7 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 420"
    ),
    LegalRule(
        "bns_115_2", "BNS 2023", "115(2)", "స్వచ్ఛందంగా గాయపరచడం (Voluntarily causing hurt)",
        ("causing_hurt", "intentional_act"),
        {"causing_hurt": "శారీరక గాయం", "intentional_act": "ఉద్దేశపూర్వక చర్య"},
        "1 సంవత్సరం వరకు జైలు లేదా జరిమానా.", "Non-cognizable", "Bailable", "Any Magistrate", "IPC 323"
    ),
    LegalRule(
        "bns_109", "BNS 2023", "109", "హత్యాయత్నం (Attempt to Murder)",
        ("act_done_with_intent", "capability_to_cause_death"),
        {"act_done_with_intent": "చంపాలనే ఉద్దేశంతో దాడి", "capability_to_cause_death": "ప్రాణాంతక చర్య"},
        "10 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Court of Session", "IPC 307"
    ),
    LegalRule(
        "bns_85", "BNS 2023", "85", "భర్త లేదా బంధువులచే క్రూరత్వం (Cruelty by husband/relatives)",
        ("woman_subjected_to_cruelty", "harassment_for_dowry_or_coercion"),
        {"woman_subjected_to_cruelty": "మహిళను వేధించడం", "harassment_for_dowry_or_coercion": "కట్నం వేధింపులు"},
        "3 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 498A"
    ),
    LegalRule(
        "it_66c", "IT Act 2000", "66C", "గుర్తింపు చోరీ / పాస్‌వర్డ్ దుర్వినియోగం (Identity Theft)",
        ("fraudulent_use", "electronic_identifier"),
        {"fraudulent_use": "దురుద్దేశపూర్వక ఉపయోగం", "electronic_identifier": "పాస్‌వర్డ్/సిమ్/ఓటీపీ చోరీ"},
        "3 సంవత్సరాల వరకు జైలు మరియు 1 లక్ష జరిమానా.", "Cognizable", "Bailable", "Magistrate First Class", "IT Act 66C"
    ),
    LegalRule(
        "bns_106_1", "BNS 2023", "106(1)", "నిర్లక్ష్యం వల్ల మరణం (Causing death by negligence)",
        ("death_caused", "rash_or_negligent_act"),
        {"death_caused": "మరణం సంభవించడం", "rash_or_negligent_act": "నిర్లక్ష్యపు చర్య"},
        "5 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Bailable", "Magistrate First Class", "IPC 304A"
    )
)

def framework_for(incident_date: Optional[date]) -> tuple[str, str]:
    if incident_date is None:
        return ("సంఘటన తేదీ నిర్ధారించబడలేదు. BNS మరియు IPC రెండింటి సమగ్ర పరిశీలన అవసరం.", "BOTH")
    if incident_date >= NEW_LAWS_START:
        return (f"01-07-2024 తర్వాత జరిగిన సంఘటన ({incident_date.strftime('%d-%m-%Y')}). చట్టాలు: BNS, 2023 + BNSS, 2023 + BSA, 2023.", "NEW")
    return (f"01-07-2024 కు ముందు జరిగిన సంఘటన ({incident_date.strftime('%d-%m-%Y')}). చట్టాలు: IPC + CrPC + IEA.", "OLD")

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
            return (text_limit(result), "") if result.strip() else ("", "PDF లో టెక్స్ట్ లభించలేదు.")
        if name.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):
            if not OCR_AVAILABLE:
                return "", "OCR అందుబాటులో లేదు."
            image = Image.open(io.BytesIO(raw))
            for language in ("tel+eng", "eng"):
                try:
                    result = pytesseract.image_to_string(image, lang=language)
                    if result.strip():
                        return text_limit(result), ""
                except Exception:
                    continue
            return "", "చిత్రం నుండి టెక్స్ట్ చదవలేకపోయాము."
        if name.endswith((".txt", ".csv", ".log")):
            for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
                try:
                    return text_limit(raw.decode(encoding)), ""
                except UnicodeDecodeError:
                    pass
        return "", "సపోర్ట్ చేయని ఫైల్ ఫార్మాట్."
    except Exception as exc:
        return "", f"ఫైల్ రీడింగ్ లోపం: {exc}"

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
        return None, "GROQ_API_KEY కాన్ఫిగర్ చేయబడలేదు."
    
    fact_keys = {key: label for rule in LEGAL_RULES for key, label in rule.fact_labels.items()}
    schema = {key: {"supported": False, "quotes": []} for key in fact_keys}
    
    prompt = (
        "You are an Indian police legal-research AI.\n"
        "Extract facts from the following untrusted case complaint. Return JSON only, with no markdown fences.\n\n"
        "Required JSON structure:\n"
        "{\n"
        '  "occurrence_date_iso": "YYYY-MM-DD or null",\n'
        '  "occurrence_date_basis": "string explaining how occurrence date was found",\n'
        '  "offence_nature": "e.g. Theft, House Breaking, Cheating, Hurt, Murder Attempt, Cyber Crime, Accident",\n'
        f'  "facts": {json.dumps(schema, ensure_ascii=False)}\n'
        "}\n\n"
        "Guidelines:\n"
        "- If incident date is stated, convert to YYYY-MM-DD format.\n"
        "- Set fact supported: true if directly stated or inferred, and provide verbatim quote in quotes.\n"
        f"Fact keys to check: {json.dumps(fact_keys, ensure_ascii=False)}\n\n"
        "<CASE_MATERIAL>\n"
        f"{material}\n"
        "</CASE_MATERIAL>"
    )

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

def assessment(extracted: dict) -> list[dict]:
    facts_dict = extracted.get("facts", {})
    rows = []
    for rule in LEGAL_RULES:
        missing = []
        for ing in rule.ingredients:
            item = facts_dict.get(ing, {})
            supported = bool(item.get("supported")) if isinstance(item, dict) else False
            if not supported:
                missing.append(rule.fact_labels.get(ing, ing))
        
        status = "PRIMA_FACIE_GATE_PASSED" if not missing else "REQUIRES_VERIFICATION"
        rows.append({
            "rule": rule,
            "status": status,
            "missing": missing
        })
    return rows

def build_investigation_prompt(material: str, incident_date: Optional[date], results: list[dict], offence_nature: str) -> str:
    framework_text, regime = framework_for(incident_date)
    
    passed_rules = [f"{r['rule'].statute} Sec {r['rule'].section} (సమాన IPC: {r['rule'].old_law_equivalent}) - {r['rule'].title}" 
                    for r in results if r["status"] == "PRIMA_FACIE_GATE_PASSED"]
    
    date_str = incident_date.strftime('%d-%m-%Y') if incident_date else "ధృవీకరించబడలేదు"
    passed_str = ", ".join(passed_rules) if passed_rules else "ప్రత్యేక రూల్ ఇంజిన్ సెక్షన్లు సరిపోలలేదు."

    return (
        "మీరు భారతదేశంలో పనిచేస్తున్న సీనియర్ పోలీస్ ఇన్వెస్టిగేషన్ ఆఫీసర్ (IO) మరియు క్రిమినల్ లీగల్ ఎక్స్‌పర్ట్.\n"
        "క్రింద ఇవ్వబడిన ఫిర్యాదు వివరాలను పరిశీలించి స్పష్టమైన తెలుగులో పూర్తి పోలీస్ దర్యాప్తు మార్గదర్శక నివేదికను రూపొందించండి.\n\n"
        f"సంఘటన వివరాలు:\n"
        f"- సంఘటన స్వభావం: {offence_nature}\n"
        f"- సంఘటన జరిగిన తేదీ: {date_str}\n"
        f"- చట్టపరమైన ఫ్రేమ్‌వర్క్: {framework_text}\n"
        f"- పాలన విధానం: {regime}\n"
        f"- ప్రాథమికంగా సరిపోలిన సెక్షన్లు: {passed_str}\n\n"
        "ముఖ్యమైన నిబంధన:\n"
        "- BSA అంటే 'భారతీయ సాక్ష్య అధినియం, 2023'. ఎలక్ట్రానిక్ సాక్ష్యాలకు BSA Section 63 సర్టిఫికేషన్ తప్పనిసరి.\n\n"
        "క్రింది క్రమంలో పూర్తి స్థాయి పోలీస్ దర్యాప్తు నివేదిక ఇవ్వండి:\n"
        "1. ఫిర్యాదు సారాంశం (ఫిర్యాది, నిందితులు, పోయిన వస్తువులు/నష్టం వివరాలు).\n"
        "2. తేదీలు మరియు కాలవ్యవధి విశ్లేషణ (ఎఫ్ఐఆర్ నమోదులో జాప్యం ఉంటే వివరణ).\n"
        "3. వర్తించే చట్టపరమైన సెక్షన్ల పూర్తి విశ్లేషణ (BNS & IPC సెక్షన్లు, Cognizable/Bailable వివరాలు).\n"
        "4. పోలీసు దర్యాప్తు మార్గదర్శకాలు (ఘటనా స్థల పరిశీలన, క్లూస్ టీమ్, వేలిముద్రలు, అరెస్ట్ నిబంధనలు).\n"
        "5. సాక్ష్యాధారాల సేకరణ & రికవరీ ప్రొసీజర్ (రికవరీ పంచనామా, సాక్షులు).\n"
        "6. డిజిటల్ & సైబర్ సాక్ష్యాలు (మొబైల్ IMEI, CDR, సీసీటీవీ ఫుటేజ్, BSA Sec 63 సర్టిఫికేట్).\n"
        "7. సాక్షుల విచారణ ప్రణాళిక (వాంగ్మూలాల నమోదు).\n"
        "8. ముగింపు & తక్షణ కార్యాచరణ (IO తక్షణమే చేపట్టవలసిన చర్యలు).\n\n"
        "<CASE_MATERIAL>\n"
        f"{material}\n"
        "</CASE_MATERIAL>"
    )

def run_analysis(material: str, prompt: str) -> str:
    client = groq_client()
    if not client:
        return "GROQ_API_KEY కాన్ఫిగర్ చేయబడలేదు."
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

# Streamlit UI
st.set_page_config(page_title="పోలీస్ లీగల్ రీసెర్చ్ సపోర్ట్", page_icon="⚖️", layout="wide")
st.title("⚖️ పోలీస్ లీగల్ రీసెర్చ్ & సమగ్ర దర్యాప్తు మార్గదర్శక వేదిక")
st.caption("BNS / BNSS / BSA మరియు IPC / CrPC / IEA సమగ్ర చట్టాల విశ్లేషణ — అన్ని రకాల నేరాల దర్యాప్తు సహాయకారి.")

complaint = st.text_area("ఫిర్యాదు వివరాలు నమోదు చేయండి (Complaint / Case Details)", height=200, max_chars=MAX_CHARS)
uploaded = st.file_uploader("లేదా ఫిర్యాదు కాపీని అప్‌లోడ్ చేయండి (PDF, JPG, PNG, Screenshots, Text)", type=["jpg", "jpeg", "png", "webp", "pdf", "txt"])

extracted, extraction_error = extract_upload(uploaded)
if extraction_error:
    st.error(extraction_error)
elif uploaded:
    with st.expander("అప్‌లోడ్ చేసిన ఫైల్ నుండి సేకరించిన టెక్స్ట్ (Extracted / OCR Text)", expanded=False):
        st.text_area("File Text", extracted, height=150, disabled=True)

consent = st.checkbox("ఈ కేసుకు సంబంధించిన వివరాలను AI ద్వారా విశ్లేషించడానికి మరియు చట్టపరమైన పరిశోధన చేయడానికి అనుమతిస్తున్నాను.")

if st.button("⚖️ పూర్తి దర్యాప్తు నివేదిక మరియు లీగల్ సెక్షన్లను రూపొందించండి", type="primary", use_container_width=True):
    material = "COMPLAINT:\n" + text_limit(complaint) + "\n\nEXTRACTED FILE TEXT:\n" + extracted
    if not (complaint.strip() or extracted.strip()):
        st.error("దయచేసి ఫిర్యాదు టెక్స్ట్‌ను నమోదు చేయండి లేదా ఏదైనా ఫైల్‌ను అప్‌లోడ్ చేయండి.")
    elif not consent:
        st.error("దయచేసి పైన ఉన్న చెక్‌బాక్స్‌ను క్లిక్ చేసి అనుమతి ఇవ్వండి.")
    else:
        with st.spinner("సాక్ష్యాధారాలు, తేదీలు మరియు సంబంధిత చట్టాలు విశ్లేషించబడుతున్నాయి..."):
            extracted_facts, fact_error = extract_case_facts(material)

        if fact_error or extracted_facts is None:
            st.error(fact_error or "ఫ్యాక్ట్స్ సేకరించడం సాధ్యపడలేదు.")
        else:
            raw_date = extracted_facts.get("occurrence_date_iso")
            incident_date = None
            if raw_date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(raw_date)):
                try:
                    incident_date = date.fromisoformat(str(raw_date))
                except ValueError:
                    pass
            
            offence_nature = extracted_facts.get("offence_nature", "General Crime")
            framework_title, regime = framework_for(incident_date)
            
            st.subheader("📅 సంఘటన తేదీ & చట్టపరమైన పరిధి")
            date_info = f"గుర్తించిన సంఘటన తేదీ: **{incident_date.strftime('%d-%m-%Y')}**" if incident_date else "సంఘటన తేదీ నిర్ధారించబడలేదు"
            st.info(f"{date_info} | నేర స్వభావం: **{offence_nature}**\n\n📌 **{framework_title}**")

            results = assessment(extracted_facts)
            matched_rules = [r for r in results if r["status"] == "PRIMA_FACIE_GATE_PASSED"]
            
            if matched_rules:
                st.subheader("📊 రూల్ ఇంజిన్ ద్వారా నిర్ధారించబడిన ప్రాథమిక సెక్షన్లు")
                table = []
                for item in matched_rules:
                    rule = item["rule"]
                    table.append({
                        "BNS సెక్షన్": f"{rule.statute} Sec {rule.section}",
                        "సమాన IPC సెక్షన్": rule.old_law_equivalent,
                        "నేర వివరణ": rule.title,
                        "శిక్ష": rule.punishment,
                        "వర్గీకరణ": f"{rule.cognizable} / {rule.bailable}",
                        "విచారణ కోర్టు": rule.court
                    })
                st.dataframe(table, use_container_width=True, hide_index=True)

            with st.spinner("పోలీసు దర్యాప్తు మార్గదర్శకాలు (IO Guidelines) సిద్ధమవుతున్నాయి..."):
                prompt = build_investigation_prompt(material, incident_date, results, offence_nature)
                report = run_analysis(material, prompt)

            st.subheader("📋 సమగ్ర దర్యాప్తు నివేదిక & పోలీసు అధికారులకు మార్గదర్శకాలు")
            st.markdown(report)
            st.download_button(
                "రిపోర్ట్‌ను డౌన్‌లోడ్ చేసుకోండి (TXT)",
                data=report,
                file_name="police_investigation_report.txt",
                mime="text/plain",
                use_container_width=True
            )

st.caption("గమనిక: ఈ సాఫ్ట్‌వేర్ పోలీసు అధికారుల అంతర్గత పరిశోధన మరియు దర్యాప్తు సలహాల కొరకు మాత్రమే. తుది చార్జిషీట్ దాఖలులో సంబంధిత చట్ట నిబంధనలను స్వతంత్రంగా సరిచూసుకోవాలి.")
