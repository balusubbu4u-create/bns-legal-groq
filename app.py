import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from PIL import Image
import base64
import fitz
from io import BytesIO

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="BNS FIR Legal Assistant",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA FIR Legal Assistant")

st.caption(
    "Complaint facts ఆధారంగా preliminary legal analysis కోసం."
)

st.warning(
    "⚠️ ఇది AI-assisted preliminary analysis మాత్రమే. "
    "FIRలో sections నమోదు చేసే ముందు అధికారిక BNS/BNSS/BSA text, "
    "complaint facts మరియు evidence ఆధారంగా verification చేయాలి."
)

# =========================================================
# GROQ API
# =========================================================

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    st.error(
        "GROQ_API_KEY కనిపించలేదు. "
        "Streamlit → Settings → Secretsలో GROQ_API_KEY set చేయండి."
    )
    st.stop()

# =========================================================
# MODELS
# =========================================================

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-11b-vision-preview"

# =========================================================
# LEGAL SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """You are a highly cautious Indian criminal-law FIR analysis assistant.

Analyze complaints under:
- Bharatiya Nyaya Sanhita, 2023 (BNS)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
- Bharatiya Sakshya Adhiniyam, 2023 (BSA)

VERY IMPORTANT:
1. NEVER invent a section number.
2. Do not assume that every allegation automatically constitutes an offence.
3. Use ONLY facts present in the complaint.
4. Do not add facts which are not stated.
5. Separate:
   - Alleged facts
   - Legal ingredients
   - Facts supporting the ingredient
   - Missing facts
   - Evidence required
   - Possible section
   - Verification required
6. If the facts are insufficient, clearly say: "Further verification required."
7. For BNS Section 85, carefully check whether the facts satisfy the statutory meaning of cruelty under Section 86.
8. A salary/money dispute should NOT automatically be treated as dowry/property demand or cruelty.
9. A threat to kill should be examined separately as criminal intimidation. Verify the exact threat, circumstances and intention to cause alarm.
10. A husband living with another woman should not automatically be treated as a criminal offence. Analyze only what is actually alleged.
11. Do not fabricate judgments, case laws, circulars or government orders."""

# =========================================================
# HELPER FUNCTIONS FOR FILE PROCESSING
# =========================================================

def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    
    if len(text.strip()) < 50:
        st.info("📷 Scanned / Image PDF గుర్తించబడింది. PyMuPDF (fitz) ద్వారా Image processing జరుగుతోంది...")
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img = Image.open(BytesIO(pix.tobytes("png")))
            images.append(img)
        return images
    
    return text

# =========================================================
# USER INTERFACE & INPUT
# =========================================================

uploaded_file = st.file_uploader(
    "ఫిర్యాదు పత్రాన్ని (PDF, Word, or Image) అప్లోడ్ చేయండి:",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
)

manual_text = st.text_area(
    "లేదా ఫిర్యాదు వివరాలను (Complaint facts) ఇక్కడ టైప్ చేయండి లేదా పేస్ట్ చేయండి:"
)

analyze_btn = st.button("⚖️ Analyze Complaint", type="primary")

# =========================================================
# ANALYSIS LOGIC
# =========================================================

if analyze_btn:
    complaint_content = ""
    image_contents = []

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension in ["png", "jpg", "jpeg"]:
            image = Image.open(uploaded_file)
            image_contents.append(image)
            complaint_content = "Please analyze the attached image/screenshot of the complaint."
            
        elif file_extension == "docx":
            complaint_content = extract_text_from_docx(uploaded_file)
            
        elif file_extension == "pdf":
            result = extract_text_from_pdf(uploaded_file)
            if isinstance(result, list):
                image_contents = result
                complaint_content = "Please analyze the attached scanned PDF pages of the complaint."
            else:
                complaint_content = result
                
        elif file_extension == "txt":
            complaint_content = str(uploaded_file.read(), "utf-8")

    if manual_text.strip():
        if complaint_content:
            complaint_content += "\n\n" + manual_text
        else:
            complaint_content = manual_text

    if not complaint_content.strip() and not image_contents:
        st.error("தயவுசெய்து ఏదైనా ఫైల్ అప్లోడ్ చేయండి లేదా కింద టెక్స్ట్ రాయండి.")
    else:
        with st.spinner("Legal analysis జరుగుతోంది... దయచేసి వేచి ఉండండి."):
            try:
                if image_contents:
                    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    
                    user_content = [{"type": "text", "text": complaint_content}]
                    for img in image_contents:
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        user_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                        })
                    
                    messages.append({"role": "user", "content": user_content})
                    
                    response = client.chat.completions.create(
                        model=VISION_MODEL,
                        messages=messages,
                        temperature=0.1
                    )
                else:
                    response = client.chat.completions.create(
                        model=TEXT_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Here is the complaint text for analysis:\n\n{complaint_content}"}
                        ],
                        temperature=0.1
                    )

                analysis_result = response.choices[0].message.content
                
                st.subheader("📋 Preliminary Legal Analysis Report")
                st.markdown(analysis_result)

            except Exception as e:
                st.error(f"విశ్లేషణలో లోపం (Error): {e}")
