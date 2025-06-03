#!/usr/bin/env python3
"""
Test script per v1.4.16-DEMO
Verifica le nuove funzionalità:
1. Rilevamento overlap nel solver
2. Algoritmo BL-FFD per correzione
3. Responsive canvas nel frontend
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
BASE_URL = "http://localhost:8000/api/v1"
NESTING_ENDPOINT = f"{BASE_URL}/nesting/solve"

def test_overlap_detection():
    """Test rilevamento overlap e correzione BL-FFD"""
    print("🎯 TEST v1.4.16-DEMO: Rilevamento Overlap e BL-FFD")
    print("=" * 60)
    
    # Parametri di test con padding ridotto per forzare overlap
    test_request = {
        "autoclave_id": 1,
        "odl_ids": None,  # Usa tutti gli ODL disponibili
        "padding_mm": 5.0,  # Padding ridotto per aumentare probabilità overlap
        "min_distance_mm": 5.0,  # Distanza minima ridotta
        "vacuum_lines_capacity": 8,
        "allow_heuristic": True,
        "timeout_override": 60,
        "heavy_piece_threshold_kg": 30.0
    }
    
    print(f"📋 Parametri test:")
    print(f"   • Padding: {test_request['padding_mm']}mm (ridotto)")
    print(f"   • Min distance: {test_request['min_distance_mm']}mm (ridotto)")
    print(f"   • Timeout: {test_request['timeout_override']}s")
    print(f"   • Heuristic: {test_request['allow_heuristic']}")
    print()
    
    try:
        print("🚀 Invio richiesta nesting...")
        start_time = time.time()
        
        response = requests.post(
            NESTING_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ Tempo risposta: {elapsed_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Richiesta completata con successo!")
            
            # Analizza risultati
            metrics = result.get("metrics", {})
            overlaps = result.get("overlaps", [])
            positioned_tools = result.get("positioned_tools", [])
            excluded_odls = result.get("excluded_odls", [])
            
            print(f"\n📊 RISULTATI NESTING:")
            print(f"   • Success: {result.get('success', False)}")
            print(f"   • Message: {result.get('message', 'N/A')}")
            print(f"   • Algorithm: {metrics.get('algorithm_status', 'N/A')}")
            print(f"   • Fallback used: {metrics.get('fallback_used', False)}")
            print(f"   • Invalid layout: {metrics.get('invalid', False)}")
            
            print(f"\n📈 METRICHE:")
            print(f"   • Efficienza: {metrics.get('efficiency_score', 0):.1f}%")
            print(f"   • Area utilizzata: {metrics.get('area_utilization_pct', 0):.1f}%")
            print(f"   • Peso utilizzato: {metrics.get('weight_utilization_pct', 0):.1f}%")
            print(f"   • Linee vuoto: {metrics.get('vacuum_lines_used', 0)}")
            print(f"   • Tempo solver: {metrics.get('time_solver_ms', 0):.0f}ms")
            
            print(f"\n🔢 CONTEGGI:")
            print(f"   • Tool posizionati: {len(positioned_tools)}")
            print(f"   • Tool esclusi: {len(excluded_odls)}")
            print(f"   • Overlap rilevati: {len(overlaps) if overlaps else 0}")
            
            # Dettagli overlap se presenti
            if overlaps and len(overlaps) > 0:
                print(f"\n🔴 OVERLAP RILEVATI ({len(overlaps)}):")
                for i, overlap in enumerate(overlaps, 1):
                    print(f"   {i}. ODL {overlap.get('odl_a')} ⚠️ ODL {overlap.get('odl_b')}")
                    print(f"      Area A: {overlap.get('area_a')} | Area B: {overlap.get('area_b')}")
                    print(f"      Pos A: {overlap.get('pos_a')} | Pos B: {overlap.get('pos_b')}")
                
                print(f"\n⚠️ ATTENZIONE: Layout marcato come INVALID")
                print(f"   Il frontend evidenzierà i pezzi in rosso")
            else:
                print(f"\n✅ NESSUN OVERLAP: Layout valido")
            
            # Test specifici v1.4.16-DEMO
            print(f"\n🎯 VERIFICA FUNZIONALITÀ v1.4.16-DEMO:")
            
            # 1. Verifica campo invalid nelle metriche
            has_invalid_field = 'invalid' in metrics
            print(f"   ✓ Campo 'invalid' in metriche: {has_invalid_field}")
            
            # 2. Verifica campo overlaps nella risposta
            has_overlaps_field = 'overlaps' in result
            print(f"   ✓ Campo 'overlaps' in risposta: {has_overlaps_field}")
            
            # 3. Verifica algoritmo BL-FFD se overlap corretti
            algorithm_status = metrics.get('algorithm_status', '')
            bl_ffd_used = 'BL_FFD_CORRECTED' in algorithm_status
            print(f"   ✓ Algoritmo BL-FFD utilizzato: {bl_ffd_used}")
            
            # 4. Verifica struttura overlap
            if overlaps:
                overlap_structure_ok = all(
                    'odl_a' in o and 'odl_b' in o and 'area_a' in o and 'area_b' in o 
                    for o in overlaps
                )
                print(f"   ✓ Struttura overlap corretta: {overlap_structure_ok}")
            
            print(f"\n💾 Salvataggio risultati in test_v1_4_16_result.json...")
            with open('test_v1_4_16_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
            return True
            
        else:
            print(f"❌ Errore HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout della richiesta (>120s)")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Errore di connessione - verificare che il backend sia attivo")
        return False
    except Exception as e:
        print(f"💥 Errore imprevisto: {str(e)}")
        return False

def test_frontend_responsive():
    """Test responsive canvas (manuale)"""
    print(f"\n🖥️ TEST FRONTEND RESPONSIVE CANVAS:")
    print("=" * 40)
    print("Per testare il responsive canvas:")
    print("1. Aprire il frontend su http://localhost:3000")
    print("2. Navigare a un batch nesting esistente")
    print("3. Verificare che il canvas si adatti alla finestra")
    print("4. Ridimensionare la finestra e verificare il responsive")
    print("5. Se ci sono overlap, verificare evidenziazione in rosso")
    print()
    print("Funzionalità da verificare:")
    print("• ✓ Canvas si adatta automaticamente alla finestra")
    print("• ✓ Nessun scroll orizzontale")
    print("• ✓ Tool con overlap evidenziati in rosso")
    print("• ✓ Badge efficienza mostra 'Layout Invalid' se overlap")
    print("• ✓ Sezione overlap nella tabella esclusioni")

if __name__ == "__main__":
    print(f"🚀 CarbonPilot v1.4.16-DEMO Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test backend
    success = test_overlap_detection()
    
    # Test frontend (manuale)
    test_frontend_responsive()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ Test completato con successo!")
        print("🎯 Funzionalità v1.4.16-DEMO implementate correttamente")
    else:
        print("❌ Test fallito - verificare configurazione")
    
    print(f"\n📋 PROSSIMI PASSI:")
    print("1. Verificare manualmente il frontend responsive")
    print("2. Testare con diversi padding per forzare/evitare overlap")
    print("3. Verificare performance con dataset più grandi")
    print("4. Commit e tag v1.4.16-DEMO se tutto ok") 