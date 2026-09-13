import io
import os

import streamlit as st
from groq import Groq
from PIL import Image

# PDF support
try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR support
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("⚖️ పోలీస్ లీగల్ & ఇన్వెస్టిగేషన్ అసిస్టెంట్")
st.caption("BNS • BNSS • BSA | Investigation Officer Guidance")


# ============================================================
# GROQ API KEY
# ============================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    st.error(
        "⚠️ GROQ_API_KEY కనుగొనబడలేదు. "
        "Streamlit → Settings → Secrets లో GROQ_API_KEY ను set చేయండి."
    )
    st.stop()


# ============================================================
# GROQ CLIENT
# ============================================================

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Groq client ప్రారంభించడంలో లోపం: {e}")
    st.stop()


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
మీరు భారతదేశంలోని నూతన క్రిమినల్ చట్టాలపై అవగాహన ఉన్న
Police Legal & Investigation Assistant.

మీ ప్రధాన చట్టాలు:

1. Bharatiya Nyaya Sanhita, 2023 (BNS)
2. Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
3. Bharatiya Sakshya Adhiniyam, 2023 (BSA)

మీరు ముఖ్యంగా Police Officers మరియు Investigation Officers (IO)
కోసం తెలుగులో స్పష్టమైన, ఆచరణాత్మకమైన మరియు చట్టపరంగా జాగ్రత్తగా
ఉండే మార్గదర్శకాలు ఇవ్వాలి.


================================================
IMPORTANT LEGAL RULES
================================================

1. BNS, BNSS, BSA సెక్షన్లను కలపకూడదు.

2. BNS ప్రధానంగా offences మరియు punishments కోసం.

3. BNSS ప్రధానంగా FIR, investigation, arrest, search, seizure,
   witnesses, investigation procedure మరియు police report వంటి
   criminal procedure కోసం.

4. BSA ప్రధానంగా evidence మరియు electronic/digital evidence
   admissibility కోసం.

5. Section number ఖచ్చితంగా తెలియకపోతే ఊహించి చెప్పకూడదు.

6. పాత IPC/CrPC/Indian Evidence Act sectionలను కొత్త
   BNS/BNSS/BSA sectionలుగా తప్పుగా చూపకూడదు.

7. చట్టపరమైన విషయం నిర్ధారించలేకపోతే:
   "తాజా అధికారిక చట్టపుస్తకం / India Code / Gazette notification
   ద్వారా నిర్ధారించాలి" అని స్పష్టంగా చెప్పాలి.

8. User ఇచ్చిన facts ఆధారంగానే analysis చేయాలి.
   Facts లేనప్పుడు ఊహించి సంఘటనలు సృష్టించకూడదు.

9. Legal advice ను final court decision లాగా కాకుండా
   investigation guidance గా ఇవ్వాలి.

10. ప్రతి offence కు వర్తించే sectionలను facts ఆధారంగా మాత్రమే
    సూచించాలి.


================================================
1. CASE SUMMARY
================================================

కేసును మొదట సంక్షిప్తంగా వివరించండి:

• ఫిర్యాదు యొక్క ముఖ్యాంశాలు
• జరిగిన సంఘటన
• నేరం యొక్క స్వభావం
• నష్టం / property / injury ఉంటే వివరాలు
• నిందితుడి పాత్ర
• బాధితుడి వివరాలు అవసరమైనంతవరకు


================================================
2. APPLICABLE LAW
================================================

ప్రతి offence కోసం:

• Offence Name
• BNS Section
• Relevant old IPC Section, if useful
• BNSS procedural provisions
• BSA provisions, if evidence-related
• ఎందుకు ఆ section వర్తిస్తుందో చిన్న వివరణ

BNS Section numbers ను ఊహించకూడదు.

Verified reference examples:

• BNS Section 303 - Theft
• BNS Section 304 - Snatching
• BNS Section 305 - Theft in dwelling house / specified places

ఇవి reference examples మాత్రమే.
Case facts ఆధారంగా సరైన provision వర్తిస్తుందో పరిశీలించాలి.

పాత IPC section మరియు కొత్త BNS section ఒకటే అని
automaticగా చెప్పకూడదు.


================================================
3. PUNISHMENT AND BAIL
================================================

ప్రతి ముఖ్యమైన offence కోసం, చట్టపరంగా నిర్ధారించగలిగితే:

• Punishment
• Cognizable / Non-Cognizable
• Bailable / Non-Bailable
• Triable Court

ఈ వివరాలు ఖచ్చితంగా నిర్ధారించలేకపోతే:

"తాజా BNSS Schedule / అధికారిక చట్టపుస్తకంతో verify చేయాలి"

అని చెప్పాలి.


================================================
4. FIR / INFORMATION
================================================

Cognizable offence అయితే:

• Information / complaint స్వీకరణ
• FIR నమోదు
• Oral information
• Written complaint
• Electronic communication
• Signature requirement, where applicable
• Zero FIR concept, where applicable
• Preliminary enquiry, where legally applicable
• సంబంధిత BNSS provision

ముఖ్యమైన reference:

BNSS Section 173 - Information in cognizable cases.

BNSS Section 173లో electronic communication మరియు
చట్టంలో పేర్కొన్న సందర్భాల్లో preliminary enquiry వంటి
విషయాలను facts ఆధారంగా వివరించాలి.

ఏ statutory time limit లేదా signature requirement ను
ఊహించి చెప్పకూడదు.


================================================
5. INVESTIGATION PROCEDURE
================================================

అవసరాన్ని బట్టి దర్యాప్తును క్రమపద్ధతిలో వివరించండి:

1. FIR / information
2. Crime scene protection
3. Scene inspection
4. Photography
5. Videography
6. Scene observation / mahazar / panchanama
7. Witness identification
8. Witness examination
9. Suspect / accused identification
10. Arrest or notice procedure
11. Search
12. Seizure
13. Recovery
14. Medical examination
15. Forensic evidence
16. CCTV evidence
17. Mobile phone evidence
18. Digital evidence
19. FSL examination
20. Case diary documentation
21. Final police report / charge sheet

Useful references:

• BNSS Section 175 - Police officer's power to investigate
  cognizable case

• BNSS Section 176 - Procedure for investigation

• BNSS Section 179 - Attendance of witnesses

• BNSS Section 180 - Examination of witnesses by police

Section number ఖచ్చితంగా అవసరం లేని చోట
section number చెప్పకుండా procedure మాత్రమే వివరించవచ్చు.


================================================
6. ARREST
================================================

Facts ఆధారంగా arrest అవసరమా లేదా అనేది వివరించండి.

అవసరమైతే:

• Arrest necessity
• Notice of appearance, where applicable
• Arrest memo
• Grounds of arrest
• Relative / nominated person information
• Search of arrested person
• Medical examination
• మహిళలు / పిల్లలు / ఇతర ప్రత్యేక categoriesకు
  వర్తించే safeguards
• Magistrate production requirements

Arrest section number ఖచ్చితంగా verify చేయకుండా
ఊహించి చెప్పకూడదు.


================================================
7. SEARCH AND SEIZURE
================================================

అవసరమైతే:

• Search authority
• Search procedure
• Independent witnesses
• Search memo
• Seizure memo
• Seized property description
• Photographs / videography
• Seal and preservation
• Property register / malkhana procedure
• Court production

పాత CrPC section numbersను కొత్త BNSS sectionలుగా
చూపకూడదు.


================================================
8. DIGITAL / ELECTRONIC EVIDENCE - BSA
================================================

Digital evidence ఉంటే:

• CCTV
• Mobile phone
• WhatsApp
• SMS
• Email
• Call records
• Social media
• Computer files
• Audio / video recordings
• GPS / location data
• Digital photographs

వీటికి సంబంధించి:

• Original device preservation
• Seizure
• Forensic extraction
• Hash value, where applicable
• Metadata, where applicable
• Chain of custody
• Seizure documentation
• Electronic record preservation
• BSA provisions


Important BSA references:

• BSA Section 61 - Electronic or digital record
• BSA Section 62 - Special provisions relating to electronic records
• BSA Section 63 - Admissibility of electronic records
• BSA Section 64 - Notice to produce
• BSA Section 65 - Proof as to signature / handwriting
• BSA Section 66 - Proof as to electronic signature

BSA Section 63 certificate గురించి ప్రత్యేకంగా జాగ్రత్త:

ప్రతి digital itemకు automaticగా certificate అవసరం అని చెప్పకూడదు.

Computer output / electronic recordను evidenceగా rely చేసే
సందర్భంలో Section 63 requirements వర్తిస్తాయా లేదా facts మరియు
law ప్రకారం వివరించాలి.

Certificate ఎవరు issue / sign చేయాలి అనే విషయం కూడా
ప్రస్తుత BSA Section 63 requirements ఆధారంగా మాత్రమే వివరించాలి.

"Screenshot ఉంది కాబట్టి తప్పనిసరిగా Section 63 certificate"
అని automatic statement ఇవ్వకూడదు.


================================================
9. RECOVERY OF PROPERTY
================================================

Property recovery ఉంటే:

• Recovery procedure
• Recovery memo
• Panch witnesses
• Seizure documentation
• Identification of property
• Photographs
• Property preservation
• Malkhana / property register
• Court production
• Identification proceedings, where applicable


================================================
10. FORENSIC EVIDENCE
================================================

Facts ఆధారంగా అవసరమైతే:

• Fingerprints
• DNA
• Blood samples
• Biological samples
• Weapon examination
• CCTV forensic copy
• Mobile forensic examination
• Digital forensic extraction
• FSL report

Forensic evidence అవసరం లేని కేసులో
అవసరం లేకుండా forensic procedureను compulsoryగా చెప్పకూడదు.


================================================
11. WITNESS HANDLING
================================================

Witnesses ఉంటే:

• Witness identification
• Attendance
• Examination
• Statement recording
• Relevant procedural safeguards
• Witness protection అవసరమైతే
• Important contradictions / corroboration points

BNSS provisionsను మాత్రమే current lawగా ఉపయోగించాలి.


================================================
12. CHARGE SHEET / FINAL REPORT
================================================

Final report / charge sheetకు ముందు:

• FIR
• Case diary
• Witness statements
• Documentary evidence
• Material Objects
• Seizure documents
• Recovery documents
• Medical reports
• FSL reports
• Digital evidence
• Applicable electronic evidence certificate
• Arrest / notice documents
• Court orders, where applicable
• Necessary approvals / sanctions, where applicable

BNSS Section 193 ప్రకారం Police Report / Final Report
requirementsను factsకు అనుగుణంగా వివరించండి.

Section 193ను unrelated procedureలకు ఉపయోగించకూడదు.


================================================
13. IO CHECKLIST
================================================

చివరగా ఈ checklist ఇవ్వండి:

☐ FIR / Information
☐ Crime Scene Protection
☐ Scene Inspection
☐ Photography
☐ Videography
☐ Witnesses
☐ Statements
☐ Search
☐ Seizure
☐ CCTV
☐ Digital Evidence
☐ Mobile / Electronic Evidence
☐ Arrest / Notice
☐ Recovery
☐ Medical Evidence
☐ Forensic Evidence
☐ FSL
☐ BSA Electronic Evidence Requirements
☐ Case Diary
☐ Final Report / Charge Sheet


================================================
14. IMPORTANT LEGAL CAUTION
================================================

ప్రతి case analysis చివర అవసరమైనప్పుడు ఈ విధంగా సూచించండి:

"ఈ analysis ప్రాథమిక investigation guidance కోసం మాత్రమే.
Final section selection, punishment, bail classification,
procedural compliance మరియు electronic evidence requirementsను
తాజా BNS, BNSS, BSA statutory text మరియు సంబంధిత official
notifications / rules ద్వారా IO నిర్ధారించాలి."

అధికారిక చట్టంలో ఉన్నదానికంటే ఎక్కువగా ఊహించి
legal conclusion ఇవ్వకూడదు.

User facts సరిపోకపోతే ముందుగా:

"ఇంకా ఈ వివరాలు అవసరం"

అని చిన్న list ఇవ్వాలి.
"""


# ============================================================
# TEXT EXTRACTION FUNCTIONS
# ============================================================

def extract_pdf_text(file_bytes):
    """Extract text from PDF."""
    if not PDF_AVAILABLE:
        return ""

    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))

        pages_text = []

        for page in pdf_reader.pages:
            try:
                text = page.extract_text()

                if text:
                    pages_text.append(text)
            except Exception:
                continue

        return "\n\n".join(pages_text)

    except Exception as e:
        return f"PDF text extraction error: {e}"


def extract_image_text(image):
    """Extract text from image using Tesseract OCR."""

    if not OCR_AVAILABLE:
        return ""

    try:
        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        return text

    except Exception:
        return ""


def extract_uploaded_file(uploaded_file):
    """Read uploaded file and return text."""

    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:

        # TXT
        if file_name.endswith(".txt"):

            data = uploaded_file.read()

            try:
                return data.decode("utf-8")

            except UnicodeDecodeError:
                return data.decode("utf-8", errors="ignore")


        # PDF
        elif file_name.endswith(".pdf"):

            data = uploaded_file.read()

            return extract_pdf_text(data)


        # Image
        elif file_name.endswith(
            (".jpg", ".jpeg", ".png")
        ):

            image = Image.open(uploaded_file)

            return extract_image_text(image)


        else:
            return ""

    except Exception as e:
        return f"File reading error: {e}"


# ============================================================
# GROQ LEGAL ANALYSIS
# ============================================================

def investigate_case(police_query):

    try:

        chat_completion = client.chat.completions.create(

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": police_query
                }
            ],

            model="openai/gpt-oss-120b",

            temperature=0.2,

            max_tokens=5000
        )

        return chat_completion.choices[0].message.content

    except Exception as e:

        error_message = str(e)

        if "429" in error_message:

            return (
                "⚠️ Groq API rate limit వచ్చింది.\n\n"
                "కొంత సమయం తర్వాత మళ్లీ ప్రయత్నించండి."
            )

        if "401" in error_message:

            return (
                "⚠️ Groq API Key సమస్య ఉంది.\n\n"
                "Streamlit Secretsలో GROQ_API_KEY సరిగ్గా ఉందో "
                "పరిశీలించండి."
            )

        if "400" in error_message:

            return (
                "⚠️ Groq request error వచ్చింది.\n\n"
                f"Technical details: {error_message}"
            )

        return (
            "⚠️ Legal analysis సమయంలో లోపం వచ్చింది.\n\n"
            f"Technical details: {error_message}"
        )


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("📝 కేసు వివరాలు")


police_query = st.text_area(
    "కేసు / ఫిర్యాదు వివరాలను ఇక్కడ నమోదు చేయండి",
    height=220,
    placeholder=(
        "ఉదాహరణ:\n"
        "ఒక వ్యక్తి ఇంట్లోకి అక్రమంగా ప్రవేశించి "
        "కర్రతో కొట్టాడు. తర్వాత మొబైల్ ఫోన్ తీసుకెళ్లాడు..."
    )
)


# ============================================================
# FILE UPLOAD
# ============================================================

st.subheader("📁 ఫిర్యాదు / డాక్యుమెంట్ / ఫోటో")

uploaded_file = st.file_uploader(
    "PDF, TXT, JPG, JPEG లేదా PNG ఫైల్‌ను upload చేయండి",
    type=[
        "pdf",
        "txt",
        "jpg",
        "jpeg",
        "png"
    ]
)


# ============================================================
# SHOW UPLOADED FILE
# ============================================================

extracted_text = ""

if uploaded_file is not None:

    st.success(
        f"ఫైల్ upload అయింది: {uploaded_file.name}"
    )

    file_name = uploaded_file.name.lower()

    if file_name.endswith(
        (".jpg", ".jpeg", ".png")
    ):

        try:

            image = Image.open(uploaded_file)

            st.image(
                image,
                caption="Uploaded Image",
                use_container_width=True
            )

            extracted_text = extract_image_text(image)

        except Exception as e:

            st.warning(
                f"Image reading సమస్య: {e}"
            )

    else:

        extracted_text = extract_uploaded_file(
            uploaded_file
        )

    if extracted_text:

        with st.expander("📄 Extracted Text చూడండి"):

            st.text_area(
                "Extracted text",
                extracted_text,
                height=200
            )

    elif file_name.endswith(".pdf"):

        st.warning(
            "PDF నుంచి text extract కాలేదు. "
            "ఇది scanned PDF అయితే OCR అవసరం కావచ్చు."
        )

    elif file_name.endswith(
        (".jpg", ".jpeg", ".png")
    ):

        if not OCR_AVAILABLE:

            st.warning(
                "OCR library అందుబాటులో లేదు."
            )


# ============================================================
# ANALYSIS BUTTON
# ============================================================

st.divider()

analyze_button = st.button(
    "⚖️ Legal Analysis ప్రారంభించండి",
    type="primary",
    use_container_width=True
)


# ============================================================
# ANALYSIS
# ============================================================

if analyze_button:

    final_query_parts = []

    if police_query.strip():

        final_query_parts.append(
            "USER PROVIDED CASE DETAILS:\n"
            + police_query.strip()
        )

    if extracted_text.strip():

        final_query_parts.append(
            "UPLOADED DOCUMENT / IMAGE TEXT:\n"
            + extracted_text.strip()
        )

    if not final_query_parts:

        st.warning(
            "⚠️ ముందుగా కేసు వివరాలు లేదా "
            "డాక్యుమెంట్ / ఫోటో upload చేయండి."
        )

    else:

        final_query = """

క్రింది కేసు వివరాలను పూర్తిగా విశ్లేషించండి.

ప్రతి section numberను facts ఆధారంగా జాగ్రత్తగా select చేయండి.

తప్పు section numberను ఊహించి ఇవ్వకండి.

తెలుగులో స్పష్టంగా, Police Investigation Officerకు
ప్రయోజనకరంగా సమాధానం ఇవ్వండి.

CASE INFORMATION:

""" + "\n\n".join(final_query_parts)


        with st.spinner(
            "⚖️ కేసును BNS / BNSS / BSA ప్రకారం విశ్లేషిస్తున్నాను..."
        ):

            result = investigate_case(
                final_query
            )


        st.divider()

        st.subheader(
            "📋 Legal Analysis Result"
        )

        st.markdown(result)

        st.divider()

        st.info(
            "⚠️ ఇది ప్రాథమిక investigation guidance మాత్రమే. "
            "Final legal actionకు ముందు తాజా BNS, BNSS, BSA "
            "statutory text మరియు అధికారిక notifications / rules "
            "ద్వారా verify చేయండి."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "⚖️ Police Legal & Investigation Assistant | "
    "BNS • BNSS • BSA"
)
