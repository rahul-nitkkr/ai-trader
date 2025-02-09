import os
import random
import string
from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

def generate_random_email():
    """Generate a random email for API key registration"""
    username_length = random.randint(6, 12)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
    year = random.randint(1980, 2000)
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = random.choice(domains)
    return f"{username}+{year}@{domain}"

def generate_api_key():
    """Generate a new Alpha Vantage API key"""
    url = "https://www.alphavantage.co/create_post/"
    email = generate_random_email()
    
    # Get CSRF token first
    session = requests.Session()
    support_url = "https://www.alphavantage.co/support/"
    session.get(support_url)
    csrf_token = session.cookies.get('csrftoken')
    
    if not csrf_token:
        return None, "Failed to get CSRF token"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.alphavantage.co',
        'referer': 'https://www.alphavantage.co/support/',
        'x-requested-with': 'XMLHttpRequest',
        'x-csrftoken': csrf_token
    }
    
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'first_text': 'deprecated',
        'last_text': 'deprecated',
        'occupation_text': 'Investor',
        'organization_text': 'Trading Corp',
        'email_text': email
    }
    
    try:
        response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()
        
        if 'text' in response_data:
            # Try different patterns to extract API key
            patterns = [
                'API key: ',
                'Your API key is: ',
                'Your dedicated access key is: ',
                'access key: '
            ]
            
            for pattern in patterns:
                if pattern in response_data['text']:
                    api_key = response_data['text'].split(pattern)[1].split('.')[0].strip()
                    return api_key, None
            
            return None, "Could not find API key in response"
        else:
            return None, "Invalid response format"
            
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

@app.route('/api/token', methods=['GET'])
def get_token():
    """API endpoint to get a new Alpha Vantage API key"""
    api_key, error = generate_api_key()
    
    if api_key:
        return jsonify({
            'success': True,
            'api_key': api_key,
            'generated_at': datetime.utcnow().isoformat(),
            'message': 'API key generated successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': error,
            'message': 'Failed to generate API key'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7785))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 