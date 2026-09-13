import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from PIL import Image
import base64
import fitz  # PyMuPDF
from io import BytesIO

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="BNS FIR Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA FIR Legal Assistant")
st.caption("Complaint facts ఆధారంగా ప్రాథమిక చట్టపరమైన విశ్లేషణ (Preliminary Legal Analysis).")

st.warning(
    "⚠️ ఇది AI-assisted preliminary analysis మాత్రమే. "
    "FIRలో సెక్షన్లు నమోదు చేసే ముందు అధికారిక BNS, BNSS, BSA చట్టాలు, "
    "ఫిర్యాదు వివరాలు మరియు సాక్ష్యాధారాల ఆధారంగా ధృవీకరించుకోవాలి."
)

# =========================================================
# 2. GROQ CLIENT & MODEL DISCOVERY
# =========================================================
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY కనిపించలేదు. Streamlit Secrets లో GROQ_API_KEY ని సెట్ చేయండి.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@st.cache_data(ttl=3600)
def get_available_models():
    """Groq API ద్వారా మీ ఖాతాకు అందుబాటులో ఉన్న మోడళ్లను గుర్తిస్తుంది."""
    try:
        models_data = client.models.list()
        all_models = [m.id for m in models_data.data]
        
        # టెక్స్ట్ మోడల్స్ ప్రాధాన్యత క్రమం
        preferred_text = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        text_models = [m for m in preferred_text if m in all_models]
        if not text_models:
            text_models = [m for m in all_models if "vision" not in m.lower()]
            
        # విజన్ మోడల్స్ ప్రాధాన్యత క్రమం
        preferred_vision = [
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview"
        ]
        vision_models = [m for m in preferred_vision if m in all_models]
        if not vision_models:
            vision_models = [m for m in all_models if "vision" in m.lower()]

        return text_models, vision_models
    except Exception:
        # నెట్‌వర్క్ లేదా API సమస్య వస్తే డీఫాల్ట్ లిస్ట్
        return ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"], ["llama-3.2-11b-vision-preview"]

text_model_list, vision_model_list = get_available_models()

# సైడ్‌బార్ సెట్టింగ్స్
st.sidebar.header("⚙️ Model Settings")
selected_text_model = st.sidebar.selectbox("Text Model ఎంచుకోండి:", text_model_list, index=0)

if vision_model_list:
    selected_vision_model = st.sidebar.selectbox("Vision Model ఎంచుకోండి:", vision_model_list, index=0)
else:
    selected_vision_model = None
    st.sidebar.warning("విజన్ మోడల్స్ మీ ఖాతాకు అందుబాటులో లేవు.")

# =========================================================
# 3. LEGAL SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = """You are a highly cautious Indian criminal-law FIR analysis assistant.

Analyze complaints under:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

VERY IMPORTANT RULES:
1. NEVER invent a section number.
2. Do not assume that every allegation automatically constitutes an offence.
3. Use ONLY facts present in the complaint. Do not add facts which are not stated.
4. Separate:
   - Alleged facts
   - Legal ingredients
   - Facts supporting the ingredient
   - Missing facts
   - Evidence required
   - Possible section
   - Verification required
5. If the facts are insufficient, clearly say: "Further verification required."
6. For BNS Section 85, carefully check whether the facts satisfy cruelty under Section 86.
7. A salary/money dispute should NOT automatically be treated as dowry demand or cruelty.
8. A threat to kill should be examined separately as criminal intimidation. Verify the circumstances and intention to cause alarm.
9. A husband living with another woman should not automatically be treated as a criminal offence. Analyze only what is actually alleged.
10. Do not fabricate judgments, case laws, circulars, or government orders."""

# =========================================================
# 4. HELPER FUNCTIONS (DOCUMENT & IMAGE PROCESSING)
# =========================================================
def extract_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def process_pdf_file(file):
    """సాధారణ టెక్స్ట్ PDF అయితే టెక్స్ట్‌ని, స్కాన్ చేసిన PDF అయితే ఇమేజ్‌లను ఇస్తుంది."""
    reader = PdfReader(file)
    extracted_text = ""
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            extracted_text += txt + "\n"
    
    # 60 కంటే తక్కువ అక్షరాలు ఉంటే అది స్కాన్ చేసిన PDFగా పరిగణించబడుతుంది
    if len(extracted_text.strip()) < 60:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        images = []
        # మెమొరీ మరియు టోకెన్ పరిమితి దృష్ట్యా గరిష్టంగా 5 పేజీలు
        max_pages = min(len(doc), 5)
        for page_idx in range(max_pages):
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=130)
            img = Image.open(BytesIO(pix.tobytes("png")))
            # సైజు కుదించడం
            img.thumbnail((1200, 1200))
            images.append(img)
        return False, images
    
    return True, extracted_text

def encode_image_to_base64(pil_image):
    buffered = BytesIO()
    # JPEG లోకి మార్చి సైజును తగ్గించడం
    pil_image.convert("RGB").save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# =========================================================
# 5. USER INTERFACE
# =========================================================
uploaded_file = st.file_uploader(
    "ఫిర్యాదు పత్రాన్ని అప్‌లోడ్ చేయండి (PDF, Word, or Image):",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
)

manual_text = st.text_area(
    "లేదా ఫిర్యాదు వివరాలను (Complaint facts) ఇక్కడ టైప్ చేయండి / పేస్ట్ చేయండి:",
    height=150
)

analyze_btn = st.button("⚖️ Analyze Complaint", type="primary")

# =========================================================
# 6. EXECUTION LOGIC
# =========================================================
if analyze_btn:
    complaint_text = manual_text.strip()
    images_to_analyze = []
    
    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1].lower()
        
        if ext in ["png", "jpg", "jpeg"]:
            img = Image.open(uploaded_file)
            img.thumbnail((1200, 1200))
            images_to_analyze.append(img)
            
        elif ext == "docx":
            complaint_text += "\n" + extract_from_docx(uploaded_file)
            
        elif ext == "txt":
            complaint_text += "\n" + str(uploaded_file.read(), "utf-8", errors="ignore")
            
        elif ext == "pdf":
            is_text, result = process_pdf_file(uploaded_file)
            if is_text:
                complaint_text += "\n" + result
            else:
                st.info("📷 ఇది స్కాన్ చేసిన PDF అని గుర్తించబడింది. విజన్ ప్రాసెసింగ్ జరుగుతోంది...")
                images_to_analyze = result

    # ఇన్‌పుట్ వెరిఫికేషన్
    if not complaint_text.strip() and not images_to_analyze:
        st.error("దయచేసి ఏదైనా ఫైల్ అప్‌లోడ్ చేయండి లేదా ఫిర్యాదు వివరాలను టెక్స్ట్ బాక్స్‌లో నమోదు చేయండి.")
    else:
        with st.spinner("⚖️ చట్టపరమైన విశ్లేషణ జరుగుతోంది... దయచేసి వేచి ఉండండి."):
            try:
                # కేస్ 1: ఇమేజ్ లేదా స్కాన్ చేసిన PDF విశ్లేషణ
                if images_to_analyze:
                    if not selected_vision_model:
                        st.error("మీ ఖాతాలో విజన్ మోడల్ అందుబాటులో లేదు. దయచేసి టెక్స్ట్ రూపంలో ఫిర్యాదును అందించండి.")
                    else:
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                        user_content = []
                        
                        prompt_msg = "Please read and analyze the attached scanned complaint document."
                        if complaint_text:
                            prompt_msg += f"\nAdditional notes:\n{complaint_text}"
                            
                        user_content.append({"type": "text", "text": prompt_msg})
                        
                        for img in images_to_analyze:
                            b64 = encode_image_to_base64(img)
                            user_content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                            })
                            
                        messages.append({"role": "user", "content": user_content})
                        
                        response = client.chat.completions.create(
                            model=selected_vision_model,
                            messages=messages,
                            temperature=0.1
                        )
                        st.subheader("📋 Preliminary Legal Analysis Report")
                        st.markdown(response.choices[0].message.content)
                        st.caption(f"Used Vision Model: `{selected_vision_model}`")

                # కేస్ 2: సాధారణ టెక్స్ట్ విశ్లేషణ
                else:
                    response = client.chat.completions.create(
                        model=selected_text_model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Analyze this complaint:\n\n{complaint_text}"}
                        ],
                        temperature=0.1
                    )
                    st.subheader("📋 Preliminary Legal Analysis Report")
                    st.markdown(response.choices[0].message.content)
                    st.caption(f"Used Text Model: `{selected_text_model}`")

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం సంభవించింది: {e}")
                st.info("సలహా: సైడ్‌బార్‌లోని మోడల్ మార్చి మళ్ళీ 'Analyze Complaint' క్లిక్ చేసి చూడండి.")
