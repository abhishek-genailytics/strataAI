#!/usr/bin/env python3
"""
Test JWT token validation with actual browser token
"""
import sys
sys.path.append('/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI/backend')

from jose import jwt, JWTError
from app.core.config import settings

# Test token from browser (you'll need to paste this)
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU2MDkzNzE0LCJpYXQiOjE3NTYwOTAxMTQsImlzcyI6Imh0dHBzOi8vcHVjdnR1cmFnbGx4bWt2bXdvcXYuc3VwYWJhc2UuY28vYXV0aC92MSIsInN1YiI6IjNlNzU5NzJmLTJmMzMtNGJjZC1hNzY1LWY5NzY1YjU5YzY1YyIsImVtYWlsIjoiYWJoaXNoZWtAZ2VuYWlseXRpY3MuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6e30sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTYwOTAxMTR9XSwic2Vzc2lvbl9pZCI6IjNlNzU5NzJmLTJmMzMtNGJjZC1hNzY1LWY5NzY1YjU5YzY1YyIsImlzX2Fub255bW91cyI6ZmFsc2V9"

def test_jwt_validation():
    print(f"JWT Secret (first 20 chars): {settings.SUPABASE_JWT_SECRET[:20]}...")
    print(f"Token (first 50 chars): {test_token[:50]}...")
    
    try:
        # Try to decode the token
        payload = jwt.decode(
            test_token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        print("✅ JWT validation successful!")
        print(f"User ID: {payload.get('sub')}")
        print(f"Email: {payload.get('email')}")
        print(f"Role: {payload.get('role')}")
        return True
        
    except JWTError as e:
        print(f"❌ JWT validation failed: {e}")
        return False

if __name__ == "__main__":
    test_jwt_validation()
