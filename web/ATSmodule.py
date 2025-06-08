"""
Action Items:
- Fix the module import errors - done
- create this file as a package and import in app.py - done
"""
import openai
import os
import fitz  # PyMuPDF for PDF parsing

def extract_text_from_pdf(pdf_path):
    # Extracts text from a PDF file.
    doc = fitz.open(pdf_path)
    text = " ".join(page.get_text() for page in doc)
    return text

def analyze_resume(job_description, resume_text):
    # Uses OpenAI API to compute ATS score and provide detailed suggestions.
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