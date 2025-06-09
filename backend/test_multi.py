import requests
import json

# Test endpoint multi-batch
url = 'http://localhost:8000/api/batch_nesting/genera-multi'
data = {
    "odl_ids": ["1", "2", "3"],
    "parametri": {
        "padding_mm": 1,
        "min_distance_mm": 1
    }
}

try:
    print("🚀 TEST ENDPOINT MULTI-BATCH")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data)
    print(f"\n✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESSO!")
        print(f"Batch generati: {result.get('total_batches', 'N/A')}")
        print(f"Best batch: {result.get('best_batch_id', 'N/A')}")
        
        if 'batches' in result:
            print("\n📊 RIEPILOGO BATCH:")
            for i, batch in enumerate(result['batches']):
                autoclave = batch.get('autoclave_nome', f"Autoclave {i+1}")
                efficienza = batch.get('efficienza_area', 0)
                print(f"  {i+1}. {autoclave}: {efficienza:.1f}% efficienza")
    else:
        print("❌ ERRORE!")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ ERRORE: {e}") 