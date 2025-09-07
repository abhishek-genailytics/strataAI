#!/usr/bin/env python3
"""
Test script to verify the playground read endpoints are properly configured.
This tests the route registration and basic structure.
"""

from app.main import app

def test_playground_endpoints_exist():
    """Test that the playground endpoints are registered in the FastAPI app"""
    
    # Get all routes from the app
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method != 'HEAD':  # Skip HEAD methods
                    routes.append(f"{method} {route.path}")
    
    # Check that our playground endpoints are registered
    expected_routes = [
        "GET /v1/playground/sessions/{session_id}",
        "GET /v1/playground/sessions/{session_id}/messages"
    ]
    
    print("Registered routes:")
    for route in sorted(routes):
        if "/v1/playground" in route:
            print(f"  {route}")
    
    # Verify our expected routes exist
    for expected in expected_routes:
        found = any(expected in route for route in routes)
        assert found, f"Expected route not found: {expected}"
        print(f"✅ Found: {expected}")
    
    print("✅ All playground endpoints are properly registered")

if __name__ == "__main__":
    test_playground_endpoints_exist()
    print("🎉 Playground read endpoints test completed successfully!")
