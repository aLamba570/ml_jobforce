import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from sentence_transformers import SentenceTransformer
from app.utils.job_scraper import scrape_jobs_by_skills
import pymongo
import os
from datetime import datetime, timedelta

# Database connection for MongoDB
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://alamba570:ankush@cluster0.opvl6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
DB_NAME = os.environ.get('DB_NAME', 'jobforce')

# Load spaCy model for basic NLP tasks
nlp = spacy.load("en_core_web_md")

# Load sentence transformer model for semantic similarity
try:
    sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
except:
    # Fallback to a simpler model if main one isn't available
    sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

def connect_to_mongodb():
    """Connect to MongoDB and return database connection"""
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def preprocess_job_description(job_description):
    """Preprocess job description text for better matching"""
    # Use spaCy to remove stopwords and non-relevant tokens
    doc = nlp(job_description.lower())
    
    # Keep only relevant parts of speech and remove stopwords
    tokens = [token.lemma_ for token in doc 
              if not token.is_stop and not token.is_punct 
              and token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB']]
    
    return " ".join(tokens)

def get_jobs_from_db(skills=None, limit=50):
    """Get jobs from MongoDB database, filtered by skills if provided"""
    db = connect_to_mongodb()
    if not db:
        return []
        
    jobs_collection = db['jobs']
    
    # Base query - get recent jobs
    query = {
        'scrapedAt': {'$gte': datetime.now() - timedelta(days=30)}  # Jobs from last 30 days
    }
    
    # If skills provided, filter by skills
    if skills and len(skills) > 0:
        query['skills'] = {'$in': skills}
    
    # Find jobs
    jobs = list(jobs_collection.find(
        query,
        {'_id': 1, 'title': 1, 'company': 1, 'description': 1, 'skills': 1, 
         'location': 1, 'url': 1, 'source': 1, 'postedAt': 1}
    ).sort('postedAt', -1).limit(limit))
    
    # Convert MongoDB _id to string
    for job in jobs:
        job['id'] = str(job.pop('_id'))
    
    return jobs

def match_jobs_to_skills(skills, limit=10):
    """
    Match jobs to the list of extracted skills
    Returns jobs ranked by relevance
    """
    # Try to get jobs from DB
    db_jobs = get_jobs_from_db(skills, limit=100)
    
    # If not enough jobs in DB, scrape some new ones
    if len(db_jobs) < 20:
        scraped_jobs = scrape_jobs_by_skills(skills, limit=50)
        
        # Save scraped jobs to DB
        if scraped_jobs:
            db = connect_to_mongodb()
            if db:
                jobs_collection = db['jobs']
                
                # Prepare jobs for insertion
                for job in scraped_jobs:
                    # Create upsert query to avoid duplicates
                    filter_query = {'source': job['source'], 'sourceId': job['sourceId']}
                    jobs_collection.update_one(filter_query, {'$set': job}, upsert=True)
                
                # Get updated list of jobs
                db_jobs = get_jobs_from_db(skills, limit=100)
    
    # Calculate relevance scores for the jobs
    job_scores = []
    
    for job in db_jobs:
        # Count matching skills
        job_skills = job.get('skills', [])
        matching_skills = set(skills).intersection(set(job_skills))
        skill_match_count = len(matching_skills)
        
        # Calculate skill match ratio
        if job_skills:
            skill_coverage = len(matching_skills) / len(skills) if skills else 0
            skill_relevance = len(matching_skills) / len(job_skills)
            skill_score = (skill_coverage + skill_relevance) / 2
        else:
            skill_score = 0
        
        # Calculate recency score (newer jobs score higher)
        posted_at = job.get('postedAt')
        if posted_at:
            days_old = (datetime.now() - posted_at).days
            recency_score = max(0, 1 - (days_old / 30))  # Linear decay over 30 days
        else:
            recency_score = 0.5  # Default score if date unknown
        
        # Combined score (70% skill match, 30% recency)
        combined_score = (skill_score * 0.7) + (recency_score * 0.3)
        match_score = int(combined_score * 100)
        
        job_scores.append({
            "id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location", ""),
            "description": job.get("description", ""),
            "skills": job.get("skills", []),
            "url": job.get("url", ""),
            "matching_skills": list(matching_skills),
            "match_score": match_score,
            "source": job.get("source", ""),
            "posted_at": job.get("postedAt")
        })
    
    # Sort by match score (descending)
    ranked_jobs = sorted(job_scores, key=lambda x: x["match_score"], reverse=True)
    
    # Return top N results
    return ranked_jobs[:limit]

def calculate_job_similarity(resume_text, job_description):
    """
    Calculate semantic similarity between resume and job description
    Returns a similarity score between 0 and 100
    """
    # Preprocess texts
    resume_text_processed = preprocess_job_description(resume_text)
    job_description_processed = preprocess_job_description(job_description)
    
    # Check if texts are non-empty
    if not resume_text_processed or not job_description_processed:
        return 0
    
    # Generate embeddings with sentence transformer
    resume_embedding = sentence_model.encode([resume_text_processed])[0]
    job_embedding = sentence_model.encode([job_description_processed])[0]
    
    # Calculate cosine similarity
    similarity = cosine_similarity(
        resume_embedding.reshape(1, -1),
        job_embedding.reshape(1, -1)
    )[0][0]
    
    # Convert to percentage score (0-100)
    similarity_score = int(similarity * 100)
    
    return similarity_score

def get_job_recommendations(resume_text, user_skills, location=None, limit=10):
    """
    Get personalized job recommendations based on resume text and skills
    """
    # Extract skills from resume if not provided
    if not user_skills and resume_text:
        from app.models.skill_extractor import extract_skills_from_text
        skills_data = extract_skills_from_text(resume_text)
        user_skills = skills_data.get('all_skills', [])
    
    # Match jobs based on skills
    matched_jobs = match_jobs_to_skills(user_skills, limit=limit*2)
    
    # If we have resume text, refine the matches using semantic similarity
    if resume_text and matched_jobs:
        for job in matched_jobs:
            job_desc = job.get('description', '')
            if job_desc:
                similarity_score = calculate_job_similarity(resume_text, job_desc)
                # Update match score with semantic similarity (blend scores)
                job['match_score'] = int(job['match_score'] * 0.7 + similarity_score * 0.3)
        
        # Re-sort based on updated scores
        matched_jobs = sorted(matched_jobs, key=lambda x: x['match_score'], reverse=True)
    
    # Filter by location if provided
    if location and matched_jobs:
        filtered_jobs = []
        for job in matched_jobs:
            job_location = job.get('location', '').lower()
            if job_location and location.lower() in job_location:
                filtered_jobs.append(job)
        
        # If location filtering returns results, use them
        if filtered_jobs:
            matched_jobs = filtered_jobs
    
    # Return top N results
    return matched_jobs[:limit]