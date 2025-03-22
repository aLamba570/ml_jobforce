import os
import re
import json
import spacy
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
import docx
import io

# Load spaCy model
nlp = spacy.load("en_core_web_md")

# Load vocabulary files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '../../data')

# Load skills vocabulary
try:
    with open(os.path.join(DATA_DIR, 'skills_vocabulary.json'), 'r') as f:
        SKILLS_DB = json.load(f)
except FileNotFoundError:
    print("Warning: skills_vocabulary.json not found, using fallback skills")
    SKILLS_DB = {"technical_skills": [], "soft_skills": []}

# Load job titles
try:
    with open(os.path.join(DATA_DIR, 'job_titles_keyword.json'), 'r') as f:
        JOB_TITLES = json.load(f)
except FileNotFoundError:
    print("Warning: job_titles_keyword.json not found, using empty job titles list")
    JOB_TITLES = []

# Load industry keywords
try:
    with open(os.path.join(DATA_DIR, 'industrykeywords.json'), 'r') as f:
        INDUSTRY_KEYWORDS = json.load(f)
except FileNotFoundError:
    print("Warning: industrykeywords.json not found, using empty industry keywords list")
    INDUSTRY_KEYWORDS = []

# Flatten skills for faster lookup
ALL_SKILLS = set(SKILLS_DB.get("technical_skills", []) + SKILLS_DB.get("soft_skills", []))

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file"""
    doc = docx.Document(docx_file)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return '\n'.join(text)

def preprocess_text(text):
    """Preprocess text by removing special characters and normalizing"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_skills_from_text(text):
    """
    Extract skills from text using NLP techniques
    Returns a dictionary with categorized skills and additional metadata
    """
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    
    # Extract skills using spaCy NER and pattern matching
    technical_skills = set()
    soft_skills = set()
    job_titles = set()
    industries = set()
    
    # 1. Direct pattern matching with skills database
    for skill in SKILLS_DB.get("technical_skills", []):
        if re.search(r'\b' + re.escape(skill) + r'\b', preprocessed_text):
            technical_skills.add(skill)
            
    for skill in SKILLS_DB.get("soft_skills", []):
        if re.search(r'\b' + re.escape(skill) + r'\b', preprocessed_text):
            soft_skills.add(skill)
    
    # 2. Extract job titles
    for title in JOB_TITLES:
        if re.search(r'\b' + re.escape(title.lower()) + r'\b', preprocessed_text):
            job_titles.add(title)
    
    # 3. Extract industry keywords
    for industry in INDUSTRY_KEYWORDS:
        if re.search(r'\b' + re.escape(industry.lower()) + r'\b', preprocessed_text):
            industries.add(industry)
    
    # 4. Use spaCy for named entity recognition and phrase extraction
    doc = nlp(preprocessed_text)
    
    # Extract entities that could be skills, job titles, or industries
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            entity_text = ent.text.lower()
            
            # Check if entity contains a skill
            for skill in ALL_SKILLS:
                if skill in entity_text:
                    if skill in SKILLS_DB.get("technical_skills", []):
                        technical_skills.add(skill)
                    else:
                        soft_skills.add(skill)
    
    # 5. Extract noun phrases as potential skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        
        # Check if chunk contains a skill
        for skill in ALL_SKILLS:
            if skill in chunk_text:
                if skill in SKILLS_DB.get("technical_skills", []):
                    technical_skills.add(skill)
                else:
                    soft_skills.add(skill)
    
    # 6. Get experience levels from text
    experience_years = extract_experience_years(text)
    
    # Combine results
    result = {
        "technical_skills": list(technical_skills),
        "soft_skills": list(soft_skills),
        "job_titles": list(job_titles),
        "industries": list(industries),
        "experience_years": experience_years,
        "all_skills": list(technical_skills.union(soft_skills))
    }
    
    return result

def extract_experience_years(text):
    """Extract years of experience from text"""
    experience_pattern = r'(\d+)(?:\+)?\s+(?:years?|yrs?)(?:\s+of)?\s+experience'
    matches = re.findall(experience_pattern, text.lower())
    
    if matches:
        # Return the highest number of years mentioned
        return max(int(year) for year in matches)
    return None

def extract_skills_from_file(file):
    """Extract skills from a resume file (PDF or DOCX)"""
    filename = file.filename
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Create in-memory file-like object
    file_stream = io.BytesIO(file.read())
    
    # Extract text based on file type
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_stream)
    elif file_extension == '.docx':
        text = extract_text_from_docx(file_stream)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    # Extract skills from the text
    skills_data = extract_skills_from_text(text)
    
    # Add the raw text for future processing
    skills_data["raw_text"] = text
    
    return skills_data