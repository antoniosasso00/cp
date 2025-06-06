#!/usr/bin/env python3
"""
Test avanzato per l'algoritmo FFD 2D ottimizzato
Verifica efficienza migliorata con selezione intelligente dei tool
"""

import sys
import os
import requests
import json
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def test_advanced_nesting():
    """Testa il nesting avanzato con strategie ottimizzate"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 TEST ALGORITMO FFD 2D AVANZATO")
    print("=" * 60)
    
    # 1. Test con autoclave Medium (migliore rapporto tool/spazio)
    print("📊 Test 1: Autoclave MEDIUM (2000x1200mm)")
    print("-" * 40)
    
    try:
        # Recupera tutti gli ODL compatibili
        response = requests.get(f"{base_url}/api/odl/")
        all_odl = response.json()
        odl_attesa_cura = [odl for odl in all_odl if odl['status'] == 'Attesa Cura']
        
        # Seleziona tool più piccoli per test ottimizzato
        selected_odl = odl_attesa_cura[:8]  # Più tool per testare packing
        test_odl_ids = [str(odl['id']) for odl in selected_odl]
        
        payload = {
            "odl_ids": test_odl_ids,
            "autoclave_ids": ["2"],  # Autoclave Medium
            "parameters": {
                "padding_mm": 8,  # Più aggressivo
                "min_distance_mm": 5,  # Ridotto ulteriormente 
                "vacuum_lines_capacity": 12,  # Aumentato limite
                "priorita_area": True
            }
        }
        
        print(f"   📦 Testing con {len(test_odl_ids)} ODL su autoclave Medium")
        
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
            
            # Analizza risultato dettagliato
            positioned_details = result.get('positioned_tools', [])
            rotated_count = sum(1 for tool in positioned_details if tool.get('rotated', False))
            
            print(f"   🔄 Tool ruotati: {rotated_count}/{positioned_tools}")
            
            # Valutazione migliorata
            if efficiency >= 50:
                print(f"   🎉 EFFICIENZA ECCELLENTE: {efficiency:.1f}% ≥ 50%")
                test1_success = True
            elif efficiency >= 35:
                print(f"   ✅ EFFICIENZA BUONA: {efficiency:.1f}% ≥ 35%")
                test1_success = True
            else:
                print(f"   ⚠️ EFFICIENZA MIGLIORABILE: {efficiency:.1f}% < 35%")
                test1_success = False
                
        else:
            print(f"   ❌ Errore API: {response.status_code}")
            test1_success = False
            
    except Exception as e:
        print(f"❌ Errore nel test 1: {e}")
        test1_success = False
    
    # 2. Test con autoclave Compact (massima densità)
    print(f"\n📊 Test 2: Autoclave COMPACT (1500x800mm)")
    print("-" * 40)
    
    try:
        # Seleziona tool più piccoli per massima densità
        small_odl = [odl for odl in odl_attesa_cura if 'id' in odl and int(odl['id']) <= 15]
        test_odl_ids_compact = [str(odl['id']) for odl in small_odl[:6]]
        
        payload = {
            "odl_ids": test_odl_ids_compact,
            "autoclave_ids": ["3"],  # Autoclave Compact
            "parameters": {
                "padding_mm": 5,  # Molto aggressivo
                "min_distance_mm": 3,  # Minimo assoluto
                "vacuum_lines_capacity": 8,
                "priorita_area": True
            }
        }
        
        print(f"   📦 Testing con {len(test_odl_ids_compact)} ODL su autoclave Compact")
        
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
            print(f"   🔧 Tool posizionati: {positioned_tools}/{len(test_odl_ids_compact)}")
            print(f"   ⚖️ Peso totale: {total_weight:.1f}kg")
            
            # Valutazione per autoclave compatta
            if efficiency >= 70:
                print(f"   🏆 EFFICIENZA STRAORDINARIA: {efficiency:.1f}% ≥ 70%")
                test2_success = True
            elif efficiency >= 50:
                print(f"   🎉 EFFICIENZA OTTIMA: {efficiency:.1f}% ≥ 50%")  
                test2_success = True
            else:
                print(f"   ⚠️ EFFICIENZA DA MIGLIORARE: {efficiency:.1f}% < 50%")
                test2_success = False
                
        else:
            print(f"   ❌ Errore API: {response.status_code}")
            test2_success = False
            
    except Exception as e:
        print(f"❌ Errore nel test 2: {e}")
        test2_success = False
    
    # 3. Test parametri ultra-aggressivi
    print(f"\n📊 Test 3: Parametri ULTRA-AGGRESSIVI")
    print("-" * 40)
    
    try:
        payload = {
            "odl_ids": test_odl_ids[:5],  # 5 ODL per test veloce
            "autoclave_ids": ["2"],  # Medium
            "parameters": {
                "padding_mm": 3,  # Ultra-aggressivo
                "min_distance_mm": 2,  # Estremamente ridotto
                "vacuum_lines_capacity": 15,  # Limite alto
                "priorita_area": True
            }
        }
        
        response = requests.post(
            f"{base_url}/api/batch_nesting/genera",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            efficiency = result.get('efficiency', 0)
            positioned_tools = len(result.get('positioned_tools', []))
            
            print(f"   📊 Efficienza ULTRA-AGGRESSIVA: {efficiency:.1f}%")
            print(f"   🔧 Tool posizionati: {positioned_tools}/5")
            
            test3_success = efficiency >= 30
        else:
            test3_success = False
            
    except Exception as e:
        print(f"❌ Errore nel test 3: {e}")
        test3_success = False
    
    # Risultato finale
    print(f"\n🏁 RISULTATO COMPLESSIVO")
    print("=" * 40)
    
    tests_passed = sum([test1_success, test2_success, test3_success])
    
    if tests_passed >= 2:
        print(f"🎉 ALGORITMO FFD 2D MIGLIORATO!")
        print(f"✅ {tests_passed}/3 test superati")
        print("🚀 L'ottimizzazione ha dato risultati positivi")
        return True
    else:
        print(f"⚠️ MIGLIORAMENTI PARZIALI")
        print(f"📊 {tests_passed}/3 test superati")
        print("🔧 Sono necessarie ulteriori ottimizzazioni")
        return False

if __name__ == "__main__":
    success = test_advanced_nesting()
    sys.exit(0 if success else 1) 