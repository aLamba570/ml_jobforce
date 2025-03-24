# seed_database.py
from datetime import datetime
import pymongo

# MongoDB connection
MONGO_URI = 'mongodb+srv://alamba570:ankush@cluster0.opvl6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
DB_NAME = 'jobforce'

# Sample jobs with skills matching the test
sample_jobs = [
    {
        "title": "Full Stack Developer",
        "company": "Tech Corp",
        "location": "Remote",
        "description": "Looking for a skilled developer with experience in MERN stack",
        "url": "https://example.com/job1",
        "source": "sample",
        "sourceId": "sample_job_1",
        "skills": ["javascript", "react", "node.js", "mongodb", "express"],
        "postedAt": datetime.now(),
        "scrapedAt": datetime.now()
    },
    {
        "title": "DevOps Engineer",
        "company": "Cloud Inc",
        "location": "New York",
        "description": "DevOps engineer with AWS and containerization experience",
        "url": "https://example.com/job2",
        "source": "sample",
        "sourceId": "sample_job_2",
        "skills": ["aws", "docker", "python", "ci/cd"],
        "postedAt": datetime.now(),
        "scrapedAt": datetime.now()
    },
    # Add more sample jobs with relevant skills
]

def seed_database():
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        jobs_collection = db['jobs']
        
        # Insert sample jobs
        for job in sample_jobs:
            # Update or insert
            filter_query = {'source': job['source'], 'sourceId': job['sourceId']}
            jobs_collection.update_one(filter_query, {'$set': job}, upsert=True)
        
        # Count jobs after seeding
        job_count = jobs_collection.count_documents({})
        print(f"Database seeded successfully. Total jobs: {job_count}")
        
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_database()