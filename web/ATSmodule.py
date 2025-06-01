"""
Action Items:
- Fix the module import errors
- create this file as a package and import in app.py
- Add a .env file with the OpenAI API key
- Add a README file with instructions
- Add a .gitignore file to ignore the .env file
- Add a LICENSE file
- Add a setup.py file for packaging
- update the requirements.txt file
"""
import openai
import os
import fitz  # PyMuPDF for PDF parsing
import nltk
from flask import Flask, request, render_template, send_file
from dotenv import load_dotenv

# Load API Key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
nltk.download("punkt")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = " ".join(page.get_text() for page in doc)
    return text

def analyze_resume(job_description, resume_text):
    """Uses OpenAI API to compute ATS score and provide detailed suggestions."""
    prompt = f"""
    You are an ATS system. Compare the resume with the job description and:
    1. Provide an ATS compatibility score (out of 10).
    2. Identify missing skills, experience gaps, and keyword misalignment.
    3. Format suggestions clearly under sections: 'Missing Keywords', 'Experience Gaps', and 'Recommended Changes'.

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Return the score first (as a number), followed by structured suggestions.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    output = response["choices"][0]["message"]["content"]
    score, suggestions = output.split("\n", 1)

    with open("ATS_suggestions.txt", "w") as f:
        f.write(suggestions)

    return float(score), suggestions

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        job_desc = request.form["job_desc"]
        
        if "resume" in request.files:
            resume_file = request.files["resume"]
            if resume_file.filename.endswith(".pdf"):
                resume_text = extract_text_from_pdf(resume_file)
            else:
                resume_text = resume_file.read().decode("utf-8")

            ats_score, suggestions = analyze_resume(job_desc, resume_text)
            return render_template("index.html", score=ats_score, suggestions=suggestions)

    return render_template("index.html", score=None, suggestions=None)

@app.route("/download")
def download():
    return send_file("ATS_suggestions.txt", as_attachment=True)