import requests
import json
import os
import time
from bs4 import BeautifulSoup
import concurrent.futures
from datetime import datetime
import random
from app.models.skill_extractor import extract_skills_from_text

# Set up headers for requests to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# Sources to scrape
SOURCES = {
    'remoteok': 'https://remoteok.com/api',
    'we_work_remotely': 'https://weworkremotely.com/remote-jobs.json'
}

# API keys for job APIs (for demonstration, using free tier limits)
API_KEYS = {
    'jooble': os.environ.get('JOOBLE_API_KEY', '62936976-168b-427b-ba84-3514af0f7962'),
    'adzuna': os.environ.get('ADZUNA_API_KEY', 'c9ec64f6690cb1c018793c0c8e6d8c98'),
    'jsearch': os.environ.get('JSEARCH_API_KEY', '4e55afc2a1msh0e03a079e1dd351p143f53jsn08519e111e8b')
}

def scrape_remoteok():
    """Scrape RemoteOK API for jobs"""
    try:
        response = requests.get(SOURCES['remoteok'], headers=HEADERS)
        if response.status_code == 200:
            jobs = response.json()
            
            # RemoteOK returns first item as info, skip it
            if jobs and not isinstance(jobs[0], dict):
                jobs = jobs[1:]
                
            processed_jobs = []
            for job in jobs:
                if isinstance(job, dict):
                    # Extract skills from job description
                    skills_data = extract_skills_from_text(job.get('description', ''))
                    
                    # Safely parse the 'date' field
                    try:
                        date = int(job.get('date', 0))  # Convert to integer
                        posted_at = datetime.fromtimestamp(date)
                    except (ValueError, TypeError):
                        posted_at = None  # Default to None if invalid
                    
                    processed_job = {
                        'title': job.get('position', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', 'Remote'),
                        'description': job.get('description', ''),
                        'url': f"https://remoteok.com/remote-jobs/{job.get('slug', '')}",
                        'source': 'remoteok',
                        'sourceId': job.get('id', ''),
                        'skills': skills_data.get('all_skills', []),
                        'postedAt': posted_at,
                        'scrapedAt': datetime.now()
                    }
                    processed_jobs.append(processed_job)
            
            return processed_jobs
        return []
    except Exception as e:
        print(f"Error scraping RemoteOK: {e}")
        return []

def scrape_weworkremotely():
    """Scrape We Work Remotely API for jobs"""
    try:
        response = requests.get(SOURCES['we_work_remotely'], headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
                
            processed_jobs = []
            for job in jobs:
                # Get full job description
                job_url = f"https://weworkremotely.com/remote-jobs/{job.get('id', '')}"
                job_response = requests.get(job_url, headers=HEADERS)
                
                if job_response.status_code == 200:
                    soup = BeautifulSoup(job_response.text, 'html.parser')
                    description = soup.select_one('.listing-container')
                    description_text = description.get_text() if description else job.get('description', '')
                    
                    # Extract skills from job description
                    skills_data = extract_skills_from_text(description_text)
                    
                    processed_job = {
                        'title': job.get('title', ''),
                        'company': job.get('company_name', ''),
                        'location': job.get('region', 'Remote'),
                        'description': description_text,
                        'url': job_url,
                        'source': 'weworkremotely',
                        'sourceId': str(job.get('id', '')),
                        'skills': skills_data.get('all_skills', []),
                        'postedAt': datetime.strptime(job.get('listed_at', ''), '%Y-%m-%dT%H:%M:%S.%fZ') if job.get('listed_at') else None,
                        'scrapedAt': datetime.now()
                    }
                    processed_jobs.append(processed_job)
                
                # Avoid rate limiting
                time.sleep(random.uniform(1, 3))
            
            return processed_jobs
        return []
    except Exception as e:
        print(f"Error scraping We Work Remotely: {e}")
        return []

def fetch_jooble_jobs(query='developer', location='', page=1):
    """Fetch jobs from Jooble API"""
    if not API_KEYS['jooble']:
        return []
        
    try:
        url = 'https://jooble.org/api/jobs'
        params = {
            'keywords': query,
            'location': location,
            'page': page
        }
        
        response = requests.post(url, json=params, headers={
            'Content-Type': 'application/json',
            'apiKey': API_KEYS['jooble']
        })
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            
            processed_jobs = []
            for job in jobs:
                # Extract skills from job description
                skills_data = extract_skills_from_text(job.get('snippet', ''))
                
                processed_job = {
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'description': job.get('snippet', ''),
                    'url': job.get('link', ''),
                    'source': 'jooble',
                    'sourceId': job.get('id', ''),
                    'skills': skills_data.get('all_skills', []),
                    'postedAt': datetime.strptime(job.get('updated', ''), '%Y-%m-%dT%H:%M:%S.%fZ') if job.get('updated') else None,
                    'scrapedAt': datetime.now()
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        return []
    except Exception as e:
        print(f"Error fetching Jooble jobs: {e}")
        return []

def fetch_jsearch_jobs(query='software engineer', location='', limit=20):
    """Fetch jobs from JSearch API"""
    if not API_KEYS['jsearch']:
        return []
        
    try:
        url = 'https://jsearch.p.rapidapi.com/search'
        params = {
            'query': f"{query} in {location}" if location else query,
            'num_pages': 1,
            'page': 1
        }
        
        response = requests.get(url, 
                                headers={
                                    'X-RapidAPI-Key': API_KEYS['jsearch'],
                                    'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
                                },
                                params=params)
        
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('data', [])
            
            processed_jobs = []
            for job in jobs[:limit]:
                # Extract skills from job description
                skills_data = extract_skills_from_text(job.get('job_description', ''))
                
                processed_job = {
                    'title': job.get('job_title', ''),
                    'company': job.get('employer_name', ''),
                    'location': job.get('job_city', '') + ', ' + job.get('job_country', ''),
                    'description': job.get('job_description', ''),
                    'url': job.get('job_apply_link', ''),
                    'source': 'jsearch',
                    'sourceId': job.get('job_id', ''),
                    'skills': skills_data.get('all_skills', []),
                    'postedAt': datetime.strptime(job.get('job_posted_at_datetime_utc', ''), '%Y-%m-%dT%H:%M:%S.%fZ') if job.get('job_posted_at_datetime_utc') else None,
                    'scrapedAt': datetime.now()
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        return []
    except Exception as e:
        print(f"Error fetching JSearch jobs: {e}")
        return []

def scrape_all_jobs():
    """Scrape jobs from all sources in parallel"""
    all_jobs = []
    
    # Use ThreadPoolExecutor to run scrapers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Start the scrapers
        future_remoteok = executor.submit(scrape_remoteok)
        future_weworkremotely = executor.submit(scrape_weworkremotely)
        future_jooble = executor.submit(fetch_jooble_jobs, 'software developer')
        
        # Collect results
        all_jobs.extend(future_remoteok.result())
        all_jobs.extend(future_weworkremotely.result())
        all_jobs.extend(future_jooble.result())
    
    return all_jobs

def scrape_jobs_by_skills(skills, limit=100):
    """Scrape jobs related to specific skills"""
    all_jobs = []
    
    # Convert skills to comma-separated string for queries
    skill_query = ', '.join(skills[:3])  # Use top 3 skills to avoid query being too long
    
    print(f"Scraping jobs for query: {skill_query}, limit: {limit}")
    
    try:
        # Get jobs from JSearch with increased limit
        jsearch_jobs = fetch_jsearch_jobs(query=skill_query, limit=limit//2)
        print(f"JSearch returned {len(jsearch_jobs)} jobs")
        all_jobs.extend(jsearch_jobs)
    except Exception as e:
        print(f"Error fetching from JSearch: {e}")
    
    try:
        # Get jobs from Jooble with multiple pages
        for page in range(1, 3):  # Fetch from pages 1 and 2
            jooble_jobs = fetch_jooble_jobs(query=skill_query, page=page)
            print(f"Jooble page {page} returned {len(jooble_jobs)} jobs")
            all_jobs.extend(jooble_jobs)
            time.sleep(1)  # Avoid rate limiting
    except Exception as e:
        print(f"Error fetching from Jooble: {e}")
    
    # Add jobs from other sources if available
    try:
        remoteok_jobs = scrape_remoteok()
        print(f"RemoteOK returned {len(remoteok_jobs)} jobs")
        all_jobs.extend(remoteok_jobs)
    except Exception as e:
        print(f"Error fetching from RemoteOK: {e}")
    
    try:
        weworkremotely_jobs = scrape_weworkremotely()
        print(f"WeWorkRemotely returned {len(weworkremotely_jobs)} jobs")
        all_jobs.extend(weworkremotely_jobs)
    except Exception as e:
        print(f"Error fetching from WeWorkRemotely: {e}")
    
    # Extract skills for jobs that don't have them
    from app.models.skill_extractor import extract_skills_from_text
    
    for job in all_jobs:
        if not job.get('skills') and job.get('description'):
            try:
                extracted_skills = extract_skills_from_text(job['description'])
                if isinstance(extracted_skills, dict) and 'all_skills' in extracted_skills:
                    job['skills'] = extracted_skills['all_skills']
                elif isinstance(extracted_skills, list):
                    job['skills'] = extracted_skills
                else:
                    # Default to empty list
                    job['skills'] = []
            except Exception as e:
                print(f"Error extracting skills from job: {e}")
                job['skills'] = []
    
    print(f"Total jobs scraped: {len(all_jobs)}")
    
    # Return all jobs up to the limit
    return all_jobs[:limit]

if __name__ == '__main__':
    # Test scraper
    jobs = scrape_all_jobs()
    print(f"Scraped {len(jobs)} jobs")