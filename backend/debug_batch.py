import requests
import json
from datetime import datetime

print("🔍 DEBUG BATCH NESTING")
print("=" * 50)

try:
    # 1. Lista batch recenti
    print("📋 BATCH RECENTI:")
    response = requests.get('http://localhost:8000/api/batch_nesting?limit=10')
    if response.status_code == 200:
        batches = response.json()
        print(f"Trovati {len(batches)} batch:")
        
        for i, batch in enumerate(batches[:5]):
            created = batch.get('created_at', 'N/A')
            autoclave_id = batch.get('autoclave_id', 'N/A')
            print(f"  {i+1}. ID: {batch['id'][:8]}... | Autoclave: {autoclave_id} | Created: {created}")
    else:
        print(f"❌ Errore: {response.status_code}")
    
    print("\n" + "=" * 50)
    
    # 2. Test endpoint genera-multi per vedere se funziona
    print("🚀 TEST GENERA-MULTI:")
    data = {
        "odl_ids": ["1", "2", "3", "4", "5"],
        "parametri": {
            "padding_mm": 1,
            "min_distance_mm": 1
        }
    }
    
    response = requests.post('http://localhost:8000/api/batch_nesting/genera-multi', json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS: {result.get('success_count', 0)} batch generati")
        print(f"Best batch: {result.get('best_batch_id', 'N/A')}")
        
        if 'batch_results' in result:
            print("📊 BATCH GENERATI:")
            for i, batch in enumerate(result['batch_results']):
                autoclave = batch.get('autoclave_nome', 'N/A')
                efficienza = batch.get('efficiency', 0)
                success = batch.get('success', False)
                print(f"  {i+1}. {autoclave}: {efficienza:.1f}% - {'✅' if success else '❌'}")
    else:
        print(f"❌ ERRORE: {response.text}")

except Exception as e:
    print(f"❌ ERRORE: {e}") 