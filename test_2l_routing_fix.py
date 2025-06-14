#!/usr/bin/env python3
"""
Test script to verify 2L routing fix
Checks that when 2L autoclaves are used, tools are positioned on both levels
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:3000"

def test_backend_2l_endpoints():
    """Test that backend 2L endpoints are available"""
    print("🔍 Testing backend 2L endpoints...")
    
    # Test /2l-multi endpoint exists
    try:
        response = requests.post(f"{BACKEND_URL}/batch_nesting/2l-multi", 
                               json={"test": "availability"}, 
                               timeout=5)
        if response.status_code in [400, 422]:  # Bad request but endpoint exists
            print("✅ Backend /2l-multi endpoint is available")
            return True
        else:
            print(f"⚠️ Backend /2l-multi returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend /2l-multi endpoint error: {e}")
        return False

def test_frontend_api_route():
    """Test that frontend API route for 2L is available"""
    print("🔍 Testing frontend API route...")
    
    try:
        response = requests.post(f"{FRONTEND_URL}/api/batch_nesting/2l-multi", 
                               json={"test": "availability"}, 
                               timeout=5)
        if response.status_code in [400, 422, 500]:  # Route exists but request invalid
            print("✅ Frontend API route /api/batch_nesting/2l-multi is available")
            return True
        else:
            print(f"⚠️ Frontend API route returned status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend API route error: {e}")
        return False

def test_autoclaves_2l_capability():
    """Test that autoclaves with 2L capability exist"""
    print("🔍 Testing autoclaves 2L capability...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/autoclavi", timeout=10)
        if response.status_code == 200:
            autoclavi = response.json()
            cavalletti_autoclavi = [
                a for a in autoclavi 
                if a.get('usa_cavalletti') or str(a.get('usa_cavalletti')).lower() == 'true'
            ]
            
            print(f"📊 Found {len(autoclavi)} autoclavi total")
            print(f"📊 Found {len(cavalletti_autoclavi)} autoclavi with cavalletti support")
            
            if cavalletti_autoclavi:
                print("✅ 2L-capable autoclavi found:")
                for autoclave in cavalletti_autoclavi:
                    print(f"   - {autoclave['nome']} (ID: {autoclave['id']}) - cavalletti: {autoclave.get('usa_cavalletti')}")
                return True, cavalletti_autoclavi
            else:
                print("❌ No 2L-capable autoclavi found")
                return False, []
        else:
            print(f"❌ Failed to get autoclavi: {response.status_code}")
            return False, []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting autoclavi: {e}")
        return False, []

def test_odl_availability():
    """Test that ODL in 'Attesa Cura' state exist"""
    print("🔍 Testing ODL availability...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/odl", timeout=10)
        if response.status_code == 200:
            odl_list = response.json()
            attesa_cura_odl = [
                odl for odl in odl_list 
                if odl.get('status') == 'Attesa Cura'
            ]
            
            print(f"📊 Found {len(odl_list)} ODL total")
            print(f"📊 Found {len(attesa_cura_odl)} ODL in 'Attesa Cura' state")
            
            if attesa_cura_odl:
                print("✅ ODL ready for nesting found:")
                for odl in attesa_cura_odl[:3]:  # Show first 3
                    print(f"   - ODL {odl['numero_odl']} (ID: {odl['id']}) - {odl['parte']['part_number']}")
                return True, attesa_cura_odl
            else:
                print("❌ No ODL in 'Attesa Cura' state found")
                return False, []
        else:
            print(f"❌ Failed to get ODL: {response.status_code}")
            return False, []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting ODL: {e}")
        return False, []

def test_2l_generation_endpoint():
    """Test actual 2L generation with sample data"""
    print("🔍 Testing 2L generation endpoint...")
    
    # Get 2L autoclavi and ODL
    has_autoclavi, autoclavi_2l = test_autoclaves_2l_capability()
    has_odl, odl_attesa = test_odl_availability()
    
    if not has_autoclavi or not has_odl:
        print("❌ Cannot test 2L generation: missing autoclavi or ODL")
        return False
    
    # Prepare test request
    test_request = {
        "autoclavi_2l": [autoclavi_2l[0]['id']],  # Use first 2L autoclave
        "odl_ids": [odl_attesa[0]['id']],         # Use first available ODL
        "parametri": {
            "padding_mm": 5.0,
            "min_distance_mm": 10.0
        },
        "use_cavalletti": True,
        "cavalletto_height_mm": 100.0,
        "max_weight_per_level_kg": 200.0,
        "prefer_base_level": True
    }
    
    print(f"📡 Testing 2L generation with autoclave {autoclavi_2l[0]['nome']} and ODL {odl_attesa[0]['numero_odl']}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/batch_nesting/2l-multi", 
                               json=test_request, 
                               timeout=60)  # Allow 60s for generation
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 2L generation successful!")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Batch count: {len(result.get('batch_results', []))}")
            
            # Check for 2L specific data
            if result.get('batch_results'):
                batch = result['batch_results'][0]
                level_0_count = batch.get('level_0_count', 0)
                level_1_count = batch.get('level_1_count', 0)
                cavalletti_count = batch.get('cavalletti_count', 0)
                
                print(f"   Level 0 tools: {level_0_count}")
                print(f"   Level 1 tools: {level_1_count}")
                print(f"   Cavalletti: {cavalletti_count}")
                
                if level_1_count > 0 or cavalletti_count > 0:
                    print("🎯 SUCCESS: 2L positioning is working! Tools positioned on multiple levels.")
                    return True
                else:
                    print("⚠️ WARNING: Only level 0 positioning found. 2L algorithm may not be engaging.")
                    return False
            else:
                print("⚠️ WARNING: No batch results returned")
                return False
        else:
            print(f"❌ 2L generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing 2L generation: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing 2L Routing Fix")
    print("=" * 50)
    
    tests = [
        ("Backend 2L endpoints", test_backend_2l_endpoints),
        ("Frontend API route", test_frontend_api_route),
        ("Autoclavi 2L capability", lambda: test_autoclaves_2l_capability()[0]),
        ("ODL availability", lambda: test_odl_availability()[0]),
        ("2L generation", test_2l_generation_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! 2L routing fix is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 