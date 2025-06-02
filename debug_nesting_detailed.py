#!/usr/bin/env python3
"""
Script di debug dettagliato per il problema batch_id None
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def debug_nesting_generation():
    """Debug dettagliato della generazione nesting"""
    print("🔍 DEBUG DETTAGLIATO GENERAZIONE NESTING")
    print("=" * 60)
    
    # Payload di test
    payload = {
        "odl_ids": ["1"],  # Solo un ODL per semplificare
        "autoclave_ids": ["1"],
        "parametri": {
            "padding_mm": 10,
            "min_distance_mm": 8
        }
    }
    
    print(f"📤 Payload inviato:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        # Chiamata API
        response = requests.post(
            f"{API_BASE}/batch_nesting/genera",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Headers: {dict(response.headers)}")
        print()
        
        # Analisi risposta
        if response.status_code == 200:
            data = response.json()
            print("✅ RISPOSTA RICEVUTA:")
            print(json.dumps(data, indent=2))
            
            # Analisi campi specifici
            print("\n🔍 ANALISI CAMPI:")
            print(f"  - batch_id: {repr(data.get('batch_id'))}")
            print(f"  - success: {data.get('success')}")
            print(f"  - message: {data.get('message')}")
            print(f"  - algorithm_status: {data.get('algorithm_status')}")
            
        else:
            print("❌ ERRORE NELLA RISPOSTA:")
            print(f"Status: {response.status_code}")
            
            try:
                error_data = response.json()
                print("Error JSON:")
                print(json.dumps(error_data, indent=2))
                
                # Analisi errore Pydantic
                if "detail" in error_data:
                    detail = error_data["detail"]
                    if "validation error" in detail:
                        print("\n🚨 ERRORE DI VALIDAZIONE PYDANTIC IDENTIFICATO:")
                        print(f"   {detail}")
                        
                        if "batch_id" in detail and "NoneType" in detail:
                            print("\n💡 CAUSA: Il servizio sta restituendo None per batch_id")
                            print("   Questo indica un problema nel RobustNestingService")
                            
            except:
                print("Response text:")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Eccezione durante la chiamata: {str(e)}")

def test_data_consistency():
    """Verifica la consistenza dei dati"""
    print("\n🔍 VERIFICA CONSISTENZA DATI")
    print("=" * 40)
    
    try:
        response = requests.get(f"{API_BASE}/batch_nesting/data")
        if response.status_code == 200:
            data = response.json()
            
            odl_count = len(data.get('odl_in_attesa_cura', []))
            autoclave_count = len(data.get('autoclavi_disponibili', []))
            
            print(f"✅ ODL disponibili: {odl_count}")
            print(f"✅ Autoclavi disponibili: {autoclave_count}")
            
            if odl_count > 0 and autoclave_count > 0:
                print("✅ Dati sufficienti per il nesting")
                
                # Mostra primo ODL e autoclave
                first_odl = data['odl_in_attesa_cura'][0]
                first_autoclave = data['autoclavi_disponibili'][0]
                
                print(f"\n📋 Primo ODL (ID: {first_odl['id']}):")
                print(f"   - Status: {first_odl['status']}")
                print(f"   - Tool: {first_odl.get('tool', {}).get('part_number_tool', 'N/A')}")
                print(f"   - Dimensioni tool: {first_odl.get('tool', {}).get('larghezza_piano', 0)}x{first_odl.get('tool', {}).get('lunghezza_piano', 0)}")
                
                print(f"\n🏭 Prima Autoclave (ID: {first_autoclave['id']}):")
                print(f"   - Nome: {first_autoclave['nome']}")
                print(f"   - Stato: {first_autoclave['stato']}")
                print(f"   - Dimensioni: {first_autoclave['larghezza_piano']}x{first_autoclave['lunghezza']}")
                
                return True
            else:
                print("❌ Dati insufficienti per il nesting")
                return False
        else:
            print(f"❌ Errore nel recupero dati: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

def main():
    """Esegue il debug completo"""
    print("🧪 DEBUG COMPLETO PROBLEMA NESTING")
    print("=" * 80)
    
    # Test 1: Verifica dati
    data_ok = test_data_consistency()
    
    if not data_ok:
        print("\n❌ PROBLEMA: Dati non disponibili per il nesting")
        return
    
    # Test 2: Debug generazione
    debug_nesting_generation()
    
    print("\n" + "=" * 80)
    print("🎯 CONCLUSIONI:")
    print("   Se vedi 'batch_id: None' nell'output sopra, il problema è nel")
    print("   RobustNestingService che restituisce None invece di una stringa.")
    print("   Questo può accadere se:")
    print("   1. Il nesting fallisce completamente")
    print("   2. Non vengono trovati ODL/autoclavi validi")
    print("   3. C'è un errore nell'algoritmo di nesting")

if __name__ == "__main__":
    main() 