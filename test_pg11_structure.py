#!/usr/bin/env python3
"""
Structure validation test for PG-11 Model & Provider Picker implementation.
Tests code structure without requiring database connections.
"""
import sys
import os
import ast
import importlib.util

def test_model_structure():
    """Test PlaygroundModel has required branding fields."""
    try:
        # Read and parse the models file
        models_file = "backend/app/models/playground_models.py"
        with open(models_file, 'r') as f:
            content = f.read()
        
        # Check for required fields in PlaygroundModel
        required_fields = [
            "provider_display_name: str",
            "provider_logo_url: Optional[str]"
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✅ PlaygroundModel has field: {field}")
            else:
                print(f"❌ PlaygroundModel missing field: {field}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate PlaygroundModel: {e}")
        return False

def test_provider_status_structure():
    """Test ProviderStatusResponse has required branding fields."""
    try:
        # Read and parse the keys file
        keys_file = "backend/app/api/playground_keys.py"
        with open(keys_file, 'r') as f:
            content = f.read()
        
        # Check for required fields in ProviderStatusResponse
        required_fields = [
            "display_name: str",
            "logo_url: Optional[str]"
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✅ ProviderStatusResponse has field: {field}")
            else:
                print(f"❌ ProviderStatusResponse missing field: {field}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate ProviderStatusResponse: {e}")
        return False

def test_session_update_structure():
    """Test PlaygroundSessionUpdate has picker fields."""
    try:
        # Read and parse the session models file
        session_file = "backend/app/models/playground_session.py"
        with open(session_file, 'r') as f:
            content = f.read()
        
        # Check for required fields in PlaygroundSessionUpdate
        required_fields = [
            "provider: Optional[str]",
            "model: Optional[str]", 
            "default_params: Optional[Dict[str, Any]]"
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✅ PlaygroundSessionUpdate has field: {field}")
            else:
                print(f"❌ PlaygroundSessionUpdate missing field: {field}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate PlaygroundSessionUpdate: {e}")
        return False

def test_picker_endpoint_exists():
    """Test that picker aggregator endpoint file exists."""
    try:
        picker_file = "backend/app/api/playground_picker.py"
        if os.path.exists(picker_file):
            print("✅ Picker aggregator endpoint file exists")
            
            # Check for key components
            with open(picker_file, 'r') as f:
                content = f.read()
            
            required_components = [
                "class PickerConfigResponse",
                "async def get_picker_config",
                "models: PlaygroundModelsResponse",
                "provider_status: ProvidersStatusResponse"
            ]
            
            for component in required_components:
                if component in content:
                    print(f"✅ Picker endpoint has: {component}")
                else:
                    print(f"❌ Picker endpoint missing: {component}")
                    return False
            
            return True
        else:
            print("❌ Picker aggregator endpoint file does not exist")
            return False
        
    except Exception as e:
        print(f"❌ Failed to validate picker endpoint: {e}")
        return False

def test_main_app_imports():
    """Test that main.py imports the picker router."""
    try:
        main_file = "backend/app/main.py"
        with open(main_file, 'r') as f:
            content = f.read()
        
        required_imports = [
            "from app.api.playground_picker import router as playground_picker_router",
            "app.include_router(playground_picker_router"
        ]
        
        for import_line in required_imports:
            if import_line in content:
                print(f"✅ Main app has: {import_line}")
            else:
                print(f"❌ Main app missing: {import_line}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate main app imports: {e}")
        return False

def test_models_service_branding():
    """Test that models service includes provider branding."""
    try:
        service_file = "backend/app/services/models_service.py"
        with open(service_file, 'r') as f:
            content = f.read()
        
        required_components = [
            "logo_url",
            "provider_display_name=model_data[\"ai_providers\"][\"display_name\"]",
            "provider_logo_url=model_data[\"ai_providers\"].get(\"logo_url\")"
        ]
        
        for component in required_components:
            if component in content:
                print(f"✅ Models service has: {component}")
            else:
                print(f"❌ Models service missing: {component}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate models service: {e}")
        return False

def main():
    """Run all structure validation tests."""
    print("🧪 Testing PG-11 Structure Implementation")
    print("=" * 60)
    
    # Change to project directory
    os.chdir("/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI")
    
    tests = [
        test_model_structure,
        test_provider_status_structure,
        test_session_update_structure,
        test_picker_endpoint_exists,
        test_main_app_imports,
        test_models_service_branding
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            print(f"\n🔍 Running {test.__name__}...")
            if test():
                passed += 1
                print(f"✅ {test.__name__} passed")
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All structure tests passed! PG-11 implementation is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
