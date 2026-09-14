Comprehensive Police Legal Research & Investigation Support Tool.
Supports all criminal offence categories under BNS, BNSS, BSA and IPC, CrPC, IEA.
Handles PDF, JPG, PNG, and plain-text complaint sources.
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
    cognizable: str
    bailable: str
    court: str
    old_law_equivalent: str
    notes: str = ""

# అన్ని ప్రధాన నేరాల సమగ్ర రూల్స్ డేటాబేస్
LEGAL_RULES = (
    # --- దొంగతనం & ఆస్తి నేరాలు ---
    LegalRule(
        "bns_303_2", "BNS 2023", "303(2)", "సాధారణ దొంగతనం (Theft)",
        ("dishonest_intention", "movable_property", "taken_without_consent"),
        {"dishonest_intention": "దురుద్దేశం ధృవీకరించబడింది", "movable_property": "చరాస్తి (బంగారం, నగదు, మొబైల్ మొదలైనవి)", "taken_without_consent": "సమ్మతి లేకుండా తీసుకున్నారు"},
        "3 సంవత్సరాల వరకు జైలు, లేదా జరిమానా, లేదా రెండూ.", "Cognizable", "Non-bailable", "Any Magistrate", "IPC 379"
    ),
    LegalRule(
        "bns_305", "BNS 2023", "305", "నివాస గృహంలో దొంగతనం (Theft in dwelling house)",
        ("dishonest_intention", "movable_property", "taken_without_consent", "dwelling_house"),
        {"dishonest_intention": "దురుద్దేశం ధృవీకరించబడింది", "movable_property": "చరాస్తి ఉంది", "taken_without_consent": "సమ్మతి లేకుండా తీసుకున్నారు", "dwelling_house": "నివాస గృహం/భవనంలో జరిగింది"},
        "7 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 380"
    ),
    LegalRule(
        "bns_331_4", "BNS 2023", "331(4)", "రాత్రివేళ తాళాలు తీసి/కన్నం వేసి దొంగతనానికి చొరబడటం (House-breaking by night)",
        ("house_trespass", "by_night", "intent_to_theft"),
        {"house_trespass": "తలుపు తీయడం లేదా గృహ ప్రవేశం", "by_night": "రాత్రివేళ జరిగింది (సూర్యాస్తమయం తర్వాత)", "intent_to_theft": "దొంగతనం చేయాలనే ఉద్దేశం"},
        "14 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 457"
    ),
    # --- మోసం మరియు ఆర్థిక నేరాలు ---
    LegalRule(
        "bns_318_4", "BNS 2023", "318(4)", "మోసగించి ఆస్తి డెలివరీ చేయించడం (Cheating)",
        ("deception", "fraudulent_inducement", "property_delivered"),
        {"deception": "వంచన/మోసం రుజువైంది", "fraudulent_inducement": "తప్పుడు వాగ్దానంతో ప్రేరేపించడం", "property_delivered": "డబ్బు/ఆస్తి ఇప్పించుకోవడం"},
        "7 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 420"
    ),
    # --- శరీరానికి వ్యతిరేక నేరాలు (శారీరక దాడులు & గాయాలు) ---
    LegalRule(
        "bns_115_2", "BNS 2023", "115(2)", "స్వచ్ఛందంగా గాయపరచడం (Voluntarily causing hurt)",
        ("causing_hurt", "intentional_act"),
        {"causing_hurt": "శారీరక నొప్పి లేదా గాయం జరిగింది", "intentional_act": "ఉద్దేశపూర్వకంగా గాయం చేయడం"},
        "1 సంవత్సరం వరకు జైలు, లేదా 10,000 వరకు జరిమానా, లేదా రెండూ.", "Non-cognizable", "Bailable", "Any Magistrate", "IPC 323"
    ),
    LegalRule(
        "bns_117_2", "BNS 2023", "117(2)", "తీవ్రమైన గాయం కలిగించడం (Grievous hurt)",
        ("grievous_hurt", "intentional_act"),
        {"grievous_hurt": "ఎముకల విరుపు, తీవ్ర గాయం, ప్రాణాపాయ స్థితి", "intentional_act": "ఉద్దేశపూర్వక చర్య"},
        "7 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Bailable", "Any Magistrate", "IPC 325"
    ),
    LegalRule(
        "bns_109", "BNS 2023", "109", "హత్యాయత్నం (Attempt to Murder)",
        ("act_done_with_intent", "capability_to_cause_death"),
        {"act_done_with_intent": "హత్య చేయాలనే ఉద్దేశంతో దాడి చేయడం", "capability_to_cause_death": "ప్రాణం పోయే అవకాశం ఉన్న చర్య"},
        "10 సంవత్సరాల వరకు జైలు మరియు జరిమానా (గాయమైతే జీవితఖైదు వరకు).", "Cognizable", "Non-bailable", "Court of Session", "IPC 307"
    ),
    # --- మహిళలపై నేరాలు ---
    LegalRule(
        "bns_85", "BNS 2023", "85", "భర్త లేదా బంధువులచే క్రూరత్వం (Cruelty by husband or relatives)",
        ("woman_subjected_to_cruelty", "harassment_for_dowry_or_coercion"),
        {"woman_subjected_to_cruelty": "వివాహిత స్త్రీని శారీరకంగా/మానసికంగా వేధించడం", "harassment_for_dowry_or_coercion": "వరకట్నం లేదా అక్రమ డిమాండ్ల కోసం వేధింపులు"},
        "3 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Magistrate First Class", "IPC 498A"
    ),
    LegalRule(
        "bns_74", "BNS 2023", "74", "స్త్రీ గౌరవానికి భంగం కలిగించేలా బలప్రయోగం (Outraging modesty of woman)",
        ("assault_or_force_on_woman", "intent_to_outrage_modesty"),
        {"assault_or_force_on_woman": "మహిళపై బలప్రయోగం లేదా దాడి", "intent_to_outrage_modesty": "ఆమె గౌరవానికి భంగం కలిగించే ఉద్దేశం"},
        "1 నుండి 5 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Non-bailable", "Any Magistrate", "IPC 354"
    ),
    # --- సైబర్ నేరాలు ---
    LegalRule(
        "it_66c", "IT Act 2000", "66C", "గుర్తింపు చోరీ / పాస్‌వర్డ్ దుర్వినియోగం (Identity Theft)",
        ("fraudulent_use", "electronic_identifier"),
        {"fraudulent_use": "దురుద్దేశపూర్వకంగా ఉపయోగించడం", "electronic_identifier": "మరొకరి పాస్‌వర్డ్, సిమ్, ఓటీపీ, లేదా డిజిటల్ సిగ్నేచర్"},
        "3 సంవత్సరాల వరకు జైలు మరియు 1 లక్ష వరకు జరిమానా.", "Cognizable", "Bailable", "Magistrate First Class", "IT Act 66C"
    ),
    LegalRule(
        "it_66d", "IT Act 2000", "66D", "కంప్యూటర్ వనరుల ద్వారా వ్యక్తిగత మారువేషంలో మోసం (Cheating by personation using computer)",
        ("cheating_by_personation", "computer_device_used"),
        {"cheating_by_personation": "మరొకరిగా నటించి మోసం చేయడం", "computer_device_used": "మొబైల్ ఫోన్, ఇంటర్నెట్ లేదా కంప్యూటర్ ద్వారా"},
        "3 సంవత్సరాల వరకు జైలు మరియు 1 లక్ష వరకు జరిమానా.", "Cognizable", "Bailable", "Magistrate First Class", "IT Act 66D"
    ),
    # --- రోడ్డు ప్రమాదాలు ---
    LegalRule(
        "bns_281", "BNS 2023", "281", "ప్రజా రహదారిపై నిర్లక్ష్యపు డ్రైవింగ్ (Rash driving on a public way)",
        ("driving_on_public_way", "rash_or_negligent_manner"),
        {"driving_on_public_way": "ప్రజా రహదారిపై వాహనం నడపడం", "rash_or_negligent_manner": "ప్రజల ప్రాణాలకు ముప్పు కలిగించే నిర్లక్ష్యం"},
        "6 నెలల వరకు జైలు, లేదా 1,000 జరిమానా, లేదా రెండూ.", "Cognizable", "Bailable", "Any Magistrate", "IPC 279"
    ),
    LegalRule(
        "bns_106_1", "BNS 2023", "106(1)", "నిర్లక్ష్యం వల్ల మరణం సంభవించడం (Causing death by negligence)",
        ("death_caused", "rash_or_negligent_act"),
        {"death_caused": "వ్యక్తి మరణం సంభవించడం", "rash_or_negligent_act": "నిర్లక్ష్యపు చర్య (రోడ్డు ప్రమాదం మొదలైనవి)"},
        "5 సంవత్సరాల వరకు జైలు మరియు జరిమానా.", "Cognizable", "Bailable", "Magistrate First Class", "IPC 304A"
    )
)

def framework_for(incident_date: Optional[date]) -> tuple[str, str]:
    if incident_date is None:
        return (
            "సంఘటన తేదీ నిర్ధారించబడలేదు. అందువల్ల BNS మరియు IPC రెండింటి సమగ్ర పరిశీలన అవసరం.",
            "BOTH"
        )
    if incident_date >= NEW_LAWS_START:
        return (
            f"01-07-2024 తర్వాత జరిగిన సంఘటన ({incident_date.strftime('%d-%m-%Y')}). వర్తించే చట్టాలు: BNS, 2023 + BNSS, 2023 + BSA, 2023.",
            "NEW"
        )
    return (
        f"01-07-2024 కు ముందు జరిగిన సంఘటన ({incident_date.strftime('%d-%m-%Y')}). వర్తించే చట్టాలు: IPC + CrPC + Indian Evidence Act (పరిశీలనార్థం BNS సమాన సెక్షన్లు కూడా ఇవ్వబడతాయి).",
        "OLD"
    )

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
            return (text_limit(result), "") if result.strip() else ("", "PDF లో టెక్స్ట్ లభించలేదు; OCR చిత్రం అప్‌లోడ్ చేయండి.")
        if name.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):
            if not OCR_AVAILABLE:
                return "", "OCR అందుబాటులో లేదు (pytesseract ఇన్‌స్టాల్ చేయండి)."
            image = Image.open(io.BytesIO(raw))
            for language in ("tel+eng", "eng"):
                try:
                    result = pytesseract.image_to_string(image, lang=language)
                    if result.strip():
                        return text_limit(result), ""
                except Exception:
                    continue
            return "", "చిత్రం నుండి టెక్స్ట్‌ను చదవలేకపోయాము."
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
    
    prompt = f"""You are an Indian police legal-research AI.
Extract facts from the following untrusted case complaint. Return JSON only, with no markdown fences.

Required JSON structure:
{{
  "occurrence_date_iso": "YYYY-MM-DD or null",
  "occurrence_date_basis": "string explaining how occurrence date was found",
  "offence_nature": "e.g. Theft, House Breaking, Cheating, Hurt, Murder Attempt, Cyber Crime, Accident",
  "facts": {json.dumps(schema, ensure_ascii=False)}
}}

Guidelines:
- If incident date is stated (e.g. 28-05-2017), convert to YYYY-MM-DD. Distinguish occurrence date from complaint filing date.
- Set fact `supported: true` if directly stated or prima-facie inferred from the text, and provide verbatim quote in `quotes`.
- If gold, mobile, money, or goods are stolen: mark movable_property, dishonest_intention, taken_without_consent as true.
- If door broken or back bolt opened at night: dwelling_house, house_trespass, by_night as true.

Fact keys to check: {json.dumps(fact_keys, ensure_ascii=False)}

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
    passed_str = ", ".join(passed_rules) if passed_rules else "ప్రత్యేక రూల్ ఇంజిన్ సెక్షన్లు సరిపోలలేదు, కింద AI విశ్లేషణను అనుసరించండి."

    return f"""
మీరు భారతదేశంలో పనిచేస్తున్న సీనియర్ పోలీస్ ఇన్వెస్టిగేషన్ ఆఫీసర్ (IO) మరియు క్రిమినల్ లీగల్ ఎక్స్‌పర్ట్.
క్రింద ఇవ్వబడిన ఫిర్యాదు వివరాలను క్షుణ్ణంగా పరిశీలించి స్పష్టమైన, సాధికారిక తెలుగులో పూర్తి పోలీస్ దర్యాప్తు మార్గదర్శక నివేదికను రూపొందించండి.

సంఘటన వివరాలు:
- సంఘటన స్వభావం: {offence_nature}
- సంఘటన జరిగిన తేదీ: {date_str}
- చట్టపరమైన ఫ్రేమ్‌వర్క్: {framework_text}
- పద్ధతి (Regime): {regime} (గమనిక: సంఘటన 01-07-2024 ముందైతే ఎఫ్ఐఆర్ IPC కింద నమోదు చేయాలి. అయితే ప్రస్తుతం న్యాయస్థానాలు మరియు అధికారుల అవగాహన కోసం BNS సమాన సెక్షన్లను కూడా పక్కన సూచించండి).
- ప్రాథమికంగా సరిపోలిన సెక్షన్లు: {passed_str}

ముఖ్యమైన నిబంధన:
- BSA అంటే "భారతీయ సాక్ష్య అధినియం, 2023" (Bharatiya Sakshya Adhiniyam, 2023). బ్యాంకింగ్ చట్టాలతో గందరగోళం చెందవద్దు. ఎలక్ట్రానిక్ సాక్ష్యాలకు BSA Section 63 (పాత IEA 65B సమానం) సర్టిఫికేషన్ అవసరం.

క్రింది క్రమంలో పూర్తి స్థాయి పోలీస్ దర్యాప్తు నివేదిక ఇవ్వండి:
1. **ఫిర్యాదు సారాంశం**: ఫిర్యాది, నిందితులు (తెలిసినవారా/అపరిచితులా), పోయిన వస్తువులు లేదా జరిగిన నష్టం/దాడి వివరాలు.
2. **తేదీలు మరియు కాలవ్యవధి విశ్లేషణ**: సంఘటన జరిగిన సమయం, ఫిర్యాదు చేసిన సమయం, ఎఫ్ఐఆర్ నమోదులో జాప్యం ఉంటే దర్యాప్తు అధికారి సమర్థించాల్సిన అంశాలు.
3. **వర్తించే చట్టపరమైన సెక్షన్ల పూర్తి విశ్లేషణ**:
   - వర్తించే BNS సెక్షన్లు మరియు సమాన IPC సెక్షన్లు.
   - నేరం Cognizable ఆ కాదా? Bailable ఆ లేక Non-bailable ఆ? ఏ మేజిస్ట్రేట్ కోర్టు విచారిస్తుంది?
4. **పోలీసు దర్యాప్తు మార్గదర్శకాలు (Actionable Guidelines for IO)**:
   - ఘటనా స్థల పరిశీలన (Scene of Crime), క్రైమ్ డీటెయిల్స్ ఫారమ్ (CDF), నక్షా తయారీ.
   - క్లూస్ టీమ్ (Clues Team), వేలిముద్రలు (Fingerprints), డాగ్ స్క్వాడ్ పరిశీలన.
   - నిందితుల గుర్తింపు మరియు అరెస్ట్ నియమాలు (BNSS Sec 35 / CrPC Sec 41 మార్గదర్శకాలు).
5. **సాక్ష్యాధారాల సేకరణ & రికవరీ ప్రొసీజర్**:
   - దొంగిలించబడిన సొత్తు లేదా నేరానికి వాడిన ఆయుధాల రికవరీ పంచనామా (Seizure Panchanama).
   - రికవరీ సాక్షులు (Panchas) మరియు మెమోరండం ఆఫ్ కన్ఫెషన్.
6. **డిజిటల్ & సైబర్ సాక్ష్యాలు (BSA Section 63 మార్గదర్శకాలు)**:
   - పోయిన మొబైల్ ఫోన్ (IMEI నంబర్ ట్రాకింగ్, CEIR పోర్టల్ ఎంట్రీ).
   - సీసీటీవీ ఫుటేజ్ (CCTV), కాల్ డాటా రికార్డులు (CDR), టవర్ డంప్ (Tower Dump) సేకరణ.
   - BNSS Sec 94 / CrPC Sec 91 క్రింద సర్వీస్ ప్రొవైడర్లకు నోటీసులు మరియు BSA Sec 63 సర్టిఫికేట్ తప్పనిసరి ప్రక్రియ.
7. **సాక్షుల విచారణ ప్రణాళిక**: ఎవరెవరి వాంగ్మూలాలు (180 BNSS / 161 CrPC) నమోదు చేయాలి?
8. **ముగింపు & తక్షణ కార్యాచరణ**: దర్యాప్తు అధికారి తక్షణమే చేపట్టవలసిన మొదటి 3 చర్యలు.

<CASE_MATERIAL>
{material}
</CASE_MATERIAL>
"""

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
            # 1. తేదీ నిర్ధారణ
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

            # 2. రూల్ ఇంజిన్ ఫలితాలు
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

            # 3. AI ద్వారా పూర్తి సమగ్ర నివేదిక తయారీ
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
