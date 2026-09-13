from io import BytesIO
import base64
from PIL import Image
from docx import Document
from pypdf import PdfReader
import fitz  # PyMuPDF for scanned/image PDFs
from groq import Groq
import streamlit as st

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="BNS FIR Legal Assistant", page_icon="⚖️", layout="wide"
)

st.title("⚖️ BNS / BNSS / BSA FIR Legal Assistant")

st.caption("Complaint facts ఆధారంగా preliminary legal analysis కోసం.")

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

TEXT_MODEL = "openai/gpt-oss-120b"
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
"""


# =========================================================
# HELPER FUNCTIONS FOR FILE EXTRACTION
# =========================================================


def extract_text_from_pdf(uploaded_file):
  reader = PdfReader(uploaded_file)
  text = ""
  for page in reader.pages:
    extracted = page.extract_text()
    if extracted:
      text += extracted + "\n"
  return text


def extract_text_from_docx(uploaded_file):
  doc = Document(uploaded_file)
  return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_scanned_pdf(uploaded_file):
  doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
  text = ""
  images = []
  for page in doc:
    text += page.get_text()
    image_list = page.get_images(full=True)
    for img in image_list:
      xref = img[0]
      base_image = doc.extract_image(xref)
      image_bytes = base_image["image"]
      images.append(Image.open(BytesIO(image_bytes)))
  return text, images


# =========================================================
# USER INTERFACE & INPUT HANDLING
# =========================================================

col1, col2 = st.columns([1, 1])

with col1:
  st.subheader("📁 Upload Complaint Document")
  uploaded_file = st.file_uploader(
      "Upload PDF, DOCX, or Image (PNG/JPG)", type=["pdf", "docx", "png", "jpg"]
  )

with col2:
  st.subheader("📝 Or Enter/Paste Complaint Text")
  complaint_text_input = st.text_area(
      "Enter complaint facts here...", height=150
  )

extracted_text = ""
uploaded_images = []

if uploaded_file is not None:
  file_extension = uploaded_file.name.split(".")[-1].lower()
  if file_extension == "pdf":
    try:
      extracted_text = extract_text_from_pdf(uploaded_file)
      if not extracted_text.strip():
        uploaded_file.seek(0)
        extracted_text, uploaded_images = extract_text_from_scanned_pdf(
            uploaded_file
        )
    except Exception as e:
      st.error(f"Error reading PDF: {e}")
  elif file_extension == "docx":
    try:
      extracted_text = extract_text_from_docx(uploaded_file)
    except Exception as e:
      st.error(f"Error reading DOCX: {e}")
  elif file_extension in ["png", "jpg", "jpeg"]:
    try:
      image = Image.open(uploaded_file)
      uploaded_images.append(image)
    except Exception as e:
      st.error(f"Error loading image: {e}")

# Combine text sources cleanly
final_complaint_content = (
    complaint_text_input.strip() if complaint_text_input else extracted_text
)

if st.button("🔍 Analyze Complaint", type="primary"):
  if not final_complaint_content and not uploaded_images:
    st.warning(
        "தயవుசெய்து complaint text ఇవ్వండి లేదా document/image upload చేయండి."
    )
  else:
    with st.spinner("Analyzing complaint facts against BNS/BNSS/BSA..."):
      try:
        if uploaded_images and not final_complaint_content:
          buffered = BytesIO()
          uploaded_images[0].save(buffered, format="JPEG")
          img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

          chat_completion = client.chat.completions.create(
              model=VISION_MODEL,
              messages=[
                  {"role": "system", "content": SYSTEM_PROMPT},
                  {
                      "role": "user",
                      "content": [
                          {
                              "type": "text",
                              "text": (
                                  "Analyze the attached FIR/complaint image"
                                  " strictly following the system prompt rules."
                              ),
                          },
                          {
                              "type": "image_url",
                              "image_url": {
                                  "url": (
                                      f"data:image/jpeg;base64,{img_base64}"
                                  )
                              },
                          },
                      ],
                  },
              ],
              temperature=0.1,
          )
        else:
          prompt = f"""
          Please analyze the following complaint/FIR text strictly based on the system guidelines:
          
          COMPLAINT TEXT:
          {final_complaint_content}
          """
          chat_completion = client.chat.completions.create(
              model=TEXT_MODEL,
              messages=[
                  {"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt},
              ],
              temperature=0.1,
          )

        analysis_result = chat_completion.choices[0].message.content
        st.subheader("📋 Preliminary Legal Analysis")
        st.markdown(analysis_result)

      except Exception as e:
        st.error(f"API Error during analysis: {e}")
