#!/usr/bin/env python3
"""
Quick test script to verify authentication and analytics endpoints
"""
import requests
import json

# Test the analytics endpoint with a mock JWT token
def test_analytics_endpoint():
    url = "http://localhost:8000/api/v1/analytics/usage-summary"
    
    # Test without auth
    print("Testing without authentication...")
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()
    
    # Test with invalid auth
    print("Testing with invalid authentication...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

if __name__ == "__main__":
    test_analytics_endpoint()
