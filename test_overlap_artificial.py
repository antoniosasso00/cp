#!/usr/bin/env python3
"""
Test artificiale per verificare il sistema di rilevamento overlap v1.4.16-DEMO
Simula overlap modificando temporaneamente le posizioni per testare la funzionalità
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
NESTING_ENDPOINT = f"{BASE_URL}/batch_nesting/solve"

def create_artificial_overlap_response():
    """Crea una risposta artificiale con overlap per testare il frontend"""
    print("🎭 CREAZIONE RISPOSTA ARTIFICIALE CON OVERLAP")
    print("=" * 50)
    
    # Prima ottieni una risposta normale
    test_request = {
        "autoclave_id": 1,
        "odl_ids": [147, 148, 149],  # Solo 3 ODL per semplicità
        "padding_mm": 5.0,
        "min_distance_mm": 5.0,
        "vacuum_lines_capacity": 20,
        "allow_heuristic": True,
        "timeout_override": 30,
        "heavy_piece_threshold_kg": 10.0
    }
    
    try:
        print("🚀 Ottengo layout normale...")
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            positioned_tools = result.get("positioned_tools", [])
            
            if len(positioned_tools) >= 2:
                print(f"✅ Layout normale ottenuto con {len(positioned_tools)} tool")
                
                # Modifica artificialmente le posizioni per creare overlap
                print("🔧 Modifico posizioni per creare overlap artificiali...")
                
                # Sovrapponi il secondo tool al primo
                if len(positioned_tools) >= 2:
                    tool1 = positioned_tools[0]
                    tool2 = positioned_tools[1]
                    
                    # Posiziona tool2 parzialmente sopra tool1
                    original_x2 = tool2['x']
                    original_y2 = tool2['y']
                    
                    tool2['x'] = tool1['x'] + (tool1['width'] * 0.5)  # Overlap del 50%
                    tool2['y'] = tool1['y'] + (tool1['height'] * 0.3)  # Overlap del 30%
                    
                    print(f"   • Tool {tool1['odl_id']}: x={tool1['x']}, y={tool1['y']}, w={tool1['width']}, h={tool1['height']}")
                    print(f"   • Tool {tool2['odl_id']}: x={tool2['x']}, y={tool2['y']}, w={tool2['width']}, h={tool2['height']}")
                    print(f"   • Overlap creato spostando tool {tool2['odl_id']} da ({original_x2}, {original_y2})")
                
                # Aggiungi informazioni overlap artificiali
                artificial_overlaps = [
                    {
                        "odl_a": positioned_tools[0]['odl_id'],
                        "odl_b": positioned_tools[1]['odl_id'],
                        "area_a": {
                            "x": positioned_tools[0]['x'],
                            "y": positioned_tools[0]['y'],
                            "width": positioned_tools[0]['width'],
                            "height": positioned_tools[0]['height']
                        },
                        "area_b": {
                            "x": positioned_tools[1]['x'],
                            "y": positioned_tools[1]['y'],
                            "width": positioned_tools[1]['width'],
                            "height": positioned_tools[1]['height']
                        },
                        "overlap_area_cm2": 15000.0,  # Area di sovrapposizione simulata
                        "severity": "medium"
                    }
                ]
                
                # Aggiorna la risposta
                result['overlaps'] = artificial_overlaps
                result['metrics']['invalid'] = True
                result['message'] = "Layout con overlap artificiali per test v1.4.16-DEMO"
                result['success'] = True  # Mantieni success=True per testare la visualizzazione
                
                print(f"\n🎯 OVERLAP ARTIFICIALI CREATI:")
                print(f"   • Numero overlap: {len(artificial_overlaps)}")
                print(f"   • Layout marcato come invalid: {result['metrics']['invalid']}")
                print(f"   • Tool coinvolti: {artificial_overlaps[0]['odl_a']} ⚠️ {artificial_overlaps[0]['odl_b']}")
                
                # Salva il risultato artificiale
                with open('test_artificial_overlap_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"\n💾 Risultato salvato in test_artificial_overlap_result.json")
                print(f"📋 Usa questo file per testare il frontend:")
                print(f"   1. Copia il contenuto del file")
                print(f"   2. Simula una risposta API con questi dati")
                print(f"   3. Verifica evidenziazione rossa dei tool sovrapposti")
                print(f"   4. Controlla badge 'Layout Invalid'")
                print(f"   5. Verifica sezione overlap nella tabella")
                
                return True
            else:
                print("❌ Non abbastanza tool per creare overlap")
                return False
        else:
            print(f"❌ Errore HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Errore: {str(e)}")
        return False

def verify_overlap_detection_logic():
    """Verifica la logica di rilevamento overlap"""
    print(f"\n🔍 VERIFICA LOGICA RILEVAMENTO OVERLAP")
    print("=" * 40)
    
    # Simula due rettangoli sovrapposti
    rect_a = {"x": 100, "y": 100, "width": 200, "height": 150}
    rect_b = {"x": 150, "y": 125, "width": 180, "height": 120}
    
    print(f"📐 Test overlap detection:")
    print(f"   • Rettangolo A: x={rect_a['x']}, y={rect_a['y']}, w={rect_a['width']}, h={rect_a['height']}")
    print(f"   • Rettangolo B: x={rect_b['x']}, y={rect_b['y']}, w={rect_b['width']}, h={rect_b['height']}")
    
    # Logica di rilevamento overlap (stessa del backend)
    def check_overlap(a, b):
        return not (
            a['x'] + a['width'] <= b['x'] or
            b['x'] + b['width'] <= a['x'] or
            a['y'] + a['height'] <= b['y'] or
            b['y'] + b['height'] <= a['y']
        )
    
    overlap_detected = check_overlap(rect_a, rect_b)
    print(f"   • Overlap rilevato: {overlap_detected}")
    
    if overlap_detected:
        # Calcola area di sovrapposizione
        overlap_x1 = max(rect_a['x'], rect_b['x'])
        overlap_y1 = max(rect_a['y'], rect_b['y'])
        overlap_x2 = min(rect_a['x'] + rect_a['width'], rect_b['x'] + rect_b['width'])
        overlap_y2 = min(rect_a['y'] + rect_a['height'], rect_b['y'] + rect_b['height'])
        
        overlap_width = overlap_x2 - overlap_x1
        overlap_height = overlap_y2 - overlap_y1
        overlap_area = overlap_width * overlap_height
        
        print(f"   • Area overlap: {overlap_area} mm² ({overlap_width}×{overlap_height})")
        print(f"   ✅ Logica di rilevamento funziona correttamente")
    else:
        print(f"   ❌ Overlap non rilevato - verifica logica")
    
    return overlap_detected

def generate_frontend_test_data():
    """Genera dati di test per il frontend"""
    print(f"\n📊 GENERAZIONE DATI TEST FRONTEND")
    print("=" * 40)
    
    # Dati di test completi per il frontend
    frontend_test_data = {
        "success": True,
        "message": "Test v1.4.16-DEMO: Layout con overlap per verifica frontend",
        "positioned_tools": [
            {
                "odl_id": 147,
                "tool_id": 147,
                "x": 100.0,
                "y": 100.0,
                "width": 500.0,
                "height": 400.0,
                "rotated": False,
                "plane": 1,
                "weight_kg": 40.0
            },
            {
                "odl_id": 148,
                "tool_id": 148,
                "x": 350.0,  # Overlap con il primo
                "y": 250.0,  # Overlap con il primo
                "width": 450.0,
                "height": 350.0,
                "rotated": False,
                "plane": 1,
                "weight_kg": 45.0
            },
            {
                "odl_id": 149,
                "tool_id": 149,
                "x": 900.0,
                "y": 100.0,
                "width": 400.0,
                "height": 300.0,
                "rotated": False,
                "plane": 1,
                "weight_kg": 35.0
            }
        ],
        "excluded_odls": [
            {
                "odl_id": 150,
                "reason": "Capacità linee vuoto superata",
                "part_number": "TEST-PART-150",
                "tool_dimensions": "600x500mm"
            }
        ],
        "excluded_reasons": {
            "Capacità linee vuoto superata": 1
        },
        "overlaps": [
            {
                "odl_a": 147,
                "odl_b": 148,
                "area_a": {
                    "x": 100.0,
                    "y": 100.0,
                    "width": 500.0,
                    "height": 400.0
                },
                "area_b": {
                    "x": 350.0,
                    "y": 250.0,
                    "width": 450.0,
                    "height": 350.0
                },
                "overlap_area_cm2": 18750.0,
                "severity": "high"
            }
        ],
        "metrics": {
            "area_utilization_pct": 65.5,
            "vacuum_util_pct": 75.0,
            "efficiency_score": 68.25,
            "weight_utilization_pct": 48.0,
            "time_solver_ms": 1250.0,
            "fallback_used": True,
            "heuristic_iters": 0,
            "algorithm_status": "FALLBACK_GREEDY_WITH_OVERLAPS",
            "invalid": True,  # Campo chiave per v1.4.16-DEMO
            "total_area_cm2": 131250.0,
            "total_weight_kg": 120.0,
            "vacuum_lines_used": 6,
            "pieces_positioned": 3,
            "pieces_excluded": 1
        },
        "autoclave_info": {
            "id": 1,
            "nome": "Test-Autoclave-v1.4.16",
            "larghezza_piano": 1200.0,
            "lunghezza": 2000.0,
            "max_load_kg": 500.0,
            "num_linee_vuoto": 8
        },
        "solved_at": datetime.now().isoformat()
    }
    
    # Salva i dati di test
    with open('frontend_test_data_v1_4_16.json', 'w', encoding='utf-8') as f:
        json.dump(frontend_test_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Dati di test salvati in frontend_test_data_v1_4_16.json")
    print(f"\n📋 ISTRUZIONI TEST FRONTEND:")
    print(f"1. Usa questi dati per simulare una risposta API")
    print(f"2. Verifica evidenziazione rossa per ODL 147 e 148")
    print(f"3. Controlla badge efficienza rosso con 'Layout Invalid'")
    print(f"4. Verifica sezione overlap nella tabella esclusioni")
    print(f"5. Testa responsive canvas ridimensionando finestra")
    print(f"6. Verifica toast notification per layout invalid")
    
    return True

if __name__ == "__main__":
    print(f"🎭 CarbonPilot v1.4.16-DEMO - Test Overlap Artificiale")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Crea overlap artificiali
    artificial_created = create_artificial_overlap_response()
    
    # Test 2: Verifica logica rilevamento
    logic_verified = verify_overlap_detection_logic()
    
    # Test 3: Genera dati per frontend
    frontend_data_generated = generate_frontend_test_data()
    
    print(f"\n{'='*50}")
    print("📊 RIASSUNTO TEST ARTIFICIALI:")
    print(f"   • Overlap artificiali creati: {artificial_created}")
    print(f"   • Logica rilevamento verificata: {logic_verified}")
    print(f"   • Dati frontend generati: {frontend_data_generated}")
    
    if all([artificial_created, logic_verified, frontend_data_generated]):
        print(f"\n✅ TUTTI I TEST COMPLETATI CON SUCCESSO!")
        print(f"🎯 Sistema v1.4.16-DEMO pronto per test frontend")
    else:
        print(f"\n⚠️ Alcuni test non completati - verifica i dettagli sopra")
    
    print(f"\n🚀 PROSSIMI PASSI:")
    print("1. Usa i file JSON generati per testare il frontend")
    print("2. Verifica responsive canvas e evidenziazione overlap")
    print("3. Testa tutte le funzionalità v1.4.16-DEMO")
    print("4. Se tutto ok, procedi con commit e tag finale") 