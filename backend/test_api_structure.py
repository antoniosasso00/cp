#!/usr/bin/env python3
"""
Test dell'API per verificare la struttura dati del batch nesting
"""
import requests
import json
import sys

def test_api_structure():
    """Testa la struttura dati dell'API"""
    
    # ID del batch generato dal debug_nesting_issue.py
    batch_id = "ef4e005d-cc35-43f2-b08e-b1240546aab3"
    
    print(f"🔍 ANALISI STRUTTURA DATI API")
    print("=" * 50)
    
    try:
        # Test endpoint /full
        print(f"📡 Test endpoint: /api/v1/batch_nesting/{batch_id}/full")
        url = f"http://localhost:8000/api/v1/batch_nesting/{batch_id}/full"
        
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analizza la struttura
            print("\n📋 STRUTTURA DATI RICEVUTA:")
            print("-" * 30)
            
            print("✅ Campi principali:")
            for key in data.keys():
                print(f"  • {key}: {type(data[key])}")
            
            # Controlla configurazione_json
            if 'configurazione_json' in data and data['configurazione_json']:
                print(f"\n✅ configurazione_json presente:")
                config = data['configurazione_json']
                for key in config.keys():
                    print(f"  • {key}: {type(config[key])}")
                
                # Tool positions
                if 'tool_positions' in config:
                    print(f"\n✅ tool_positions ({len(config['tool_positions'])} elementi):")
                    if config['tool_positions']:
                        first_tool = config['tool_positions'][0]
                        for key, value in first_tool.items():
                            print(f"  • {key}: {value} ({type(value)})")
                    else:
                        print("  (lista vuota)")
                else:
                    print(f"\n❌ tool_positions NON presente in configurazione_json")
            else:
                print(f"\n❌ configurazione_json mancante o null")
            
            # Controlla autoclave
            if 'autoclave' in data and data['autoclave']:
                print(f"\n✅ autoclave presente:")
                autoclave = data['autoclave']
                for key, value in autoclave.items():
                    print(f"  • {key}: {value} ({type(value)})")
            else:
                print(f"\n❌ autoclave mancante o null")
                
            # Salva JSON per debug completo
            print(f"\n💾 Salvataggio dati completi in debug_batch_data.json")
            with open('debug_batch_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
        else:
            print(f"❌ Errore HTTP: {response.status_code}")
            print(f"Risposta: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Errore di connessione. Assicurati che il server sia in esecuzione.")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    test_api_structure() 