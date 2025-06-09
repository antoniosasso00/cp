#!/usr/bin/env python3
"""
Script di test per verificare le migliorie di efficienza dell'algoritmo nesting
"""

import requests
import json
import time

def test_algorithm_efficiency():
    """Testa l'efficienza del nuovo algoritmo ottimizzato"""
    
    print("🔧 TEST EFFICIENZA REALE - Algoritmo Ottimizzato")
    print("=" * 60)
    
    # Configurazione test
    base_url = "http://localhost:8000"
    
    # Test cases con diversi scenari
    test_cases = [
        {
            "name": "MAROSO - ODL Piccoli",
            "odl_ids": [3, 9],
            "autoclave_id": "MAROSO",
            "expected_min_efficiency": 60.0
        },
        {
            "name": "PANINI - ODL Misti", 
            "odl_ids": [5, 6, 7],
            "autoclave_id": "PANINI",
            "expected_min_efficiency": 70.0
        },
        {
            "name": "ISMAR - ODL Multi",
            "odl_ids": [8, 10, 11],
            "autoclave_id": "ISMAR", 
            "expected_min_efficiency": 65.0
        }
    ]
    
    # Parametri ottimizzati per efficienza reale
    optimized_params = {
        "padding_mm": 0.2,
        "min_distance_mm": 0.2,
        "use_fallback": True,
        "allow_heuristic": True
    }
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔧 TEST {i}/3: {test_case['name']}")
        print(f"   ODL: {test_case['odl_ids']}")
        print(f"   Autoclave: {test_case['autoclave_id']}")
        
        try:
            # Payload per API
            payload = {
                "odl_ids": test_case["odl_ids"],
                "autoclave_id": test_case["autoclave_id"],
                "parameters": optimized_params
            }
            
            # Chiamata API
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/batch_nesting/genera",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                # Estrai metriche
                batch_id = result.get("batch_id", "N/A")
                efficiency = result.get("efficiency", 0)
                positioned_count = result.get("positioned_tools_count", 0)
                total_count = len(test_case["odl_ids"])
                area_pct = result.get("area_percentage", 0)
                algorithm = result.get("algorithm_used", "N/A")
                execution_time = end_time - start_time
                
                # Valutazione risultato
                success = efficiency >= test_case["expected_min_efficiency"]
                status_icon = "✅" if success else "⚠️"
                
                print(f"   {status_icon} EFFICIENZA: {efficiency:.1f}% (Target: {test_case['expected_min_efficiency']:.1f}%+)")
                print(f"   📊 POSIZIONATI: {positioned_count}/{total_count} ODL")
                print(f"   📦 AREA UTILIZZATA: {area_pct:.1f}%")
                print(f"   🚀 ALGORITMO: {algorithm}")
                print(f"   ⏱️ TEMPO: {execution_time:.2f}s")
                print(f"   🆔 BATCH: {batch_id}")
                
                results.append({
                    "test_name": test_case["name"],
                    "efficiency": efficiency,
                    "success": success,
                    "positioned_count": positioned_count,
                    "total_count": total_count,
                    "area_pct": area_pct,
                    "algorithm": algorithm,
                    "execution_time": execution_time,
                    "batch_id": batch_id
                })
                
            else:
                print(f"   ❌ ERRORE API: {response.status_code}")
                print(f"   📄 DETTAGLI: {response.text}")
                
                results.append({
                    "test_name": test_case["name"],
                    "efficiency": 0,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"   ❌ ERRORE: {str(e)}")
            results.append({
                "test_name": test_case["name"],
                "efficiency": 0,
                "success": False,
                "error": str(e)
            })
    
    # Riepilogo finale
    print("\n" + "=" * 60)
    print("🔧 RIEPILOGO RISULTATI TEST EFFICIENZA")
    print("=" * 60)
    
    successful_tests = [r for r in results if r.get("success", False)]
    total_tests = len([r for r in results if "error" not in r])
    
    if total_tests > 0:
        avg_efficiency = sum(r["efficiency"] for r in results if "error" not in r) / total_tests
        max_efficiency = max(r["efficiency"] for r in results if "error" not in r)
        min_efficiency = min(r["efficiency"] for r in results if "error" not in r)
        
        print(f"✅ TEST COMPLETATI: {len(successful_tests)}/{len(test_cases)}")
        print(f"📊 EFFICIENZA MEDIA: {avg_efficiency:.1f}%")
        print(f"🚀 EFFICIENZA MASSIMA: {max_efficiency:.1f}%")
        print(f"⚠️ EFFICIENZA MINIMA: {min_efficiency:.1f}%")
        
        # Valutazione complessiva
        if avg_efficiency >= 70.0:
            print(f"🎯 VALUTAZIONE: OTTIMA - Algoritmo efficienza reale funzionante")
        elif avg_efficiency >= 60.0:
            print(f"🎯 VALUTAZIONE: BUONA - Miglioramenti applicati con successo")  
        elif avg_efficiency >= 40.0:
            print(f"🎯 VALUTAZIONE: MIGLIORABILE - Progresso rispetto al 25% precedente")
        else:
            print(f"🎯 VALUTAZIONE: PROBLEMATICA - Necessarie ulteriori ottimizzazioni")
            
        # Dettagli per test
        print(f"\n📋 DETTAGLI PER TEST:")
        for result in results:
            if "error" not in result:
                status = "✅" if result["success"] else "⚠️"
                print(f"   {status} {result['test_name']}: {result['efficiency']:.1f}% ({result['positioned_count']}/{result['total_count']} ODL)")
            else:
                print(f"   ❌ {result['test_name']}: ERRORE - {result['error']}")
                
    else:
        print("❌ NESSUN TEST COMPLETATO - Verificare stato backend")

if __name__ == "__main__":
    test_algorithm_efficiency() 