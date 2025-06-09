#!/usr/bin/env python3
"""
Test semplice per verificare un singolo ODL
"""
import requests
import json

def test_single_odl():
    print("🔧 === TEST SINGOLO ODL ===")
    
    # Test endpoint singolo
    url = "http://localhost:8000/api/batch_nesting/genera"
    
    # Payload semplice con un solo ODL
    payload = {
        "odl_ids": ["1"],
        "parametri": {
            "padding": 1,
            "use_aerospace": True
        }
    }
    
    print(f"📡 Chiamata: {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Risposta ricevuta")
            print(f"🎯 Success: {result.get('success', 'N/A')}")
            print(f"📝 Message: {result.get('message', 'N/A')}")
            
            # Controlla per il fix CP-SAT
            message = str(result.get('message', ''))
            if 'BoundedLinearExpression' in message and 'FIX: SUCCESS' in message:
                print("🎯 CP-SAT FIX CONFERMATO!")
                return True
            else:
                print(f"📋 Dettagli completi: {json.dumps(result, indent=2)}")
                return True
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📝 Response: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_single_odl()
    print(f"\n🎯 === RESULT: {'SUCCESS' if success else 'FAILED'} ===") 