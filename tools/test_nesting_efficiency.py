#!/usr/bin/env python3
"""
Test dell'efficienza del sistema di nesting
Verifica che l'efficienza sia ragionevole con i dati di test
"""

import sys
import os
import requests
import json
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_nesting_efficiency():
    """Testa l'efficienza del nesting con diversi scenari"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 TEST EFFICIENZA NESTING")
    print("=" * 50)
    
    # 1. Controlla autoclavi disponibili
    print("📋 Controllo autoclavi...")
    try:
        response = requests.get(f"{base_url}/api/autoclavi/")
        autoclavi = response.json()
        print(f"✅ Trovate {len(autoclavi)} autoclavi")
        for auto in autoclavi:
            print(f"   🏭 {auto['nome']}: {auto['lunghezza']}x{auto['larghezza_piano']}mm")
    except Exception as e:
        print(f"❌ Errore nel recupero autoclavi: {e}")
        return False
    
    # 2. Controlla ODL disponibili
    print("\n📋 Controllo ODL...")
    try:
        response = requests.get(f"{base_url}/api/odl/")
        all_odl = response.json()
        odl_attesa_cura = [odl for odl in all_odl if odl['status'] == 'Attesa Cura']
        print(f"✅ Trovati {len(odl_attesa_cura)} ODL in 'Attesa Cura'")
        
        if len(odl_attesa_cura) < 4:
            print("❌ Troppo pochi ODL per il test")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel recupero ODL: {e}")
        return False
    
    # 3. Test nesting con autoclave grande
    print("\n🧪 Test nesting con autoclave LARGE...")
    try:
        # Prendi i primi 6 ODL per un test ragionevole
        test_odl_ids = [str(odl['id']) for odl in odl_attesa_cura[:6]]
        
        payload = {
            "odl_ids": test_odl_ids,
            "autoclave_ids": ["1"],  # Autoclave Large come stringa
            "parameters": {
                "padding_mm": 15,
                "min_distance_mm": 10,
                "vacuum_lines_capacity": 10,
                "priorita_area": True
            }
        }
        
        print(f"   📦 Testing con ODL: {test_odl_ids}")
        
        response = requests.post(
            f"{base_url}/api/batch_nesting/genera",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            efficiency = result.get('efficiency', 0)
            positioned_tools = len(result.get('positioned_tools', []))
            total_weight = result.get('total_weight', 0)
            
            print(f"   ✅ Nesting completato!")
            print(f"   📊 Efficienza: {efficiency:.1f}%")
            print(f"   🔧 Tool posizionati: {positioned_tools}/{len(test_odl_ids)}")
            print(f"   ⚖️ Peso totale: {total_weight:.1f}kg")
            
            # Valutazione efficienza
            if efficiency >= 60:
                print(f"   🎉 EFFICIENZA OTTIMA: {efficiency:.1f}% ≥ 60%")
                return True
            elif efficiency >= 40:
                print(f"   ⚠️ EFFICIENZA ACCETTABILE: {efficiency:.1f}% ≥ 40%")
                return True
            else:
                print(f"   ❌ EFFICIENZA BASSA: {efficiency:.1f}% < 40%")
                print("   🔍 Possibili cause:")
                print("     - Tool troppo grandi per l'autoclave")
                print("     - Algoritmo di posizionamento non ottimale")
                print("     - Parametri di padding troppo conservativi")
                return False
                
        else:
            print(f"   ❌ Errore API: {response.status_code}")
            print(f"   📝 Risposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel test nesting: {e}")
        return False

if __name__ == "__main__":
    success = test_nesting_efficiency()
    if success:
        print("\n🎉 TEST COMPLETATO CON SUCCESSO!")
        print("✅ Il sistema di nesting funziona correttamente")
    else:
        print("\n❌ TEST FALLITO!")
        print("🔧 Il sistema di nesting necessita di correzioni")
    
    sys.exit(0 if success else 1) 