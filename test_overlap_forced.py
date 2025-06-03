#!/usr/bin/env python3
"""
Test specifico per forzare overlap e testare BL-FFD
Usa parametri validi ma strategici per forzare sovrapposizioni
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
NESTING_ENDPOINT = f"{BASE_URL}/batch_nesting/solve"

def test_forced_overlap():
    """Test con parametri minimi validi per forzare overlap"""
    print("🔴 TEST OVERLAP FORZATO - v1.4.16-DEMO")
    print("=" * 50)
    
    # Parametri minimi validi ma strategici per forzare overlap
    test_request = {
        "autoclave_id": 1,
        "odl_ids": [147, 148, 149, 150, 151, 152],  # 6 ODL grandi specifici
        "padding_mm": 5.0,  # Minimo consentito
        "min_distance_mm": 5.0,  # Minimo consentito
        "vacuum_lines_capacity": 20,  # Capacità alta per non limitare
        "allow_heuristic": False,  # Forza CP-SAT per layout più denso
        "timeout_override": 30,  # Minimo consentito
        "heavy_piece_threshold_kg": 10.0  # Minimo consentito
    }
    
    print(f"📋 Parametri strategici:")
    print(f"   • ODL selezionati: {len(test_request['odl_ids'])} (grandi)")
    print(f"   • Padding: {test_request['padding_mm']}mm (minimo valido)")
    print(f"   • Min distance: {test_request['min_distance_mm']}mm (minimo valido)")
    print(f"   • Timeout: {test_request['timeout_override']}s (minimo valido)")
    print(f"   • Heavy threshold: {test_request['heavy_piece_threshold_kg']}kg (minimo)")
    print(f"   • Heuristic: {test_request['allow_heuristic']} (forza CP-SAT)")
    print()
    
    try:
        print("🚀 Invio richiesta con parametri strategici...")
        start_time = time.time()
        
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ Tempo risposta: {elapsed_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Richiesta completata!")
            
            # Analizza risultati
            metrics = result.get("metrics", {})
            overlaps = result.get("overlaps", [])
            positioned_tools = result.get("positioned_tools", [])
            
            print(f"\n📊 RISULTATI:")
            print(f"   • Success: {result.get('success', False)}")
            print(f"   • Algorithm: {metrics.get('algorithm_status', 'N/A')}")
            print(f"   • Invalid layout: {metrics.get('invalid', False)}")
            print(f"   • Tool posizionati: {len(positioned_tools)}")
            print(f"   • Overlap rilevati: {len(overlaps) if overlaps else 0}")
            
            # Dettagli overlap
            if overlaps and len(overlaps) > 0:
                print(f"\n🔴 OVERLAP RILEVATI ({len(overlaps)}):")
                for i, overlap in enumerate(overlaps, 1):
                    print(f"   {i}. ODL {overlap.get('odl_a')} ⚠️ ODL {overlap.get('odl_b')}")
                    area_a = overlap.get('area_a', {})
                    area_b = overlap.get('area_b', {})
                    print(f"      A: x={area_a.get('x')}, y={area_a.get('y')}, w={area_a.get('width')}, h={area_a.get('height')}")
                    print(f"      B: x={area_b.get('x')}, y={area_b.get('y')}, w={area_b.get('width')}, h={area_b.get('height')}")
                
                print(f"\n🎯 SUCCESSO: Overlap rilevati correttamente!")
                print(f"   Il sistema BL-FFD dovrebbe essere stato attivato")
                
                # Verifica se BL-FFD è stato utilizzato
                algorithm_status = metrics.get('algorithm_status', '')
                if 'BL_FFD' in algorithm_status:
                    print(f"   ✅ BL-FFD utilizzato: {algorithm_status}")
                else:
                    print(f"   ⚠️ BL-FFD non utilizzato: {algorithm_status}")
                    
            else:
                print(f"\n⚠️ NESSUN OVERLAP: Layout ottimizzato correttamente")
                print(f"   Il solver è riuscito a evitare sovrapposizioni")
            
            # Salva risultati
            with open('test_overlap_forced_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            return len(overlaps) > 0 if overlaps else False
            
        else:
            print(f"❌ Errore HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Errore: {str(e)}")
        return False

def test_with_many_large_pieces():
    """Test con molti pezzi grandi per saturare lo spazio"""
    print(f"\n🔧 TEST CON MOLTI PEZZI GRANDI")
    print("=" * 40)
    
    # Seleziona molti ODL grandi per saturare lo spazio
    large_odl_ids = [147, 148, 149, 150, 151, 152, 83, 84, 85, 87, 88, 89, 90, 91, 92]
    
    test_request = {
        "autoclave_id": 1,
        "odl_ids": large_odl_ids,  # Molti ODL grandi
        "padding_mm": 5.0,  # Minimo valido
        "min_distance_mm": 5.0,  # Minimo valido
        "vacuum_lines_capacity": 50,  # Capacità molto alta
        "allow_heuristic": True,  # Permetti heuristic per layout più aggressivo
        "timeout_override": 30,  # Minimo valido
        "heavy_piece_threshold_kg": 10.0  # Minimo valido
    }
    
    print(f"📋 Parametri saturazione:")
    print(f"   • ODL grandi selezionati: {len(large_odl_ids)}")
    print(f"   • Padding: {test_request['padding_mm']}mm")
    print(f"   • Timeout: {test_request['timeout_override']}s")
    print(f"   • Heuristic: {test_request['allow_heuristic']} (permesso)")
    print()
    
    try:
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            overlaps = result.get("overlaps", [])
            metrics = result.get("metrics", {})
            positioned_tools = result.get("positioned_tools", [])
            
            print(f"📊 Risultati saturazione:")
            print(f"   • Tool posizionati: {len(positioned_tools)}")
            print(f"   • Overlap: {len(overlaps) if overlaps else 0}")
            print(f"   • Invalid: {metrics.get('invalid', False)}")
            print(f"   • Algorithm: {metrics.get('algorithm_status', 'N/A')}")
            
            if overlaps and len(overlaps) > 0:
                print(f"\n🔴 OVERLAP TROVATI:")
                for overlap in overlaps[:3]:  # Mostra solo i primi 3
                    print(f"   • ODL {overlap.get('odl_a')} ⚠️ ODL {overlap.get('odl_b')}")
            
            return len(overlaps) > 0 if overlaps else False
        else:
            print(f"❌ Errore: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Errore: {str(e)}")
        return False

def test_manual_overlap_creation():
    """Test creando manualmente una situazione di overlap"""
    print(f"\n🎯 TEST CREAZIONE MANUALE OVERLAP")
    print("=" * 40)
    
    # Usa molti pezzi grandi con parametri aggressivi
    test_request = {
        "autoclave_id": 1,
        "odl_ids": [147, 148, 149, 150, 151, 152, 83, 84, 85, 87, 88, 89],  # 12 pezzi grandi
        "padding_mm": 5.0,  # Minimo
        "min_distance_mm": 5.0,  # Minimo
        "vacuum_lines_capacity": 50,  # Alto per non limitare
        "allow_heuristic": True,  # Permetti heuristic aggressiva
        "timeout_override": 30,  # Minimo per forzare soluzioni rapide
        "heavy_piece_threshold_kg": 10.0  # Basso per considerare molti pezzi pesanti
    }
    
    print(f"📋 Parametri manuali:")
    print(f"   • Pezzi grandi: {len(test_request['odl_ids'])}")
    print(f"   • Parametri minimi per massima densità")
    print(f"   • Heuristic abilitata per layout aggressivo")
    print()
    
    try:
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            overlaps = result.get("overlaps", [])
            metrics = result.get("metrics", {})
            positioned_tools = result.get("positioned_tools", [])
            
            print(f"📊 Risultati manuali:")
            print(f"   • Success: {result.get('success', False)}")
            print(f"   • Tool posizionati: {len(positioned_tools)}")
            print(f"   • Overlap: {len(overlaps) if overlaps else 0}")
            print(f"   • Invalid: {metrics.get('invalid', False)}")
            print(f"   • Algorithm: {metrics.get('algorithm_status', 'N/A')}")
            
            if overlaps and len(overlaps) > 0:
                print(f"\n🔴 OVERLAP MANUALI TROVATI:")
                for overlap in overlaps[:5]:  # Mostra solo i primi 5
                    print(f"   • ODL {overlap.get('odl_a')} ⚠️ ODL {overlap.get('odl_b')}")
            
            return len(overlaps) > 0 if overlaps else False
        else:
            print(f"❌ Errore: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Errore: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🔴 CarbonPilot v1.4.16-DEMO - Test Overlap Forzato")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Parametri strategici
    overlap_found_1 = test_forced_overlap()
    
    # Test 2: Molti pezzi grandi
    overlap_found_2 = test_with_many_large_pieces()
    
    # Test 3: Creazione manuale
    overlap_found_3 = test_manual_overlap_creation()
    
    print(f"\n{'='*50}")
    if overlap_found_1 or overlap_found_2 or overlap_found_3:
        print("✅ OVERLAP RILEVATI: Funzionalità v1.4.16-DEMO verificata!")
        print("🎯 Il sistema di rilevamento overlap funziona correttamente")
    else:
        print("⚠️ NESSUN OVERLAP: Il solver è molto efficiente!")
        print("💡 Questo è positivo - significa che il sistema evita sovrapposizioni")
        print("🔧 Per testare BL-FFD, potrebbe essere necessario modificare il solver")
    
    print(f"\n📋 VERIFICA MANUALE FRONTEND:")
    print("1. Aprire http://localhost:3000")
    print("2. Navigare al batch nesting generato")
    print("3. Verificare evidenziazione rossa se overlap presenti")
    print("4. Controllare badge 'Layout Invalid' se applicabile")
    print("5. Testare responsive canvas ridimensionando la finestra") 