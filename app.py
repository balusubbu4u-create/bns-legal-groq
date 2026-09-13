import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from PIL import Image
import base64
import fitz  # PyMuPDF
from io import BytesIO

# =========================================================
# 1. PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="BNS / BNSS / BSA Legal & Investigation Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA & IPC / CrPC / IEA స్మార్ట్ లీగల్ అసిస్టెంట్")
st.caption(
    "ఫిర్యాదు పత్రాలు, స్క్రీన్‌షాట్లు, వాయిస్, ఆడియో/వీడియో మరియు టెక్స్ట్ ఆధారంగా సమగ్ర చట్టపరమైన విశ్లేషణ."
)

st.warning(
    "⚠️ ఇది AI-assisted preliminary legal analysis మాత్రమే. "
    "FIR మరియు చార్జిషీట్ నమోదు చేసే ముందు అధికారిక చట్టాలు మరియు సాక్ష్యాధారాల ఆధారంగా ధృవీకరించుకోవాలి."
)

# =========================================================
# 2. GROQ CLIENT CONFIGURATION & SAFE FALLBACKS
# =========================================================
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY కనిపించలేదు. Streamlit Cloud -> Settings -> Secrets లో GROQ_API_KEY నమోదు చేయండి.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

TEXT_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
VISION_MODELS = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"]
AUDIO_MODEL = "whisper-large-v3"

# =========================================================
# 3. DETAILED LEGAL SYSTEM PROMPT (INCLUDING BSA & IEA)
# =========================================================
LEGAL_SYSTEM_PROMPT = """You are an expert Indian Criminal Law and Police Investigation Assistant specialized in:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)
- Comprehensive comparative analysis with:
  * Indian Penal Code, 1860 (IPC)
  * Code of Criminal Procedure, 1973 (CrPC)
  * Indian Evidence Act, 1872 (IEA)

Analyze the given complaint thoroughly and provide a structured, professional report in clear Telugu and English legal terminology under the following EXACT headers:

### 1. ఫిర్యాదు సారాంశం (Brief Facts of the Complaint)
- ప్రధాన ఆరోపణలు మరియు వాస్తవాలు (Alleged facts).

### 2. చట్టపరమైన విభాగాలు: BNS vs IPC మరియు BSA vs IEA పోలిక (Comprehensive Comparative Analysis)
కింది వివరాలతో ఒక Markdown Table ఇవ్వండి:
| ఆరోపణ / నేరం (Offence) | వర్తించే BNS సెక్షన్ | సమానమైన పాత IPC సెక్షన్ | వర్తించే BSA సెక్షన్ (సాక్ష్యం) | సమానమైన పాత IEA సెక్షన్ | శిక్ష కాలపరిమితి (Punishment) | బెయిలబుల్ / నాన్-బెయిలబుల్ | కాగ్నిజబుల్ / నాన్-కాగ్నిజబుల్ |
(Note: Never invent fake sections. Only apply sections supported strictly by stated facts.)

### 3. లీగల్ ఇంగ్రీడియంట్స్ & BSA సాక్ష్యాధారాల నిబంధనలు (Legal Ingredients & BSA/IEA Evidence Requirements)
- సెక్షన్ వర్తించడానికి కావాల్సిన ప్రధాన చట్టపరమైన అంశాలు.
- Bharatiya Sakshya Adhiniyam, 2023 (BSA) కింద ఎలక్ట్రానిక్ రికార్డ్స్, సర్టిఫికెట్లు (ఉదాహరణకు BSA Section 61, 63 / పాత IEA Section 65B) మరియు డిజిటల్ సాక్ష్యాల ప్రాముఖ్యత.

### 4. దర్యాప్తు అధికారి (IO) వెంటనే చేయవలసిన తక్షణ చర్యలు (Immediate Action Plan under BNSS & BSA)
- Section 173 BNSS కింద FIR నమోదు లేదా ప్రాథమిక విచారణ.
- Section 35 BNSS (పాత CrPC 41A) ప్రకారం నోటీసు లేదా అరెస్ట్ నిబంధనలు.
- డిజిటల్ సాక్ష్యాలు (కాల్ రికార్డింగ్‌లు, చాట్లు, సీసీటీవీ) భద్రపరచడానికి BSA ప్రకారం తీసుకోవాల్సిన జాగ్రత్తలు.

### 5. సీన్ ఆఫ్ అఫెన్స్ నుండి ఫైనల్ చార్జిషీట్ వరకు పూర్తి ఇన్వెస్టిగేషన్ రోడ్‌మ్యాప్ (Full Investigation Workflow to Charge Sheet)
1. **ఘటనా స్థల పరిశీలన:** Section 176 BNSS ప్రకారం క్రైమ్ సీన్ ఫోటోగ్రఫీ / వీడియోగ్రఫీ మరియు పంచనామా.
2. **సాక్షుల వాంగ్మూలాలు:** Section 180 BNSS (పాత 161 CrPC) ప్రకారం సాక్షుల వాంగ్మూలాల నమోదు.
3. **సాక్ష్యాధారాల స్వాధీనం & BSA నిబంధనలు:** మెటీరియల్ ఆబ్జెక్ట్స్ మరియు ఎలక్ట్రానిక్ ఎవిడెన్స్ సీజ్ పంచనామా, ఎఫ్‌ఎస్‌ఎల్ (FSL) నివేదిక మరియు BSA సర్టిఫికేషన్.
4. **నిందితుల రిమాండ్ / బెయిల్ పరిశీలన:** Section 187 BNSS కింద కస్టడీ మరియు రిమాండ్ నియమాలు.
5. **ఫైనల్ చార్జిషీట్ దాఖలు:** Section 193 BNSS (పాత 173 CrPC) కింద కోర్టులో చార్జిషీట్ దాఖలు చేసే పూర్తి ప్రక్రియ."""

# =========================================================
# 4. HELPER FUNCTIONS FOR FILE & MEDIA PROCESSING
# =========================================================

def transcribe_audio_file(file_bytes, filename):
    try:
        transcription = client.audio.transcriptions.create(
            file=(filename, file_bytes),
            model=AUDIO_MODEL,
            response_format="text"
        )
        return transcription
    except Exception as e:
        return f"ఆడియో ట్రాన్స్‌క్రిప్షన్‌లో లోపం: {str(e)}"

def extract_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def process_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"

    if len(text.strip()) < 60:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        images = []
        max_pages = min(len(doc), 4)
        for i in range(max_pages):
            page = doc[i]
            pix = page.get_pixmap(dpi=120)
            img = Image.open(BytesIO(pix.tobytes("png")))
            img.thumbnail((1100, 1100))
            images.append(img)
        return False, images
    return True, text

def image_to_base64(pil_img):
    buffered = BytesIO()
    pil_img.convert("RGB").save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def call_groq_text_completion(prompt_text):
    last_error = None
    for model_name in TEXT_MODELS:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.1
            )
            return res.choices[0].message.content, model_name
        except Exception as e:
            last_error = e
            continue
    raise last_error

def call_groq_vision_completion(images, extra_text=""):
    user_content = [{"type": "text", "text": f"Analyze this scanned complaint document thoroughly.\n{extra_text}"}]
    for img in images:
        b64 = image_to_base64(img)
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    last_error = None
    for model_name in VISION_MODELS:
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": LEGAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1
            )
            return res.choices[0].message.content, model_name
        except Exception as e:
            last_error = e
            continue
    raise last_error

# =========================================================
# 5. USER INTERFACE (TABS FOR DIFFERENT INPUTS)
# =========================================================

tab1, tab2, tab3 = st.tabs([
    "📁 డాక్యుమెంట్ లేదా స్క్రీన్ షాట్ అప్‌లోడ్",
    "🎙️ లైవ్ వాయిస్ / ఆడియో & వీడియో ఫైల్",
    "✍️ డైరెక్ట్ టెక్స్ట్ ఎంట్రీ"
])

complaint_text_payload = ""
images_payload = []

# --- TAB 1: DOCUMENTS & SCREENSHOTS ---
with tab1:
    uploaded_doc = st.file_uploader(
        "ఫిర్యాదు ఫైల్‌ను అప్‌లోడ్ చేయండి (PDF, DOCX, TXT, లేదా JPG/PNG ఫోటో/స్క్రీన్‌షాట్):",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp"],
        key="doc_uploader"
    )
    if uploaded_doc:
        ext = uploaded_doc.name.split(".")[-1].lower()
        if ext in ["png", "jpg", "jpeg", "webp"]:
            img = Image.open(uploaded_doc)
            img.thumbnail((1100, 1100))
            images_payload.append(img)
            st.image(img, caption="అప్‌లోడ్ చేసిన ఇమేజ్", use_container_width=True)
        elif ext == "docx":
            complaint_text_payload += extract_from_docx(uploaded_doc)
            st.success("Word డాక్యుమెంట్ నుండి వివరాలు లోడ్ అయ్యాయి.")
        elif ext == "txt":
            complaint_text_payload += str(uploaded_doc.read(), "utf-8", errors="ignore")
            st.success("Text డాక్యుమెంట్ నుండి వివరాలు లోడ్ అయ్యాయి.")
        elif ext == "pdf":
            is_text, result = process_pdf(uploaded_doc)
            if is_text:
                complaint_text_payload += result
                st.success("PDF నుండి టెక్స్ట్ విజయవంతంగా లోడ్ అయింది.")
            else:
                images_payload = result
                st.info(f"📷 స్కాన్ చేసిన PDF గుర్తించబడింది ({len(result)} పేజీలు ఇమేజ్ మోడ్‌లోకి మార్చబడ్డాయి).")

# --- TAB 2: VOICE RECORDING & AUDIO/VIDEO ---
with tab2:
    st.subheader("మైక్రోఫోన్ ద్వారా మాట్లాడండి లేదా ఆడియో/వీడియో ఫైల్ అప్‌లోడ్ చేయండి")
    
    live_audio = st.audio_input("మైక్రోఫోన్ ఆన్ చేసి ఫిర్యాదు వివరాలు మాట్లాడండి:")
    if live_audio:
        with st.spinner("వాయిస్ రికార్డింగ్ ప్రాసెస్ అవుతోంది (Groq Whisper)..."):
            transcription = transcribe_audio_file(live_audio.read(), "voice_record.wav")
            complaint_text_payload += "\n" + transcription
            st.success("వాయిస్ రికార్డింగ్ టెక్స్ట్‌గా మార్చబడింది:")
            st.write(transcription)

    st.divider()

    uploaded_media = st.file_uploader(
        "లేదా ఆడియో/వీడియో ఫైల్ అప్‌లోడ్ చేయండి (MP3, WAV, M4A, OGG, MP4, WebM):",
        type=["mp3", "wav", "m4a", "ogg", "mp4", "webm", "mpeg"],
        key="media_uploader"
    )
    if uploaded_media:
        with st.spinner("మీడియా ఫైల్ నుండి ఆడియో సంగ్రహించి టెక్స్ట్‌గా మారుస్తోంది..."):
            media_transcription = transcribe_audio_file(uploaded_media.read(), uploaded_media.name)
            complaint_text_payload += "\n" + media_transcription
            st.success("ఆడియో/వీడియో ఫైల్ నుండి తీసిన వివరాలు:")
            st.write(media_transcription)

# --- TAB 3: DIRECT TEXT ---
with tab3:
    manual_text = st.text_area(
        "ఫిర్యాదు వివరాలను ఇక్కడ నేరుగా టైప్ చేయండి లేదా అదనపు సమాచారాన్ని జోడించండి:",
        height=180,
        placeholder="ఉదాహరణ: బాధితురాలి పేరు..., నిందితుడు చేసిన చర్యలు..., తేదీ మరియు సమయం..."
    )
    if manual_text.strip():
        complaint_text_payload += "\n" + manual_text.strip()

# =========================================================
# 6. ACTION BUTTON & ANALYSIS PIPELINE
# =========================================================
st.markdown("---")
analyze_btn = st.button("⚖️ సమగ్ర న్యాయ విశ్లేషణ ప్రారంభించండి (Analyze Complaint)", type="primary", use_container_width=True)

if analyze_btn:
    if not complaint_text_payload.strip() and not images_payload:
        st.error("దయచేసి ఏదైనా పత్రాన్ని అప్‌లోడ్ చేయండి, వాయిస్ రికార్డ్ చేయండి లేదా టెక్స్ట్ బాక్స్‌లో ఫిర్యాదు వివరాలను నమోదు చేయండి.")
    else:
        with st.spinner("⚖️ BNS, BNSS, BSA మరియు IPC, CrPC, IEA నిబంధనల ప్రకారం పూర్తి దర్యాప్తు నివేదిక రూపొందించబడుతోంది..."):
            try:
                report = ""
                used_model = ""

                if images_payload:
                    report, used_model = call_groq_vision_completion(images_payload, complaint_text_payload)
                else:
                    report, used_model = call_groq_text_completion(complaint_text_payload)

                st.subheader("📋 సమగ్ర BNS / BNSS / BSA లీగల్ & ఇన్వెస్టిగేషన్ నివేదిక")
                st.markdown(report)
                st.caption(f"విశ్లేషణ కోసం ఉపయోగించిన Groq AI మోడల్: `{used_model}`")

                st.download_button(
                    label="📥 నివేదికను డౌన్‌లోడ్ చేయండి (Download Report as Text)",
                    data=report,
                    file_name="BNS_BSA_Investigation_Report.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"విశ్లేషణ సమయంలో లోపం ఏర్పడింది: {str(e)}")
                st.info("సలహా: Groq API కీ సరైనదో కాదో చెక్ చేయండి. సర్వర్ రద్దీగా ఉంటే కొద్దిసేపటి తర్వాత మళ్ళీ ప్రయత్నించండి.")
