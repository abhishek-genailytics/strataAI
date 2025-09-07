#!/usr/bin/env python3
"""
Test script for PG-16 preset functionality.
Tests preset catalog, parameter validation, and preset application.
"""

import asyncio
import sys
import os
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_preset_catalog():
    """Test the static preset catalog."""
    print("🧪 Testing preset catalog...")
    
    from app.config.presets import PRESETS, STOP_SNIPPETS
    from app.services.param_presets_svc import list_presets, find_preset_by_id
    
    # Test preset catalog structure
    assert len(PRESETS) == 6, f"Expected 6 presets, got {len(PRESETS)}"
    assert len(STOP_SNIPPETS) == 3, f"Expected 3 stop snippets, got {len(STOP_SNIPPETS)}"
    
    # Test preset IDs and structure
    preset_ids = [p.id for p in PRESETS]
    expected_preset_ids = ["precise", "balanced", "creative", "short", "medium", "long"]
    assert preset_ids == expected_preset_ids, f"Preset IDs mismatch: {preset_ids}"
    
    stop_ids = [s.id for s in STOP_SNIPPETS]
    expected_stop_ids = ["stop_triple_hash", "stop_md_rule", "stop_double_nl"]
    assert stop_ids == expected_stop_ids, f"Stop snippet IDs mismatch: {stop_ids}"
    
    # Test service functions
    param_presets, stop_snippets = list_presets()
    assert len(param_presets) == 6
    assert len(stop_snippets) == 3
    
    # Test preset lookup
    creative_preset = find_preset_by_id("creative")
    assert creative_preset is not None
    assert creative_preset.label == "Creative"
    assert creative_preset.params["temperature"] == 0.9
    
    # Test non-existent preset
    missing_preset = find_preset_by_id("nonexistent")
    assert missing_preset is None
    
    print("✅ Preset catalog tests passed")

async def test_model_params_validation():
    """Test ModelParams validation with stop sequences."""
    print("🧪 Testing ModelParams validation...")
    
    from app.models.model_params import ModelParams
    from pydantic import ValidationError
    
    # Test valid stop sequences
    # Single string
    params1 = ModelParams(stop="###")
    assert params1.stop == "###"
    
    # List of strings
    params2 = ModelParams(stop=["###", "---", "\n\n"])
    assert set(params2.stop) == {"###", "---", "\n\n"}  # Order may change due to deduplication
    
    # Test validation errors
    try:
        # Empty string
        ModelParams(stop="")
        assert False, "Should have raised ValidationError for empty string"
    except ValidationError as e:
        assert "stop sequence cannot be empty" in str(e)
    
    try:
        # Too long string
        ModelParams(stop="x" * 65)
        assert False, "Should have raised ValidationError for long string"
    except ValidationError as e:
        assert "stop sequence cannot exceed 64 characters" in str(e)
    
    try:
        # Too many items
        ModelParams(stop=["a", "b", "c", "d", "e"])
        assert False, "Should have raised ValidationError for too many items"
    except ValidationError as e:
        assert "stop sequences cannot exceed 4 items" in str(e)
    
    try:
        # Empty list
        ModelParams(stop=[])
        assert False, "Should have raised ValidationError for empty list"
    except ValidationError as e:
        assert "stop sequences list cannot be empty" in str(e)
    
    # Test deduplication
    params3 = ModelParams(stop=["###", "###", "---"])
    assert len(params3.stop) == 2  # Should deduplicate
    assert "###" in params3.stop
    assert "---" in params3.stop
    
    print("✅ ModelParams validation tests passed")

async def test_parameter_merging():
    """Test parameter merging logic."""
    print("🧪 Testing parameter merging...")
    
    from app.models.model_params import ModelParams
    
    # Test merge_with method
    base_params = ModelParams(temperature=0.5, max_tokens=100)
    override_params = ModelParams(temperature=0.8, top_p=0.9)
    
    merged = base_params.merge_with(override_params)
    assert merged.temperature == 0.8  # Override takes precedence
    assert merged.max_tokens == 100   # Base value preserved
    assert merged.top_p == 0.9        # New value from override
    
    # Test system defaults
    defaults = ModelParams.get_system_defaults()
    assert defaults.temperature == 0.7
    assert defaults.max_tokens == 512
    assert defaults.top_p == 1.0
    assert defaults.stop is None
    
    # Test Anthropic requirements
    anthropic_params = ModelParams(temperature=0.8)
    anthropic_ready = anthropic_params.ensure_anthropic_requirements()
    assert anthropic_ready.max_tokens == 512  # Should add default max_tokens
    
    print("✅ Parameter merging tests passed")

async def test_preset_application():
    """Test preset application logic (without database)."""
    print("🧪 Testing preset application logic...")
    
    from app.config.presets import PRESETS
    from app.models.model_params import ModelParams
    
    # Simulate applying a preset
    creative_preset = next(p for p in PRESETS if p.id == "creative")
    preset_params = ModelParams.from_dict(creative_preset.params)
    
    # Test merging with existing params
    existing_params = ModelParams(max_tokens=256, top_p=0.8)
    merged = existing_params.merge_with(preset_params)
    
    assert merged.temperature == 0.9  # From preset
    assert merged.max_tokens == 256   # Preserved from existing
    assert merged.top_p == 1.0        # From preset (overrides existing)
    
    # Test replace mode (start with system defaults)
    system_defaults = ModelParams.get_system_defaults()
    replaced = system_defaults.merge_with(preset_params)
    
    assert replaced.temperature == 0.9  # From preset
    assert replaced.max_tokens == 512   # From system defaults
    assert replaced.top_p == 1.0        # From preset (overrides system default)
    
    print("✅ Preset application tests passed")

async def test_stop_sequence_handling():
    """Test stop sequence handling in different scenarios."""
    print("🧪 Testing stop sequence handling...")
    
    from app.config.presets import STOP_SNIPPETS
    from app.models.model_params import ModelParams
    
    # Test stop snippet presets
    triple_hash = next(s for s in STOP_SNIPPETS if s.id == "stop_triple_hash")
    assert triple_hash.params["stop"] == "###"
    
    double_nl = next(s for s in STOP_SNIPPETS if s.id == "stop_double_nl")
    assert double_nl.params["stop"] == "\n\n"
    
    # Test applying stop snippet to existing params
    base_params = ModelParams(temperature=0.7, max_tokens=512)
    stop_params = ModelParams.from_dict(triple_hash.params)
    
    merged = base_params.merge_with(stop_params)
    assert merged.stop == "###"
    assert merged.temperature == 0.7  # Preserved
    
    # Test multiple stop sequences
    multi_stop = ModelParams(stop=["###", "---", "\n\n"])
    assert len(multi_stop.stop) == 3
    
    print("✅ Stop sequence handling tests passed")

async def test_app_loading():
    """Test that the app loads successfully with new presets endpoints."""
    print("🧪 Testing app loading...")
    
    try:
        from app.main import app
        
        # Check that the app has the expected routes
        routes = [route.path for route in app.routes]
        
        # Look for preset-related routes
        preset_routes = [r for r in routes if "preset" in r.lower()]
        assert len(preset_routes) > 0, "No preset routes found in app"
        
        print(f"✅ App loaded successfully with {len(preset_routes)} preset routes")
        
    except Exception as e:
        print(f"❌ App loading failed: {e}")
        raise

async def main():
    """Run all tests."""
    print("🚀 Starting PG-16 preset functionality tests...\n")
    
    try:
        await test_preset_catalog()
        await test_model_params_validation()
        await test_parameter_merging()
        await test_preset_application()
        await test_stop_sequence_handling()
        await test_app_loading()
        
        print("\n🎉 All PG-16 preset tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
