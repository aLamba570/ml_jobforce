import json
import os
import sys
import time

def test_skills_vocabulary(file_path):
    """Test that the skills vocabulary file is properly formatted"""
    
    if not os.path.exists(file_path):
        print(f"Error: Skills vocabulary file not found at {file_path}")
        return False
    
    try:
        # Load skills vocabulary
        with open(file_path, 'r') as f:
            skills_data = json.load(f)
        
        # Check structure
        if not isinstance(skills_data, dict):
            print("Error: Skills vocabulary should be a dictionary")
            return False
        
        # Check if it has the expected categories
        expected_keys = ["technical_skills", "soft_skills"]
        missing_keys = [key for key in expected_keys if key not in skills_data]
        
        if missing_keys:
            print(f"Warning: Missing expected categories: {', '.join(missing_keys)}")
        
        # Count skills
        total_skills = sum(len(skills_data[category]) for category in skills_data)
        
        # Print summary
        print(f"Skills vocabulary loaded successfully:")
        for category in skills_data:
            print(f"- {category}: {len(skills_data[category])} skills")
        print(f"Total: {total_skills} skills")
        
        # Sample of skills
        print("\nSample skills:")
        for category in skills_data:
            sample_size = min(5, len(skills_data[category]))
            sample = skills_data[category][:sample_size]
            print(f"{category}: {', '.join(sample)}...")
        
        return True
        
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in skills vocabulary file")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("===== Testing Skills Vocabulary =====")
    
    # Default path or command line argument
    default_path = "data/skills_vocabulary.json"
    file_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    success = test_skills_vocabulary(file_path)
    
    # Print result
    print("\n===== Test Result =====")
    print(f"Skills Vocabulary: {'✅ PASSED' if success else '❌ FAILED'}")