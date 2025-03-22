import os

# Application settings
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# API settings
API_PREFIX = '/api'
API_VERSION = 'v1'

# ML Model settings
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
SKILLS_VOCABULARY_FILE = os.path.join(MODEL_DIR, 'skills_vocabulary.json')
JOB_EMBEDDINGS_DIR = os.path.join(MODEL_DIR, 'job_embeddings')

# Resume processing settings
MAX_RESUME_SIZE_MB = 10
ALLOWED_EXTENSIONS = ['.pdf', '.docx']

# NLP settings
SPACY_MODEL = 'en_core_web_md'
SENTENCE_TRANSFORMER_MODEL = 'paraphrase-MiniLM-L6-v2'
FALLBACK_SENTENCE_TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'

# Skills extraction settings
MIN_SKILL_LENGTH = 2
MAX_SKILL_LENGTH = 50
SKILL_CONFIDENCE_THRESHOLD = 0.7

# Job matching settings
DEFAULT_JOB_LIMIT = 10
MIN_SIMILARITY_SCORE = 0.4

# Cross-origin settings
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')