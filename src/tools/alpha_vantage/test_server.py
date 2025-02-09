import requests
import json
import time

def test_api():
    """Test the Alpha Vantage API key generation server"""
    base_url = "http://localhost:7785"
    
    # Test health check
    print("\nTesting health check endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test token generation
    print("\nTesting token generation endpoint...")
    try:
        response = requests.get(f"{base_url}/api/token")
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get('success'):
            api_key = response.json()['api_key']
            print(f"\nSuccessfully generated API key: {api_key}")
            
            # Test the API key with a simple Alpha Vantage request
            print("\nTesting the generated API key...")
            test_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey={api_key}"
            test_response = requests.get(test_url)
            if test_response.status_code == 200:
                print("API key works! Successfully made a request to Alpha Vantage")
            else:
                print(f"API key test failed with status code: {test_response.status_code}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test rate limiting by making multiple requests
    print("\nTesting rate limiting...")
    for i in range(3):
        try:
            print(f"\nRequest {i+1}:")
            response = requests.get(f"{base_url}/api/token")
            print(f"Status code: {response.status_code}")
            if response.status_code == 200:
                print(f"Generated API key: {response.json().get('api_key')}")
            else:
                print(f"Error: {response.json().get('error')}")
            
            # Wait between requests
            if i < 2:  # Don't wait after the last request
                print("Waiting 5 seconds...")
                time.sleep(5)
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_api() 