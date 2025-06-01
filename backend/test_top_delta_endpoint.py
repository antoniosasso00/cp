#!/usr/bin/env python3
"""
Script per testare l'endpoint top-delta
"""

import requests
import json

def test_top_delta_endpoint():
    """Testa l'endpoint /api/v1/standard-times/top-delta"""
    
    url = "http://localhost:8000/api/v1/standard-times/top-delta"
    params = {
        "limit": 5,
        "days": 30
    }
    
    try:
        print("🔍 Testando endpoint top-delta...")
        print(f"URL: {url}")
        print(f"Parametri: {params}")
        
        response = requests.get(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Risposta ricevuta con successo!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get("success") and data.get("data"):
                print(f"\n📊 Trovati {len(data['data'])} scostamenti:")
                for item in data["data"]:
                    print(f"  • {item['part_number']} ({item['fase']}): {item['delta_percent']:+.1f}% - {item['colore_delta']}")
            else:
                print("⚠️ Nessun dato trovato")
                
        else:
            print(f"❌ Errore HTTP {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione - verifica che il server sia in esecuzione su localhost:8000")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    test_top_delta_endpoint() 