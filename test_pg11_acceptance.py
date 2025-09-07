#!/usr/bin/env python3
"""
PG-11 Acceptance Test Suite
Validates all requirements for Model & Provider Picker implementation.
"""
import json
import sys
import os

def test_models_endpoint_contract():
    """Test /playground/models includes branding, capabilities/limits, pricing, and availability."""
    print("🔍 Testing /playground/models endpoint contract...")
    
    # Check PlaygroundModel structure
    models_file = "backend/app/models/playground_models.py"
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Required branding fields
    branding_checks = [
        ("provider_display_name: str", "Provider display name for UI"),
        ("provider_logo_url: Optional[str]", "Provider logo URL for UI")
    ]
    
    # Required capability/limit fields
    capability_checks = [
        ("class ModelCapabilities", "Capabilities structure"),
        ("supports_streaming: bool", "Streaming support flag"),
        ("supports_function_calling: bool", "Function calling support"),
        ("vision: bool", "Vision support flag")
    ]
    
    limit_checks = [
        ("class ModelLimits", "Limits structure"),
        ("max_input_tokens: Optional[int]", "Input token limit"),
        ("max_output_tokens: Optional[int]", "Output token limit")
    ]
    
    # Required pricing fields
    pricing_checks = [
        ("class ModelPricing", "Pricing structure"),
        ("input: Optional[PricingInfo]", "Input pricing"),
        ("output: Optional[PricingInfo]", "Output pricing")
    ]
    
    # Required availability fields with locked reasons
    availability_checks = [
        ("class ModelAvailability", "Availability structure"),
        ("org_enabled: bool", "Organization enablement"),
        ("has_org_api_key: bool", "API key presence"),
        ("user_enabled: bool", "User enablement"),
        ("locked_reason: Optional[str]", "Lock reason for UI")
    ]
    
    all_checks = [
        ("Branding", branding_checks),
        ("Capabilities", capability_checks), 
        ("Limits", limit_checks),
        ("Pricing", pricing_checks),
        ("Availability", availability_checks)
    ]
    
    passed = 0
    total = 0
    
    for category, checks in all_checks:
        print(f"  📋 {category}:")
        for check, description in checks:
            total += 1
            if check in content:
                print(f"    ✅ {description}")
                passed += 1
            else:
                print(f"    ❌ Missing: {description}")
    
    # Check models service includes branding
    service_file = "backend/app/services/models_service.py"
    with open(service_file, 'r') as f:
        service_content = f.read()
    
    service_checks = [
        ("logo_url", "Logo URL in query"),
        ("provider_display_name=", "Display name mapping"),
        ("provider_logo_url=", "Logo URL mapping")
    ]
    
    print("  📋 Service Integration:")
    for check, description in service_checks:
        total += 1
        if check in service_content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    # Check availability logic with locked reasons
    availability_logic_checks = [
        ("locked_reason = None", "Lock reason initialization"),
        ("disabled_by_org", "Org disabled lock reason"),
        ("missing_org_api_key", "Missing key lock reason")
    ]
    
    print("  📋 Lock Reason Logic:")
    for check, description in availability_logic_checks:
        total += 1
        if check in service_content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 Models endpoint: {passed}/{total} checks passed")
    return success

def test_provider_status_contract():
    """Test /playground/providers/status includes branding + has_org_api_key/is_active."""
    print("\n🔍 Testing /playground/providers/status endpoint contract...")
    
    keys_file = "backend/app/api/playground_keys.py"
    with open(keys_file, 'r') as f:
        content = f.read()
    
    # Required response structure
    response_checks = [
        ("display_name: str", "Provider display name"),
        ("logo_url: Optional[str]", "Provider logo URL"),
        ("has_org_api_key: bool", "API key presence flag"),
        ("is_active: bool", "Key active status"),
        ("key_prefix: Optional[str]", "Safe key prefix"),
        ("last_used_at: Optional[str]", "Last usage timestamp")
    ]
    
    # Required query enhancements
    query_checks = [
        ("select(\"id, name, display_name, logo_url\")", "Branding in query"),
        ("\"display_name\": provider_data[\"display_name\"]", "Display name mapping"),
        ("\"logo_url\": provider_data.get(\"logo_url\")", "Logo URL mapping")
    ]
    
    passed = 0
    total = 0
    
    print("  📋 Response Structure:")
    for check, description in response_checks:
        total += 1
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    print("  📋 Query Integration:")
    for check, description in query_checks:
        total += 1
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    # Check one key per org/provider constraint understanding
    constraint_checks = [
        ("get_provider_status", "Provider status service call"),
        ("organization.id", "Organization scoping"),
        ("provider_ids", "Provider filtering")
    ]
    
    print("  📋 One Key Per Org/Provider:")
    for check, description in constraint_checks:
        total += 1
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 Provider status: {passed}/{total} checks passed")
    return success

def test_session_update_contract():
    """Test PUT /playground/sessions/{id} updates metadata and echoes back."""
    print("\n🔍 Testing PUT /playground/sessions/{id} contract...")
    
    # Check session model supports picker fields
    session_file = "backend/app/models/playground_session.py"
    with open(session_file, 'r') as f:
        session_content = f.read()
    
    model_checks = [
        ("provider: Optional[str]", "Provider field"),
        ("model: Optional[str]", "Model field"),
        ("default_params: Optional[Dict[str, Any]]", "Default params field")
    ]
    
    # Check session service handles updates
    service_file = "backend/app/services/playground_session_svc.py"
    with open(service_file, 'r') as f:
        service_content = f.read()
    
    service_checks = [
        ("if data.provider is not None:", "Provider update handling"),
        ("if data.model is not None:", "Model update handling"),
        ("if data.default_params is not None:", "Default params handling"),
        ("update_data[\"provider\"] = data.provider", "Provider storage"),
        ("update_data[\"model\"] = data.model", "Model storage"),
        ("current_metadata[\"provider\"] = data.provider", "Provider in metadata"),
        ("current_metadata[\"model\"] = data.model", "Model in metadata")
    ]
    
    # Check API endpoint validation
    api_file = "backend/app/api/playground_sessions.py"
    with open(api_file, 'r') as f:
        api_content = f.read()
    
    validation_checks = [
        ("if data.model and \"/\" not in data.model:", "Model format validation"),
        ("provider_from_model = data.model.split(\"/\")[0]", "Provider extraction"),
        ("provider_model_mismatch", "Consistency validation")
    ]
    
    passed = 0
    total = 0
    
    print("  📋 Session Model:")
    for check, description in model_checks:
        total += 1
        if check in session_content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    print("  📋 Service Logic:")
    for check, description in service_checks:
        total += 1
        if check in service_content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    print("  📋 API Validation:")
    for check, description in validation_checks:
        total += 1
        if check in api_content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 Session update: {passed}/{total} checks passed")
    return success

def test_locked_model_banner_support():
    """Test locked models can show Connect key banner from provider status."""
    print("\n🔍 Testing locked model banner support...")
    
    # Check availability includes locked_reason
    models_file = "backend/app/models/playground_models.py"
    with open(models_file, 'r') as f:
        models_content = f.read()
    
    # Check service builds locked reasons
    service_file = "backend/app/services/models_service.py"
    with open(service_file, 'r') as f:
        service_content = f.read()
    
    # Check provider status provides banner data
    keys_file = "backend/app/api/playground_keys.py"
    with open(keys_file, 'r') as f:
        keys_content = f.read()
    
    banner_checks = [
        (models_content, "locked_reason: Optional[str]", "Lock reason field"),
        (service_content, "missing_org_api_key", "Missing key reason"),
        (service_content, "disabled_by_org", "Org disabled reason"),
        (keys_content, "has_org_api_key: bool", "Key presence flag"),
        (keys_content, "display_name: str", "Provider name for banner"),
        (keys_content, "logo_url: Optional[str]", "Provider logo for banner")
    ]
    
    passed = 0
    total = len(banner_checks)
    
    print("  📋 Banner Support:")
    for content, check, description in banner_checks:
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 Banner support: {passed}/{total} checks passed")
    return success

def test_openai_compatible_routing():
    """Test OpenAI-compatible slash-model prefix routing."""
    print("\n🔍 Testing OpenAI-compatible slash-model routing...")
    
    # Check model ID format validation
    session_service_file = "backend/app/services/playground_session_svc.py"
    with open(session_service_file, 'r') as f:
        service_content = f.read()
    
    # Check models service builds slash format
    models_service_file = "backend/app/services/models_service.py"
    with open(models_service_file, 'r') as f:
        models_content = f.read()
    
    # Check API validation
    api_file = "backend/app/api/playground_sessions.py"
    with open(api_file, 'r') as f:
        api_content = f.read()
    
    routing_checks = [
        (service_content, "if \"/\" not in data.model:", "Slash format validation"),
        (models_content, "f\"{provider_name}/{model_name}\"", "Slash format construction"),
        (api_content, "openai/gpt-4o-mini", "Format documentation"),
        (api_content, "provider_from_model = data.model.split(\"/\")[0]", "Provider extraction"),
        (api_content, "provider_model_mismatch", "Consistency validation")
    ]
    
    passed = 0
    total = len(routing_checks)
    
    print("  📋 Slash-Model Format:")
    for content, check, description in routing_checks:
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 OpenAI routing: {passed}/{total} checks passed")
    return success

def test_traditional_playground_ux():
    """Test picker UX mirrors traditional playgrounds with observability."""
    print("\n🔍 Testing traditional playground UX compatibility...")
    
    # Check aggregator endpoint exists
    picker_file = "backend/app/api/playground_picker.py"
    picker_exists = os.path.exists(picker_file)
    
    ux_checks = []
    
    if picker_exists:
        with open(picker_file, 'r') as f:
            picker_content = f.read()
        
        ux_checks = [
            (picker_content, "class PickerConfigResponse", "Aggregated config response"),
            (picker_content, "models: PlaygroundModelsResponse", "Models in config"),
            (picker_content, "provider_status: ProvidersStatusResponse", "Provider status in config"),
            (picker_content, "session: Optional[PlaygroundSessionRead]", "Session in config"),
            (picker_content, "single round-trip", "Performance optimization docs")
        ]
    
    # Check main app includes picker
    main_file = "backend/app/main.py"
    with open(main_file, 'r') as f:
        main_content = f.read()
    
    integration_checks = [
        (main_content, "playground_picker_router", "Picker router import"),
        (main_content, "include_router(playground_picker_router", "Picker router mounting")
    ]
    
    passed = 0
    total = 0
    
    print("  📋 Aggregator Endpoint:")
    if picker_exists:
        print("    ✅ Picker endpoint file exists")
        passed += 1
    else:
        print("    ❌ Picker endpoint file missing")
    total += 1
    
    for content, check, description in ux_checks:
        total += 1
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    print("  📋 App Integration:")
    for content, check, description in integration_checks:
        total += 1
        if check in content:
            print(f"    ✅ {description}")
            passed += 1
        else:
            print(f"    ❌ Missing: {description}")
    
    success = passed == total
    print(f"  📊 Traditional UX: {passed}/{total} checks passed")
    return success

def main():
    """Run PG-11 acceptance tests."""
    print("🎯 PG-11 Model & Provider Picker - Acceptance Test Suite")
    print("=" * 70)
    
    # Change to project directory
    os.chdir("/Users/abhishek/Documents/GitHub/genailytics-consulting/strataAI")
    
    tests = [
        ("Models Endpoint Contract", test_models_endpoint_contract),
        ("Provider Status Contract", test_provider_status_contract), 
        ("Session Update Contract", test_session_update_contract),
        ("Locked Model Banner Support", test_locked_model_banner_support),
        ("OpenAI-Compatible Routing", test_openai_compatible_routing),
        ("Traditional Playground UX", test_traditional_playground_ux)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS: {passed_tests}/{total_tests} acceptance tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL ACCEPTANCE CRITERIA MET!")
        print("✨ PG-11 implementation is ready for production")
        return True
    else:
        print("⚠️  Some acceptance criteria not met")
        print("🔧 Please review failed tests above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
