import os
import re
import json
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Load spaCy model
nlp = spacy.load("en_core_web_md")

# Load data files
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '../../data')

def load_data_file(filename):
    """Load a JSON data file from the data directory"""
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Data file not found at {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {file_path}")
        return {}

# Load all data files
SKILLS_VOCAB = load_data_file('skills_vocabulary.json')
JOB_TITLES = load_data_file('job_titles_keyword.json')
INDUSTRY_KEYWORDS = load_data_file('industrykeywords.json')

def preprocess_text(text):
    """Preprocess text by cleaning and normalizing"""
    if not text:
        return ""
        
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits (keeping spaces)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_ngrams(text, n=1):
    """Extract n-grams from text"""
    words = text.split()
    ngrams = []
    
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i + n])
        ngrams.append(ngram)
        
    return ngrams

def get_all_skills():
    """Get a flattened list of all skills"""
    all_skills = []
    
    # Extract all skills from the vocabulary
    if isinstance(SKILLS_VOCAB, dict):
        for category, skills in SKILLS_VOCAB.items():
            if isinstance(skills, list):
                all_skills.extend(skills)
    elif isinstance(SKILLS_VOCAB, list):
        all_skills.extend(SKILLS_VOCAB)
        
    return all_skills

def get_all_job_titles():
    """Get a flattened list of all job titles"""
    all_titles = []
    
    # Extract all job titles
    if isinstance(JOB_TITLES, dict):
        for category, titles in JOB_TITLES.items():
            if isinstance(titles, list):
                all_titles.extend(titles)
    elif isinstance(JOB_TITLES, list):
        all_titles.extend(JOB_TITLES)
        
    return all_titles

def get_all_industry_keywords():
    """Get a flattened list of all industry keywords"""
    all_keywords = []
    
    # Extract all industry keywords
    if isinstance(INDUSTRY_KEYWORDS, dict):
        for category, keywords in INDUSTRY_KEYWORDS.items():
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
    elif isinstance(INDUSTRY_KEYWORDS, list):
        all_keywords.extend(INDUSTRY_KEYWORDS)
        
    return all_keywords