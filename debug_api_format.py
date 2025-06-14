#!/usr/bin/env python3
"""
Debug API Format - Test del formato response dell'endpoint result
"""

import requests
import json

def debug_api_format():
    batch_id = "3812d29b-3450-4b72-b36d-20c1c6e218dd"
    url = f"http://localhost:8000/api/batch_nesting/result/{batch_id}"
    
    print("🔍 DEBUGGING API FORMAT")
    print("=" * 50)
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Keys: {list(data.keys())}")
            
            # Controllo formato atteso
            if 'batch_results' in data:
                print("✅ Formato corretto: ha 'batch_results'")
                print(f"Numero batch_results: {len(data['batch_results'])}")
            else:
                print("❌ Formato sbagliato: manca 'batch_results'")
                print("Struttura attuale:")
                print(json.dumps(data, indent=2)[:500] + "...")
            
            # Controllo contenuto batch per 2L detection
            if isinstance(data, dict) and 'configurazione_json' in data:
                config = data['configurazione_json']
                if config:
                    has_levels = any(tool.get('level') is not None for tool in config.get('tool_positions', []))
                    has_cavalletti = bool(config.get('cavalletti'))
                    print(f"2L Detection: levels={has_levels}, cavalletti={has_cavalletti}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == '__main__':
    debug_api_format() 