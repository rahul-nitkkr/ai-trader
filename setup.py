#!/usr/bin/env python3
import nltk
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_nltk_data():
    """Download required NLTK data."""
    try:
        logger.info("Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon')
        logger.info("NLTK data downloaded successfully.")
    except Exception as e:
        logger.error(f"Error downloading NLTK data: {str(e)}")
        raise

def setup_environment():
    """Set up the environment."""
    try:
        # Create necessary directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('results', exist_ok=True)
        
        # Download NLTK data
        download_nltk_data()
        
        # Check environment file
        if not os.path.exists('.env'):
            logger.warning("No .env file found. Creating from template...")
            if os.path.exists('.env.example'):
                with open('.env.example', 'r') as example, open('.env', 'w') as env:
                    env.write(example.read())
                logger.info("Created .env file from template. Please edit it with your API keys.")
            else:
                logger.error(".env.example not found!")
                raise FileNotFoundError(".env.example not found!")
        
        # Load environment to test
        load_dotenv()
        required_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'FINNHUB_API_KEY',
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Please edit .env file and add the missing API keys.")
        
        logger.info("Setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        raise

if __name__ == "__main__":
    setup_environment() 