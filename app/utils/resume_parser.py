import os
import re
import json
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
import docx
import io
from app.utils.text_processor import (
    preprocess_text, extract_ngrams, get_all_skills,
    get_all_job_titles, get_all_industry_keywords, nlp
)

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

def extract_skills_from_text(text):
    """
    Extract skills from text using NLP techniques and skills vocabulary
    """
    if not text:
        return []
        
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    
    # Get all skills from vocabulary
    all_skills = get_all_skills()
    
    # Extract skills using pattern matching and NLP
    extracted_skills = set()
    
    # 1. Direct pattern matching with skills database
    for skill in all_skills:
        if re.search(r'\b' + re.escape(skill.lower()) + r'\b', preprocessed_text):
            extracted_skills.add(skill)
    
    # 2. Use spaCy for named entity recognition and noun phrase extraction
    doc = nlp(preprocessed_text)
    
    # Extract entities that might be skills
    for ent in doc.ents:
        # Organizations and products might be technologies or frameworks
        if ent.label_ in ["ORG", "PRODUCT"]:
            skill_candidate = ent.text.lower()
            for skill in all_skills:
                if skill.lower() in skill_candidate:
                    extracted_skills.add(skill)
    
    # Extract noun phrases as potential skills
    for chunk in doc.noun_chunks:
        skill_candidate = chunk.text.lower()
        for skill in all_skills:
            if skill.lower() in skill_candidate:
                extracted_skills.add(skill)
    
    # 3. Extract n-grams and compare against skills
    # Generate n-grams from 1 to 3 words
    for n in range(1, 4):
        ngrams = extract_ngrams(preprocessed_text, n)
        for ngram in ngrams:
            for skill in all_skills:
                if ngram == skill.lower():
                    extracted_skills.add(skill)
    
    # Convert set to list for JSON serialization
    return list(extracted_skills)

def extract_job_titles_from_text(text):
    """
    Extract job titles from resume text
    """
    if not text:
        return []
        
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    
    # Get all job titles
    all_titles = get_all_job_titles()
    
    # Extract job titles using pattern matching
    extracted_titles = set()
    
    for title in all_titles:
        if re.search(r'\b' + re.escape(title.lower()) + r'\b', preprocessed_text):
            extracted_titles.add(title)
    
    # Extract n-grams and compare against job titles
    for n in range(1, 4):  # up to 3-grams
        ngrams = extract_ngrams(preprocessed_text, n)
        for ngram in ngrams:
            for title in all_titles:
                if ngram == title.lower():
                    extracted_titles.add(title)
    
    return list(extracted_titles)

def extract_industry_keywords(text):
    """
    Extract industry keywords from resume text
    """
    if not text:
        return []
        
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    
    # Get all industry keywords
    all_keywords = get_all_industry_keywords()
    
    # Extract industry keywords using pattern matching
    extracted_keywords = set()
    
    for keyword in all_keywords:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', preprocessed_text):
            extracted_keywords.add(keyword)
    
    return list(extracted_keywords)

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
    
    # Extract various information from the text
    skills = extract_skills_from_text(text)
    job_titles = extract_job_titles_from_text(text)
    industry_keywords = extract_industry_keywords(text)
    
    return {
        "skills": skills,
        "job_titles": job_titles,
        "industry_keywords": industry_keywords,
        "raw_text": text
    }