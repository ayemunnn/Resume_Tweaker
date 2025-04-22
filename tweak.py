import streamlit as st
import google.generativeai as genai
import os
import json
import PyPDF2
import docx

# --- API Key Configuration ---
try:
    api_key = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=api_key)
except KeyError:
    st.error("Please set GEMINI_API_KEY as an environment variable.")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash')

# --- Parsing Functions ---
def parse_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def parse_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_txt(file):
    return file.read().decode("utf-8")

def parse_resume(file):
    if file.name.lower().endswith(".pdf"):
        return parse_pdf(file)
    elif file.name.lower().endswith(".docx"):
        return parse_docx(file)
    elif file.name.lower().endswith(".txt"):
        return parse_txt(file)
    else:
        st.warning("Unsupported resume file format.")
        return None

# --- Gemini Interaction ---
def call_gemini(prompt, text_data=None):
    full_prompt = prompt
    if text_data:
        full_prompt += f"\n\n---\nText Data:\n{text_data}\n---"
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

# --- Analysis Prompts ---
def analyze_resume_text(resume_text):
    prompt = """
    Analyze the following resume text. Extract key information including:
    - Contact Information (Name, Email, Phone, Location - if available)
    - Summary
    - Skills (Technical, Soft, Tools, Languages)
    - Work Experience (Title, Company, Dates, Location, Responsibilities)
    - Education
    - Certifications

    Return as JSON.
    """
    response = call_gemini(prompt, resume_text)
    try:
        return json.loads(response)
    except:
        st.warning("Could not parse resume JSON. Showing raw output.")
        return response

def analyze_jd_text(jd_text):
    prompt = """
    Analyze the following job description text. Extract key requirements including:
    - Job Title
    - Required Skills (Technical, Soft, Tools)
    - Required Experience & Education
    - Key Responsibilities
    - ATS Keywords

    Return as JSON.
    """
    response = call_gemini(prompt, jd_text)
    try:
        return json.loads(response)
    except:
        st.warning("Could not parse JD JSON. Showing raw output.")
        return response

def compare_data(resume_data, jd_data):
    prompt = f"""
    Compare the resume data and job description below.

    Resume:
    ```json
    {json.dumps(resume_data, indent=2)}
    ```

    Job Description:
    ```json
    {json.dumps(jd_data, indent=2)}
    ```

    Provide a markdown-formatted report with:
    - Skill Matches and Gaps
    - Experience Fit
    - Education & Certification Match
    - ATS Keyword Coverage
    - Make all the suggested changes, following the same formate as the uploaded resume.
    """
    return call_gemini(prompt)

# --- Streamlit App UI ---
st.title("📄 Resume Matcher using Gemini AI")

st.markdown("Upload your resume and paste a job description to analyze & compare.")

with st.sidebar:
    resume_file = st.file_uploader("📤 Upload Resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

jd_text_input = st.text_area("📋 Paste Job Description Here", height=300, help="Copy the JD text and paste it here")

if resume_file and jd_text_input.strip():
    with st.spinner("Analyzing your resume and job description..."):
        resume_text = parse_resume(resume_file)

        resume_data = analyze_resume_text(resume_text)
        jd_data = analyze_jd_text(jd_text_input)

        st.subheader("📌 Resume Insights")
        st.json(resume_data if isinstance(resume_data, dict) else {"Raw Output": resume_data})

        st.subheader("📌 Job Description Insights")
        st.json(jd_data if isinstance(jd_data, dict) else {"Raw Output": jd_data})

        comparison_report = compare_data(resume_data, jd_data)

    st.subheader("✅ Match Report")
    st.markdown(comparison_report)
else:
    st.info("Please upload your resume and paste a job description to continue.")
