import requests
import os
import sys

# Base URL for the ML service API
BASE_URL = "http://localhost:5000/api"

def test_extract_skills_from_file(file_path):
    """Test skill extraction from a resume file"""
    
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return False
    
    file_name = os.path.basename(file_path)
    
    # Prepare file for upload
    with open(file_path, 'rb') as file:
        files = {'file': (file_name, file, 'application/octet-stream')}
        
        # Send request to the API
        response = requests.post(
            f"{BASE_URL}/extract-skills",
            files=files
        )
    
    # Check if request was successful
    if response.status_code == 200:
        skills = response.json().get("skills", [])
        print(f"Successfully extracted {len(skills)} skills from {file_name}:")
        for skill in skills:
            print(f"- {skill}")
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("===== Testing Resume File Processing =====")
    
    # Check if file path is provided
    if len(sys.argv) < 2:
        print("Usage: python test_file_upload.py <path_to_resume_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    success = test_extract_skills_from_file(file_path)
    
    # Print result
    print("\n===== Test Result =====")
    print(f"File Processing: {'✅ PASSED' if success else '❌ FAILED'}")