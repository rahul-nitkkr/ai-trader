#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging
import webbrowser
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AITrader.Utils')

def update_env_file(api_key: str) -> None:
    """Update the .env file with the Alpha Vantage API key."""
    env_path = Path(__file__).parent.parent.parent / '.env'
    
    if not env_path.exists():
        logger.error(f".env file not found at {env_path}")
        sys.exit(1)
    
    # Update the .env file
    set_key(str(env_path), 'ALPHA_VANTAGE_API_KEY', api_key)
    logger.info("Successfully updated .env file with Alpha Vantage API key")

def main():
    """Main function to help generate and configure Alpha Vantage API key."""
    logger.info("Alpha Vantage API Key Configuration")
    logger.info("-" * 40)
    
    # Check if key already exists
    load_dotenv()
    existing_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if existing_key and existing_key != 'your_alpha_vantage_api_key_here':
        logger.info(f"Found existing Alpha Vantage API key: {existing_key[:5]}...")
        replace = input("Would you like to replace it? (y/N): ").lower()
        if replace != 'y':
            logger.info("Keeping existing API key")
            return
    
    # Open Alpha Vantage website
    logger.info("Opening Alpha Vantage website to get your free API key...")
    webbrowser.open('https://www.alphavantage.co/support/#api-key')
    
    # Get API key from user
    print("\nPlease follow these steps:")
    print("1. Fill out the form on the Alpha Vantage website")
    print("2. Check your email for the API key")
    print("3. Copy and paste your API key below\n")
    
    api_key = input("Enter your Alpha Vantage API key: ").strip()
    
    if not api_key:
        logger.error("No API key provided")
        return
    
    # Update .env file
    update_env_file(api_key)
    
    logger.info("\nSetup Complete!")
    logger.info("You can now use the Alpha Vantage API in your application")
    logger.info("Try running the server again with:")
    logger.info("FLASK_ENV=development python -m src.api.server")
    logger.info("The server will be available at http://localhost:7785")

if __name__ == "__main__":
    main()