#!/usr/bin/env python3
"""
Test per il nuovo sistema di nesting migliorato
"""
import requests
import json

def test_enhanced_nesting():
    """Testa il nuovo endpoint di nesting migliorato"""
    base_url = "http://localhost:8000/api/v1"  # Porta corretta
    
    print("🧪 Test Sistema Nesting Migliorato")
    print("=" * 50)
    
    # Test 1: Verifica ODL disponibili
    print("\n1. Test ODL disponibili:")
    try:
        r = requests.get(f"{base_url}/nesting/auto-multi/odl-disponibili")
        print(f"   Status: {r.status_code}")
        data = r.json()
        print(f"   ODL trovati: {data.get('total', 0)}")
        if data.get('data'):
            print(f"   Primo ODL: ID={data['data'][0].get('id')}, Parte={data['data'][0].get('parte_descrizione')}")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 2: Verifica autoclavi disponibili
    print("\n2. Test autoclavi disponibili:")
    try:
        r = requests.get(f"{base_url}/nesting/auto-multi/autoclavi-disponibili")
        print(f"   Status: {r.status_code}")
        data = r.json()
        print(f"   Autoclavi trovate: {data.get('total', 0)}")
        if data.get('data'):
            autoclave = data['data'][0]
            print(f"   Prima autoclave: {autoclave.get('nome')} ({autoclave.get('lunghezza')}x{autoclave.get('larghezza_piano')}mm)")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 3: Test nuovo endpoint enhanced-preview con body JSON corretto
    print("\n3. Test Enhanced Preview con body JSON:")
    try:
        # Payload corretto per enhanced-preview
        payload = {
            "odl_ids": [1, 2, 3],  # Lista di IDs nel body
            "autoclave_id": 1,     # Autoclave ID nel body
            "constraints": {       # Constraints opzionali
                "distanza_minima_tool_mm": 20,
                "padding_bordo_mm": 15,
                "margine_sicurezza_peso_percent": 10,
                "efficienza_minima_percent": 30,  # Ridotto per test
                "separa_cicli_cura": True,
                "abilita_rotazioni": True
            }
        }
        
        r = requests.post(
            f"{base_url}/nesting/enhanced-preview", 
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Preview generato con successo!")
            print(f"   Successo: {data.get('success')}")
            print(f"   Messaggio: {data.get('message')}")
            
            if 'autoclave' in data:
                autoclave = data['autoclave']
                print(f"   Autoclave: {autoclave.get('nome')}")
                print(f"   Area piano: {autoclave.get('area_piano', 0):.1f} cm²")
            
            if 'statistiche' in data:
                stats = data['statistiche']
                print(f"   ODL inclusi: {stats.get('odl_inclusi', 0)}")
                print(f"   ODL esclusi: {stats.get('odl_esclusi', 0)}")
                print(f"   Efficienza: {stats.get('efficienza_percent', 0):.1f}%")
                print(f"   Peso totale: {stats.get('peso_totale_kg', 0):.1f}kg")
                print(f"   Valvole utilizzate: {stats.get('valvole_utilizzate', 0)}")
            
            if 'tool_positions' in data:
                positions = data['tool_positions']
                print(f"   Posizioni tool calcolate: {len(positions)}")
                for i, pos in enumerate(positions[:3]):  # Prime 3 posizioni
                    print(f"      Tool {i+1}: ODL {pos.get('odl_id')} a ({pos.get('x'):.1f}, {pos.get('y'):.1f})")
            
            if 'odl_esclusi' in data and data['odl_esclusi']:
                print(f"\n   📋 Motivi esclusione:")
                for excluded in data['odl_esclusi'][:3]:  # Primi 3
                    print(f"      ODL {excluded.get('id')}: {excluded.get('motivo_esclusione')}")
                    
        elif r.status_code == 422:
            print(f"   ❌ Errore validazione: {r.text}")
        else:
            response_text = r.text
            print(f"   ❌ Errore {r.status_code}: {response_text}")
            
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 4: Test con vincoli personalizzati
    print("\n4. Test con vincoli personalizzati:")
    try:
        payload_custom = {
            "odl_ids": [1, 2],  # Meno ODL per test più semplice
            "autoclave_id": 1,
            "constraints": {
                "distanza_minima_tool_mm": 30,  # Maggiore distanza
                "padding_bordo_mm": 20,         # Maggiore padding
                "margine_sicurezza_peso_percent": 5,  # Minore margine peso
                "efficienza_minima_percent": 20,      # Efficienza molto bassa
                "separa_cicli_cura": False,           # Permetti cicli misti
                "abilita_rotazioni": False            # Disabilita rotazioni
            }
        }
        
        r = requests.post(
            f"{base_url}/nesting/enhanced-preview", 
            json=payload_custom,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Vincoli personalizzati applicati: {data.get('success')}")
            if 'statistiche' in data:
                stats = data['statistiche']
                print(f"   Efficienza: {stats.get('efficienza_percent', 0):.1f}%")
                
            if 'tool_positions' in data:
                rotated_count = sum(1 for pos in data['tool_positions'] if pos.get('rotated', False))
                print(f"   Tool ruotati (dovrebbe essere 0): {rotated_count}")
        elif r.status_code == 422:
            print(f"   ❌ Errore validazione: {r.text}")
        else:
            print(f"   ❌ Errore {r.status_code}: {r.text}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # Test 5: Test robustezza con ODL inesistenti
    print("\n5. Test robustezza:")
    try:
        payload_invalid = {
            "odl_ids": [99999, 99998],  # ODL che non esistono
            "autoclave_id": 1,
            "constraints": {}
        }
        
        r = requests.post(
            f"{base_url}/nesting/enhanced-preview", 
            json=payload_invalid,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status con ODL inesistenti: {r.status_code}")
        
        if r.status_code == 404:
            print(f"   ✅ Gestione corretta ODL inesistenti")
        else:
            print(f"   ⚠️ Status inaspettato: {r.status_code}")
            if r.status_code == 422:
                print(f"      Detail: {r.text}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Enhanced Nesting completato!")

if __name__ == "__main__":
    test_enhanced_nesting() 