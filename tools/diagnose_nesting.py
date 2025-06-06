#!/usr/bin/env python3
"""
Diagnosi dettagliata del sistema di nesting
Analizza le cause dell'efficienza bassa
"""

import sys
import os
import requests
import json
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def analyze_tool_sizes():
    """Analizza le dimensioni dei tool rispetto alle autoclavi"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 DIAGNOSI DIMENSIONI TOOL vs AUTOCLAVI")
    print("=" * 60)
    
    # Recupera autoclavi
    response = requests.get(f"{base_url}/api/autoclavi/")
    autoclavi = response.json()
    
    # Recupera ODL con tool
    response = requests.get(f"{base_url}/api/odl/")
    all_odl = response.json()
    odl_attesa_cura = [odl for odl in all_odl if odl['status'] == 'Attesa Cura']
    
    print(f"📊 Analisi {len(odl_attesa_cura)} ODL vs {len(autoclavi)} autoclavi\n")
    
    for auto in autoclavi:
        print(f"🏭 {auto['nome']}")
        print(f"   📏 Dimensioni: {auto['lunghezza']}x{auto['larghezza_piano']}mm")
        area_autoclave = auto['lunghezza'] * auto['larghezza_piano']
        print(f"   📊 Area totale: {area_autoclave/1000000:.2f} m²")
        
        # Analizza tool che potrebbero entrare
        compatible_tools = []
        total_tool_area = 0
        
        for odl in odl_attesa_cura[:10]:  # Primi 10 per test
            # Simula dimensioni tool (dovremmo recuperarle dal database)
            # Per ora uso dimensioni simulate basate sui dati del seed
            tool_width = 200 + (odl['id'] % 5) * 100  # 200-600mm
            tool_height = 150 + (odl['id'] % 4) * 100  # 150-450mm
            tool_area = tool_width * tool_height
            
            # Controlla se il tool può entrare (con padding)
            padding = 15
            if (tool_width + 2*padding <= auto['lunghezza'] and 
                tool_height + 2*padding <= auto['larghezza_piano']):
                compatible_tools.append({
                    'odl_id': odl['id'],
                    'width': tool_width,
                    'height': tool_height,
                    'area': tool_area
                })
                total_tool_area += tool_area
        
        if compatible_tools:
            theoretical_efficiency = (total_tool_area / area_autoclave) * 100
            print(f"   ✅ Tool compatibili: {len(compatible_tools)}")
            print(f"   📊 Area tool totale: {total_tool_area/1000000:.2f} m²")
            print(f"   🎯 Efficienza teorica: {theoretical_efficiency:.1f}%")
            
            if theoretical_efficiency > 100:
                print(f"   ⚠️ SOVRACCARICO: troppi tool per l'autoclave")
            elif theoretical_efficiency > 80:
                print(f"   🎉 OTTIMO: alta densità possibile")
            elif theoretical_efficiency > 50:
                print(f"   ✅ BUONO: densità ragionevole")
            else:
                print(f"   ⚠️ BASSO: pochi tool compatibili")
        else:
            print(f"   ❌ Nessun tool compatibile!")
        
        print()

def test_different_parameters():
    """Testa il nesting con parametri diversi"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 TEST PARAMETRI DIVERSI")
    print("=" * 40)
    
    # Recupera ODL
    response = requests.get(f"{base_url}/api/odl/")
    all_odl = response.json()
    odl_attesa_cura = [odl for odl in all_odl if odl['status'] == 'Attesa Cura']
    test_odl_ids = [str(odl['id']) for odl in odl_attesa_cura[:4]]  # Solo 4 per test veloce
    
    # Test con parametri diversi
    test_configs = [
        {"name": "Conservativo", "padding": 15, "distance": 10},
        {"name": "Moderato", "padding": 10, "distance": 5},
        {"name": "Aggressivo", "padding": 5, "distance": 2},
        {"name": "Minimo", "padding": 2, "distance": 1}
    ]
    
    for config in test_configs:
        print(f"\n🔧 Test {config['name']} (padding: {config['padding']}mm, distance: {config['distance']}mm)")
        
        payload = {
            "odl_ids": test_odl_ids,
            "autoclave_ids": ["1"],  # Autoclave Large
            "parameters": {
                "padding_mm": config['padding'],
                "min_distance_mm": config['distance'],
                "vacuum_lines_capacity": 10,
                "priorita_area": True
            }
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/batch_nesting/genera",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                efficiency = result.get('efficiency', 0)
                positioned_tools = len(result.get('positioned_tools', []))
                
                print(f"   📊 Efficienza: {efficiency:.1f}%")
                print(f"   🔧 Tool posizionati: {positioned_tools}/{len(test_odl_ids)}")
                
                if efficiency > 40:
                    print(f"   ✅ MIGLIORAMENTO SIGNIFICATIVO!")
                elif efficiency > 25:
                    print(f"   ⚠️ Miglioramento moderato")
                else:
                    print(f"   ❌ Ancora basso")
            else:
                print(f"   ❌ Errore: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")

if __name__ == "__main__":
    analyze_tool_sizes()
    test_different_parameters()
    
    print("\n🎯 RACCOMANDAZIONI:")
    print("1. Ridurre padding e distanze minime")
    print("2. Verificare dimensioni reali dei tool nel database")
    print("3. Ottimizzare algoritmo di posizionamento")
    print("4. Considerare rotazione dei tool") 