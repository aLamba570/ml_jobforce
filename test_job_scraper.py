import sys
import os

# Add parent directory to Python path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.job_scraper import scrape_all_jobs  # Corrected import

def test_job_scraper():
    """Test the job scraper functionality"""
    
    print("Starting job scraper test...")
    
    try:
        # Scrape jobs with a limit
        jobs = scrape_all_jobs()  # Updated function call
        
        # Print results
        print(f"Successfully scraped {len(jobs)} jobs:")
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.get('title')} at {job.get('company')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Skills: {', '.join(job.get('skills', []))}")
            print(f"   Source: {job.get('source')}")
        
        return True
    except Exception as e:
        print(f"Error testing job scraper: {str(e)}")
        return False

if __name__ == "__main__":
    print("===== Testing Job Scraper =====")
    
    success = test_job_scraper()
    
    # Print result
    print("\n===== Test Result =====")
    print(f"Job Scraper: {'✅ PASSED' if success else '❌ FAILED'}")