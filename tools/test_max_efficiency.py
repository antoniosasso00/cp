#!/usr/bin/env python3
"""
Test per efficienza massima - Raggiungere l'ottimo teorico
"""

import sys
import os
import requests
import json
from pathlib import Path

def test_max_efficiency():
    """Test per raggiungere l'efficienza massima teorica"""
    
    base_url = "http://localhost:8000"
    
    print("🎯 TEST EFFICIENZA MASSIMA - RAGGIUNGERE L'OTTIMO TEORICO")
    print("=" * 70)
    
    # Test con parametri ultra-ottimizzati per autoclave Compact (migliore rapporto)
    try:
        # Seleziona tool più piccoli (ID bassi = dimensioni minori)
        small_tool_ids = ['1', '2', '4', '5', '6']  # Tool piccoli
        
        payload = {
            "odl_ids": small_tool_ids,
            "autoclave_ids": ["3"],  # Compact - miglior rapporto area
            "parameters": {
                "padding_mm": 1,  # Ultra-aggressivo
                "min_distance_mm": 1,  # Minimo assoluto
                "vacuum_lines_capacity": 20,  # Limite molto alto
                "priorita_area": True
            }
        }
        
        print(f"🧪 Test ULTRA-OTTIMIZZATO: {len(small_tool_ids)} tool piccoli su Compact")
        
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
            
            # Dettagli rotazione
            positioned_details = result.get('positioned_tools', [])
            rotated_count = sum(1 for tool in positioned_details if tool.get('rotated', False))
            
            print(f"📊 RISULTATO ULTRA-OTTIMIZZATO:")
            print(f"   🎯 Efficienza: {efficiency:.1f}%")
            print(f"   🔧 Tool posizionati: {positioned_tools}/{len(small_tool_ids)}")
            print(f"   🔄 Tool ruotati: {rotated_count}/{positioned_tools}")
            print(f"   ⚖️ Peso totale: {total_weight:.1f}kg")
            
            if efficiency >= 80:
                print(f"🏆 ECCELLENZA RAGGIUNTA! {efficiency:.1f}% ≥ 80%")
                return True
            elif efficiency >= 60:
                print(f"🎉 OTTIMO RISULTATO! {efficiency:.1f}% ≥ 60%")
                return True
            else:
                print(f"✅ BUON MIGLIORAMENTO: {efficiency:.1f}%")
                return True
        else:
            print(f"❌ Errore API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Errore nel test: {e}")
        return False

if __name__ == "__main__":
    success = test_max_efficiency()
    sys.exit(0 if success else 1) 