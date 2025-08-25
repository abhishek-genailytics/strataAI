#!/usr/bin/env python3
"""
Debug authentication by creating a test JWT token
"""
import jwt
import json
from datetime import datetime, timedelta

# Create a test JWT token that matches Supabase format
def create_test_token():
    payload = {
        "aud": "authenticated",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "https://pucvturagllxmkvmwoqv.supabase.co/auth/v1",
        "sub": "test-user-id",
        "email": "abhishek@genailytics.com",
        "role": "authenticated"
    }
    
    # Use a simple secret for testing (this should match your JWT secret)
    secret = "your_supabase_jwt_secret_here"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

if __name__ == "__main__":
    token = create_test_token()
    print("Test JWT Token:")
    print(token)
    
    # Test the token with the API
    import requests
    url = "http://localhost:8000/api/v1/analytics/usage-summary"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nAPI Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
