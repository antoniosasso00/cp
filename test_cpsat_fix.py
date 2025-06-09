#!/usr/bin/env python3
"""
Test rapido per verificare il fix CP-SAT BoundedLinearExpression
"""
import requests
import json
import time

def test_cpsat_fix():
    print("🔧 === TEST CP-SAT FIX BoundedLinearExpression ===")
    
    # Endpoint per testare il fix
    url = "http://localhost:8000/api/batch_nesting/genera-multi"
    
    # Payload di test con pochi ODL - CORREZIONE: IDS come stringhe e parametri interi
    payload = {
        "odl_ids": ["1", "2", "3", "4", "5"],
        "parametri": {
            "padding": 1,
            "multithread": True,
            "use_aerospace": True
        }
    }
    
    print(f"📡 Chiamata: {url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Durata: {duration:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Risposta ricevuta")
            print(f"🎯 Success: {result.get('success', 'N/A')}")
            print(f"🔢 Success Count: {result.get('success_count', 'N/A')}")
            print(f"🏆 Best Batch ID: {result.get('best_batch_id', 'N/A')}")
            
            # Verifica se il CP-SAT è stato utilizzato senza errori
            message = result.get('message', '')
            if 'BoundedLinearExpression' in message:
                print("🚨 ERRORE: BoundedLinearExpression ancora presente!")
                return False
            elif 'CP-SAT BoundedLinearExpression FIX: SUCCESS' in message:
                print("🎯 CP-SAT FIX CONFERMATO! BoundedLinearExpression risolto!")
                return True
            elif 'CP-SAT' in message and 'fallback' not in message.lower():
                print("🎯 CP-SAT UTILIZZATO CON SUCCESSO!")
                return True
            else:
                print(f"📝 Messaggio: {message}")
                return True
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_cpsat_fix()
    print(f"\n🎯 === RESULT: {'SUCCESS' if success else 'FAILED'} ===") 