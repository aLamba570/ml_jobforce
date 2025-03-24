import time
from flask import Blueprint, request, jsonify
import json
import os
from app.models.skill_extractor import extract_skills_from_text, extract_skills_from_file
from app.models.job_matcher import match_jobs_to_skills, calculate_job_similarity
from datetime import datetime
api_bp = Blueprint('api', __name__)

# Add test route
@api_bp.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "API is working correctly"}), 200

@api_bp.route('/extract-skills', methods=['POST'])
def extract_skills_endpoint():
    """
    Extract skills from resume text or file
    Accepts either:
    - JSON with "text" field containing resume text
    - Multipart form with "file" field containing resume file (PDF/DOCX)
    - Multipart form with "resume" field containing resume file (PDF/DOCX)
    """
    try:
        print("Received skills extraction request")
        print(f"Content-Type: {request.content_type}")
        print(f"Form data keys: {list(request.form.keys())}")
        print(f"Files keys: {list(request.files.keys())}")
        
        skills_data = None
        
        # Check for file with either key name 'file' or 'resume'
        file_key = None
        if request.files:
            if 'file' in request.files:
                file_key = 'file'
            elif 'resume' in request.files:
                file_key = 'resume'
                
        if file_key:
            file = request.files[file_key]
            print(f"Processing file from '{file_key}' key: {file.filename}, mimetype: {file.mimetype}")
            
            file_extension = os.path.splitext(file.filename)[1].lower()
            print(f"File extension: {file_extension}")
            
            if file_extension not in ['.pdf', '.docx']:
                return jsonify({"error": "Unsupported file format. Please upload PDF or DOCX."}), 400
            
            try:
                skills_data = extract_skills_from_file(file)
                print(f"Extracted skills data: {skills_data}")
            except Exception as file_error:
                print(f"Error extracting skills from file: {str(file_error)}")
                import traceback
                print(traceback.format_exc())
                return jsonify({"error": f"Error processing file: {str(file_error)}"}), 500
                
        elif request.is_json and 'text' in request.json:
            text = request.json['text']
            print(f"Processing text: {text[:100]}...")  # Log first 100 chars
            
            skills_data = extract_skills_from_text(text)
        else:
            print("No valid input found")
            print(f"Is JSON: {request.is_json}")
            if request.is_json:
                print(f"JSON keys: {list(request.json.keys())}")
            return jsonify({
                "error": "No valid file or text provided", 
                "details": {
                    "content_type": request.content_type,
                    "has_files": bool(request.files),
                    "file_keys": list(request.files.keys()) if request.files else []
                }
            }), 400
        
        # Check if skills_data is None or empty
        if not skills_data:
            print("Warning: extract_skills returned empty result")
            return jsonify({"skills": []}), 200
            
        # Handle different return formats from skill extractor
        if isinstance(skills_data, list):
            # If it's already a list, return it directly
            skills_list = skills_data
        elif isinstance(skills_data, dict):
            # If it's a dictionary, combine technical and soft skills
            technical_skills = skills_data.get('technical_skills', [])
            soft_skills = skills_data.get('soft_skills', [])
            skills_list = technical_skills + soft_skills
        else:
            print(f"Unexpected skills_data format: {type(skills_data)}")
            skills_list = []
            
        print(f"Extracted skills: {skills_list}")
        return jsonify({"skills": skills_list})
    except Exception as e:
        import traceback
        print(f"Error in extract_skills_endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    
@api_bp.route('/match-jobs', methods=['POST'])
def match_jobs_endpoint():
    """
    Match jobs to extracted skills
    Accepts JSON with:
    - "skills" field containing list of skills
    - Optional "limit" field to limit number of results (default: 10)
    """
    try:
        if not request.is_json or 'skills' not in request.json:
            return jsonify({"error": "No skills provided"}), 400
            
        skills = request.json['skills']
        limit = request.json.get('limit', 10)
        
        matched_jobs = match_jobs_to_skills(skills, limit=limit)
        return jsonify({"matches": matched_jobs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/calculate-similarity', methods=['POST'])
def calculate_similarity_endpoint():
    """
    Calculate similarity between resume and job description
    Accepts JSON with:
    - "resume_text" field containing resume text
    - "job_description" field containing job description
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        resume_text = request.json.get('resume_text')
        job_description = request.json.get('job_description')
        
        if not resume_text or not job_description:
            return jsonify({"error": "Both resume_text and job_description are required"}), 400
            
        similarity_score = calculate_job_similarity(resume_text, job_description)
        return jsonify({"similarity_score": similarity_score})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@api_bp.route('/job-match', methods=['POST'])
def job_match():
    """
    Match jobs to user skills
    """
    try:
        print("Received job match request")
        
        if not request.is_json:
            return jsonify({"error": "Expected JSON with skills"}), 400
            
        data = request.json
        
        if 'skills' not in data or not isinstance(data['skills'], list):
            return jsonify({"error": "Please provide a list of skills"}), 400
            
        skills = data['skills']
        limit = int(data.get('limit', 100))  # Increased default limit to 100
        
        print(f"Matching jobs for skills: {skills}, limit: {limit}")
        
        # Import job matcher
        from app.models.job_matcher import match_jobs_to_skills, get_jobs_from_db
        
        # Try to get jobs from database first
        db_jobs = get_jobs_from_db(skills, limit=limit*2)
        print(f"Found {len(db_jobs)} matching jobs in database")
        
        # If not enough jobs in database, scrape more
        if len(db_jobs) < 20:
            print("Not enough jobs in database, scraping from external sources...")
            from app.utils.job_scraper import scrape_jobs_by_skills
            scraped_jobs = scrape_jobs_by_skills(skills, limit=limit)
            
            # Convert to format compatible with database jobs
            formatted_scraped_jobs = []
            for job in scraped_jobs:
                # Skip jobs that don't have required fields
                if not job.get('title') or not job.get('company'):
                    continue
                    
                # Format job
                formatted_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'description': job.get('description', ''),
                    'url': job.get('url', ''),
                    'source': job.get('source', ''),
                    'sourceId': job.get('sourceId', f"{job.get('source', 'unknown')}_{job.get('title', 'unknown')}_{time.time()}"),
                    'skills': job.get('skills', []),
                    'postedAt': job.get('postedAt', datetime.now()),
                    'scrapedAt': datetime.now()
                }
                formatted_scraped_jobs.append(formatted_job)
            
            # Save scraped jobs to database
            if formatted_scraped_jobs:
                try:
                    from app.models.job_matcher import connect_to_mongodb
                    db = connect_to_mongodb()
                    if db:
                        jobs_collection = db['jobs']
                        for job in formatted_scraped_jobs:
                            # Create upsert query to avoid duplicates
                            filter_query = {'source': job['source'], 'sourceId': job['sourceId']}
                            jobs_collection.update_one(filter_query, {'$set': job}, upsert=True)
                        print(f"Saved {len(formatted_scraped_jobs)} jobs to database")
                except Exception as e:
                    print(f"Error saving jobs to database: {e}")
            
            # Merge database jobs with scraped jobs
            combined_jobs = db_jobs + formatted_scraped_jobs
        else:
            combined_jobs = db_jobs
        
        # Format jobs for response
        formatted_jobs = []
        for job in combined_jobs:
            # Calculate match score for each job
            match_score = calculate_match_score(job.get('skills', []), skills)
            
            # Convert datetime objects to strings
            posted_at = job.get('postedAt')
            scraped_at = job.get('scrapedAt')
            
            # Generate a job ID if needed
            job_id = job.get('id') or job.get('_id') or job.get('sourceId') or f"{job.get('source', 'unknown')}_{int(time.time())}"
            
            formatted_job = {
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'description': job.get('description', ''),
                'url': job.get('url', ''),
                'source': job.get('source', ''),
                'skills': job.get('skills', []),
                'postedAt': posted_at.isoformat() if isinstance(posted_at, datetime) else posted_at,
                'scrapedAt': scraped_at.isoformat() if isinstance(scraped_at, datetime) else scraped_at,
                'matchScore': match_score
            }
            formatted_jobs.append(formatted_job)
        
        # Sort by match score
        formatted_jobs.sort(key=lambda x: x['matchScore'], reverse=True)
        
        # Limit the number of jobs returned
        formatted_jobs = formatted_jobs[:limit]
        
        print(f"Returning {len(formatted_jobs)} matched jobs")
        return jsonify({"jobs": formatted_jobs, "success": True})
        
    except Exception as e:
        import traceback
        print(f"Error in job_match: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "success": False}), 500

def calculate_match_score(job_skills, user_skills):
    """Calculate how well user skills match job skills"""
    if not job_skills or not user_skills:
        return 0.0
        
    # Normalize both skill sets to lowercase
    job_skills_lower = [skill.lower() for skill in job_skills]
    user_skills_lower = [skill.lower() for skill in user_skills]
    
    # Find matching skills
    matching_skills = set(job_skills_lower) & set(user_skills_lower)
    
    # Calculate score based on matching skills relative to both job skills and user skills
    job_skill_ratio = len(matching_skills) / len(job_skills) if job_skills else 0
    user_skill_ratio = len(matching_skills) / len(user_skills) if user_skills else 0
    
    # Use a weighted average - job skills match is more important
    match_score = (job_skill_ratio * 0.7) + (user_skill_ratio * 0.3)
    
    return round(match_score, 2)  # Return as a decimal between 0 and 1       
# def calculate_match_score(job_skills, user_skills):
#     """Calculate how well user skills match job skills"""
#     if not job_skills or not user_skills:
#         return 0.0
        
#     # Normalize both skill sets to lowercase
#     job_skills_lower = [skill.lower() for skill in job_skills]
#     user_skills_lower = [skill.lower() for skill in user_skills]
    
#     # Find matching skills
#     matching_skills = set(job_skills_lower) & set(user_skills_lower)
    
#     # Calculate score based on matches relative to job requirements
#     if len(job_skills) > 0:
#         return round(len(matching_skills) / len(job_skills), 2)
#     return 0.0