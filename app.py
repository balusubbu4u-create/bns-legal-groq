import streamlit as st
from groq import Groq
from pypdf import PdfReader
from docx import Document
from PIL import Image
import base64
import fitz  # PyMuPDF for scanned/image PDFs
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

SYSTEM_PROMPT = """
You are a highly cautious Indian criminal-law FIR analysis assistant.

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

6. If the facts are insufficient, clearly say:
   "Further verification required."

7. For BNS Section 85, carefully check whether the facts satisfy
   the statutory meaning of cruelty under Section 86.

8. A salary/money dispute should NOT automatically be treated as
   dowry/property demand or cruelty.

9. A threat to kill should be examined separately as criminal intimidation.
   Verify the exact threat, circumstances and intention to cause alarm.

10. A husband living with another woman should not automatically be
    treated as a criminal offence. Analyze only what is actually alleged.

11. Do not fabricate judgments, case laws, circulars or government orders.
Deenilo pdf screenshots  coverted pdf lu run svvali
