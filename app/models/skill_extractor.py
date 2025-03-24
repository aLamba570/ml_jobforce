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

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        print(f"Opening PDF file: {pdf_path}")
        pdf_file_exists = os.path.isfile(pdf_path)
        print(f"File exists: {pdf_file_exists}")
        
        if not pdf_file_exists:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        print(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_docx(docx_path):
    """Extract text from a DOCX file"""
    try:
        print(f"Opening DOCX file: {docx_path}")
        doc = docx.Document(docx_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text.append(paragraph.text)
        
        result = '\n'.join(text)
        print(f"Extracted {len(result)} characters from DOCX")
        return result
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
        raise

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
    # For debugging
    print(f"Extracting skills from text: {text[:100]}...")
    
    # Preprocess text
    processed_text = preprocess_text(text) if preprocess_text else text.lower()
    
    # Extract skills using the skills vocabulary
    technical_skills = []
    soft_skills = []
    
    # If we have skills databases
    if ALL_SKILLS:
        # Simple keyword matching for testing
        words = set(processed_text.split())
        
        # Match against technical skills
        for skill in SKILLS_DB.get("technical_skills", []):
            if skill.lower() in processed_text:
                technical_skills.append(skill)
                
        # Match against soft skills
        for skill in SKILLS_DB.get("soft_skills", []):
            if skill.lower() in processed_text:
                soft_skills.append(skill)
    else:
        # Fallback skills for testing when no vocabulary is available
        print("Warning: Using fallback skills detection")
        common_tech_skills = ["javascript", "python", "java", "c++", "react", "angular", 
                              "node.js", "express", "mongodb", "sql", "aws", "docker", "kubernetes"]
        common_soft_skills = ["communication", "leadership", "teamwork", "problem-solving", 
                              "creativity", "time management", "adaptability"]
        
        # Simple keyword matching
        for skill in common_tech_skills:
            if skill.lower() in processed_text:
                technical_skills.append(skill)
                
        for skill in common_soft_skills:
            if skill.lower() in processed_text:
                soft_skills.append(skill)
    
    # Log extracted skills
    print(f"Extracted technical skills: {technical_skills}")
    print(f"Extracted soft skills: {soft_skills}")
    
    return {
        "technical_skills": technical_skills,
        "soft_skills": soft_skills
    }

def extract_experience_years(text):
    """Extract years of experience from text"""
    experience_pattern = r'(\d+)(?:\+)?\s+(?:years?|yrs?)(?:\s+of)?\s+experience'
    matches = re.findall(experience_pattern, text.lower())
    
    if matches:
        # Return the highest number of years mentioned
        return max(int(year) for year in matches)
    return None

def extract_skills_from_file(file):
    """Extract skills from a file (PDF or DOCX)"""
    try:
        # Determine file type and extract text
        filename = file.filename
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Use a Windows-compatible temp directory
        import tempfile
        temp_dir = tempfile.gettempdir()  # This will work on all platforms
        temp_filename = f"resume_{os.urandom(8).hex()}{file_extension}"
        temp_filepath = os.path.join(temp_dir, temp_filename)
        
        print(f"Using temp directory: {temp_dir}")
        print(f"Saving file to: {temp_filepath}")
        
        # Save to temporary file for processing
        file.save(temp_filepath)
        print(f"File saved successfully to {temp_filepath}")
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = extract_text_from_pdf(temp_filepath)
        elif file_extension == '.docx':
            text = extract_text_from_docx(temp_filepath)
        else:
            # Should never reach here due to earlier validation
            raise ValueError(f"Unsupported file format: {file_extension}")
            
        print(f"Extracted text from file ({len(text)} characters)")
        
        # Clean up temp file
        try:
            os.remove(temp_filepath)
            print(f"Temp file removed: {temp_filepath}")
        except Exception as e:
            print(f"Warning: Failed to remove temp file: {e}")
            
        # Process the extracted text
        if not text:
            print("Warning: No text extracted from file")
            return {"technical_skills": [], "soft_skills": []}
            
        # Use the existing text processing function
        return extract_skills_from_text(text)
        
    except Exception as e:
        import traceback
        print(f"Error in extract_skills_from_file: {str(e)}")
        print(traceback.format_exc())
        raise