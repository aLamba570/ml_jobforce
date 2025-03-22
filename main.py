from flask import Flask, jsonify
from flask_cors import CORS
import os
import nltk
import spacy
import logging

from app.api.routes import api_bp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Download necessary NLTK data
logger.info("Downloading NLTK data...")
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load spaCy model
logger.info("Loading spaCy model...")
try:
    nlp = spacy.load("en_core_web_md")
    logger.info("spaCy model loaded successfully")
except Exception as e:
    logger.error(f"Error loading spaCy model: {str(e)}")
    # If model isn't installed, download it
    logger.info("Attempting to download spaCy model...")
    os.system("python -m spacy download en_core_web_md")
    nlp = spacy.load("en_core_web_md")

def create_app():
    logger.info("Creating Flask application...")
    app = Flask(__name__)
    
    # Configure app
    try:
        app.config.from_pyfile('app/utils/config.py')
        logger.info("Loaded configuration")
    except Exception as e:
        logger.warning(f"Could not load config file: {str(e)}")
    
    # Enable CORS
    CORS(app)
    logger.info("Enabled CORS")
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    logger.info("Registered API blueprint with prefix /api")
    
    # Add a root route for health check and API information
    @app.route('/', methods=['GET'])
    def home():
        logger.debug("Home route accessed")
        return jsonify({
            'status': 'online',
            'service': 'Job Recommendation ML Service',
            'endpoints': {
                '/api/extract-skills': 'Extract skills from resume text or file',
                '/api/match-jobs': 'Match jobs to extracted skills',
                '/api/calculate-similarity': 'Calculate similarity between resume and job'
            }
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        logger.debug("Health check route accessed")
        return jsonify({'status': 'healthy'}), 200
    
    logger.info("Flask application created successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Flask application on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)