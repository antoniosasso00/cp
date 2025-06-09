import requests
import json

print("🚀 TEST ENDPOINT MULTI-BATCH")

# Test con 3 ODL
data = {
    "odl_ids": ["1", "2", "3"],
    "parametri": {
        "padding_mm": 1,
        "min_distance_mm": 1
    }
}

try:
    response = requests.post('http://localhost:8000/api/batch_nesting/genera-multi', json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS: {result.get('success_count', 0)} batch generati")
        print(f"Best batch: {result.get('best_batch_id', 'N/A')}")
        
        # Dettagli batch
        if 'batch_results' in result:
            print("\n📊 BATCH GENERATI:")
            for i, batch in enumerate(result['batch_results']):
                autoclave = batch.get('autoclave_nome', 'N/A')
                efficiency = batch.get('efficiency', 0)
                success = batch.get('success', False)
                batch_id = batch.get('batch_id', 'N/A')
                print(f"  {i+1}. {autoclave}: {efficiency:.1f}% - {'✅' if success else '❌'} - ID: {batch_id}")
    else:
        print(f"❌ ERRORE: {response.text}")

except Exception as e:
    print(f"❌ EXCEPTION: {e}") 