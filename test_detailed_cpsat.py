#!/usr/bin/env python3
"""
Test dettagliato per il fix CP-SAT con output verboso
"""
import requests
import json
import time

def test_detailed_cpsat():
    print("🔧 === TEST DETTAGLIATO CP-SAT FIX ===")
    
    # Endpoint per testare il fix
    url = "http://localhost:8000/api/batch_nesting/genera-multi"
    
    # Payload con meno ODL per semplificare
    payload = {
        "odl_ids": ["1", "2", "3"],
        "parametri": {
            "padding": 1,
            "multithread": False,  # Disabilito multithread per debug
            "use_aerospace": True,
            "verbose": True
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
            timeout=45
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Durata: {duration:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Risposta ricevuta")
            
            # Analisi dettagliata della risposta
            print(f"\n🔍 === ANALISI RISPOSTA ===")
            print(f"🎯 Success: {result.get('success', 'N/A')}")
            print(f"🔢 Success Count: {result.get('success_count', 'N/A')}")
            print(f"🏆 Best Batch ID: {result.get('best_batch_id', 'N/A')}")
            print(f"📝 Message: {result.get('message', 'N/A')}")
            
            # Verifica se ci sono batch generati
            batches = result.get('batches', [])
            print(f"📦 Batch generati: {len(batches)}")
            
            if batches:
                for i, batch in enumerate(batches):
                    print(f"\n📦 Batch {i+1}:")
                    print(f"  • ID: {batch.get('id', 'N/A')}")
                    print(f"  • Autoclave: {batch.get('autoclave_nome', 'N/A')}")
                    print(f"  • Efficienza: {batch.get('efficiency', 'N/A'):.2f}%" if batch.get('efficiency') else "N/A")
                    print(f"  • ODL: {len(batch.get('odl_ids', []))}")
                    print(f"  • Metodo: {batch.get('generation_method', 'N/A')}")
                    
                    # Verifica se è stato usato CP-SAT
                    gen_method = batch.get('generation_method', '')
                    solver_info = batch.get('solver_info', {})
                    
                    if 'cp_sat' in gen_method.lower() or 'aerospace' in gen_method.lower():
                        print(f"  ✅ CP-SAT utilizzato!")
                    
                    if solver_info:
                        print(f"  🔧 Solver Info: {solver_info}")
            
            # Verifica il messaggio per il fix
            message = str(result.get('message', ''))
            if 'BoundedLinearExpression' in message:
                if 'FIX: SUCCESS' in message:
                    print("🎯 CP-SAT FIX CONFERMATO!")
                    return True
                else:
                    print("🚨 ERRORE: BoundedLinearExpression ancora presente!")
                    return False
            else:
                print("📋 Nessun messaggio di errore BoundedLinearExpression")
                return result.get('success', False)
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_detailed_cpsat()
    print(f"\n🎯 === RESULT: {'SUCCESS' if success else 'FAILED'} ===") 