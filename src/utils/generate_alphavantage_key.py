import requests
import random
import string
import json
import re

def generate_random_email():
    # Generate random username
    username_length = random.randint(6, 12)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
    
    # Add a random year
    year = random.randint(1980, 2000)
    
    # Random email domains
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = random.choice(domains)
    
    return f"{username}+{year}@{domain}"

def get_csrf_token():
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, get the support page to get the CSRF token
    support_url = "https://www.alphavantage.co/support/"
    response = session.get(support_url)
    
    # Extract CSRF token from the cookies
    csrf_token = session.cookies.get('csrftoken')
    
    if not csrf_token:
        print("Failed to get CSRF token")
        return None, None
        
    return session, csrf_token

def extract_api_key(text):
    # Try different patterns that have been observed in responses
    patterns = [
        r'API key: ([A-Z0-9]+)',
        r'Your API key is: ([A-Z0-9]+)',
        r'Your dedicated access key is: ([A-Z0-9]+)',
        r'access key: ([A-Z0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def generate_api_key():
    # Get session and CSRF token
    session, csrf_token = get_csrf_token()
    if not session or not csrf_token:
        return None
    
    url = "https://www.alphavantage.co/create_post/"
    email = generate_random_email()
    
    # Headers with CSRF token
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.alphavantage.co',
        'referer': 'https://www.alphavantage.co/support/',
        'x-requested-with': 'XMLHttpRequest',
        'x-csrftoken': csrf_token
    }
    
    # Form data
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'first_text': 'deprecated',
        'last_text': 'deprecated',
        'occupation_text': 'Investor',
        'organization_text': 'Trading Corp',
        'email_text': email
    }
    
    try:
        # Use the session to make the request
        response = session.post(url, headers=headers, data=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Raw response: {response.text}")
        
        try:
            response_data = response.json()
            print(f"Parsed JSON response: {response_data}")
            
            if 'text' in response_data:
                api_key = extract_api_key(response_data['text'])
                if api_key:
                    print(f"Successfully generated API key: {api_key}")
                    print(f"Email used: {email}")
                    return api_key
                else:
                    print("Could not find API key in response text")
                    return None
            else:
                print("Response doesn't have expected 'text' field")
                print("Response:", response_data)
                return None
                
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract API key directly from HTML response
            api_key = extract_api_key(response.text)
            if api_key:
                print(f"Successfully extracted API key from HTML: {api_key}")
                print(f"Email used: {email}")
                return api_key
            else:
                print("Could not find API key in response")
                return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

if __name__ == "__main__":
    api_key = generate_api_key()