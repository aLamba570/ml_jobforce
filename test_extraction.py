import requests
import json

# Base URL for the ML service API
BASE_URL = "http://localhost:5000/api"

def test_extract_skills_from_text():
    """Test skill extraction from resume text"""
    
    # Sample resume text
    sample_resume = """
    John Doe
    Software Engineer

    Professional Experience:
    - Developed web applications using React, Node.js, and MongoDB
    - Implemented RESTful APIs using Express.js
    - Deployed applications on AWS EC2 and S3
    - Used Docker for containerization
    - Familiar with CI/CD pipelines using GitHub Actions
    - Proficient in Python, JavaScript, and SQL
    
    Education:
    - Bachelor of Science in Computer Science
    
    Skills:
    - Strong communication and leadership abilities
    - Problem-solving and critical thinking
    - Time management and teamwork
    """
    
    # Send request to the API
    response = requests.post(
        f"{BASE_URL}/extract-skills",
        json={"text": sample_resume}
    )
    
    # Check if request was successful
    if response.status_code == 200:
        skills = response.json().get("skills", [])
        print(f"Successfully extracted {len(skills)} skills:")
        for skill in skills:
            print(f"- {skill}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_job_matching():
    """Test job matching with extracted skills"""
    
    # Sample skills
    sample_skills = [
        "python", "javascript", "react", "node.js", 
        "mongodb", "express", "aws", "docker"
    ]
    
    # Send request to the API
    response = requests.post(
        f"{BASE_URL}/match-jobs",
        json={"skills": sample_skills, "limit": 5}
    )
    
    # Check if request was successful
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        print(f"\nFound {len(matches)} job matches:")
        for i, job in enumerate(matches, 1):
            print(f"\n{i}. {job['title']} at {job['company']}")
            print(f"   Match score: {job['match_score']}%")
            print(f"   Matching skills: {', '.join(job['matching_skills'])}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def test_job_similarity():
    """Test similarity calculation between resume and job description"""
    
    # Sample resume text
    sample_resume = """
    Experienced software engineer with 5 years of experience in web development.
    Proficient in JavaScript, React, Node.js, and MongoDB.
    Experienced with AWS services including EC2, S3, and Lambda.
    Strong problem-solving skills and ability to work in a team environment.
    """
    
    # Sample job description
    sample_job = """
    We're looking for a Full Stack Developer with strong JavaScript skills.
    Required skills include React, Node.js, and experience with NoSQL databases like MongoDB.
    Experience with cloud platforms like AWS is a plus.
    Must have good communication skills and ability to work in a team.
    """
    
    # Send request to the API
    response = requests.post(
        f"{BASE_URL}/calculate-similarity",
        json={
            "resume_text": sample_resume,
            "job_description": sample_job
        }
    )
    
    # Check if request was successful
    if response.status_code == 200:
        similarity = response.json().get("similarity_score")
        print(f"\nSimilarity score: {similarity}%")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("===== Testing ML Service API =====")
    
    # Run tests
    extract_success = test_extract_skills_from_text()
    match_success = test_job_matching()
    similarity_success = test_job_similarity()
    
    # Print overall results
    print("\n===== Test Results =====")
    print(f"Skill Extraction: {'✅ PASSED' if extract_success else '❌ FAILED'}")
    print(f"Job Matching: {'✅ PASSED' if match_success else '❌ FAILED'}")
    print(f"Job Similarity: {'✅ PASSED' if similarity_success else '❌ FAILED'}")