from flask import Blueprint, request, jsonify
import json
import os
from app.models.skill_extractor import extract_skills_from_text, extract_skills_from_file
from app.models.job_matcher import match_jobs_to_skills, calculate_job_similarity

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
    """
    try:
        if 'file' in request.files:
            file = request.files['file']
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in ['.pdf', '.docx']:
                return jsonify({"error": "Unsupported file format. Please upload PDF or DOCX."}), 400
                
            skills = extract_skills_from_file(file)
        elif request.is_json and 'text' in request.json:
            skills = extract_skills_from_text(request.json['text'])
        else:
            return jsonify({"error": "No file or text provided"}), 400
            
        return jsonify({"skills": skills})
    except Exception as e:
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