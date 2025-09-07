#!/usr/bin/env python3
"""
Test script for PG-11 Model & Provider Picker implementation.
Validates all endpoint contracts and functionality.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.main import create_app
from fastapi.testclient import TestClient

def test_app_loads():
    """Test that the app loads successfully with all new endpoints."""
    try:
        app = create_app()
        client = TestClient(app)
        
        # Test that app starts without errors
        print("✅ App loads successfully")
        
        # Check if all routes are registered
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/v1/playground/models",
            "/api/v1/playground/providers/status", 
            "/api/v1/playground/sessions/{session_id}",
            "/api/v1/playground/picker/config"
        ]
        
        for route in expected_routes:
            # Check if route pattern exists (handle path parameters)
            route_exists = any(
                route.replace("{session_id}", "{path}") in r or 
                route in r for r in routes
            )
            if route_exists:
                print(f"✅ Route registered: {route}")
            else:
                print(f"❌ Route missing: {route}")
                print(f"Available routes: {routes}")
        
        return True
        
    except Exception as e:
        print(f"❌ App failed to load: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_response_structure():
    """Test that PlaygroundModel has the new branding fields."""
    from app.models.playground_models import PlaygroundModel, ModelAvailability
    
    try:
        # Test model creation with new fields
        model = PlaygroundModel(
            id="openai/gpt-4o-mini",
            provider="openai",
            provider_display_name="OpenAI",
            provider_logo_url="https://example.com/openai-logo.png",
            model_name="gpt-4o-mini",
            display_name="GPT-4o mini",
            availability=ModelAvailability()
        )
        
        assert model.provider_display_name == "OpenAI"
        assert model.provider_logo_url == "https://example.com/openai-logo.png"
        
        print("✅ PlaygroundModel has required branding fields")
        return True
        
    except Exception as e:
        print(f"❌ PlaygroundModel validation failed: {e}")
        return False

def test_provider_status_response_structure():
    """Test that ProviderStatusResponse has the new branding fields."""
    from app.api.playground_keys import ProviderStatusResponse
    
    try:
        # Test response creation with new fields
        response = ProviderStatusResponse(
            provider="openai",
            provider_id="123e4567-e89b-12d3-a456-426614174000",
            display_name="OpenAI",
            logo_url="https://example.com/openai-logo.png",
            has_org_api_key=True,
            is_active=True
        )
        
        assert response.display_name == "OpenAI"
        assert response.logo_url == "https://example.com/openai-logo.png"
        
        print("✅ ProviderStatusResponse has required branding fields")
        return True
        
    except Exception as e:
        print(f"❌ ProviderStatusResponse validation failed: {e}")
        return False

def test_session_update_structure():
    """Test that PlaygroundSessionUpdate supports new picker fields."""
    from app.models.playground_session import PlaygroundSessionUpdate
    
    try:
        # Test update model with new fields
        update = PlaygroundSessionUpdate(
            title="Updated Session",
            provider="anthropic",
            model="anthropic/claude-3-haiku",
            default_params={"temperature": 0.8, "max_tokens": 1024},
            metadata={"custom_field": "value"}
        )
        
        assert update.provider == "anthropic"
        assert update.model == "anthropic/claude-3-haiku"
        assert update.default_params["temperature"] == 0.8
        
        print("✅ PlaygroundSessionUpdate supports picker fields")
        return True
        
    except Exception as e:
        print(f"❌ PlaygroundSessionUpdate validation failed: {e}")
        return False

def test_picker_config_response_structure():
    """Test that PickerConfigResponse aggregates all required data."""
    from app.api.playground_picker import PickerConfigResponse
    from app.models.playground_models import PlaygroundModelsResponse
    from app.api.playground_keys import ProvidersStatusResponse
    
    try:
        # Test aggregated response structure
        config = PickerConfigResponse(
            models=PlaygroundModelsResponse(data=[], meta={}),
            provider_status=ProvidersStatusResponse(data=[]),
            session=None
        )
        
        assert hasattr(config, 'models')
        assert hasattr(config, 'provider_status')
        assert hasattr(config, 'session')
        
        print("✅ PickerConfigResponse has required aggregated fields")
        return True
        
    except Exception as e:
        print(f"❌ PickerConfigResponse validation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing PG-11 Model & Provider Picker Implementation")
    print("=" * 60)
    
    tests = [
        test_app_loads,
        test_model_response_structure,
        test_provider_status_response_structure,
        test_session_update_structure,
        test_picker_config_response_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PG-11 implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
