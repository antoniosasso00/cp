#!/usr/bin/env python3
"""
🎯 TEST EFFICIENCY OPTIMIZATION v2.0
===================================

Test delle ottimizzazioni implementate per migliorare l'efficienza:
- Padding ridotto: 0.5mm → 0.2mm
- Min distance ridotto: 0.5mm → 0.2mm  
- Eliminazione rotazione forzata ODL 2
- Objective function ribalancerata: 93% area + 5% compactness + 2% balance
- Post-compattazione ultra-aggressiva
- Target realistico: 75%+ vs 25.3% baseline

Testa su autoclavi MAROSO, PANINI, ISMAR con scenari reali.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 120  # 2 minuti timeout per test performance

def test_optimized_efficiency():
    """Test delle ottimizzazioni per efficienza reale"""
    
    print("🎯 TEST EFFICIENCY OPTIMIZATION v2.0")
    print("=" * 50)
    print("🔧 Ottimizzazioni attive:")
    print("   • Padding ultra-aggressivo: 0.2mm")
    print("   • Min distance ridotto: 0.2mm")
    print("   • No rotazione forzata ODL 2")
    print("   • Objective: 93% area + 5% compactness + 2% balance")
    print("   • Post-compattazione con padding 0.1mm")
    print("   • Target efficienza: 75%+ (vs 25.3% baseline)")
    print()
    
    # Test scenarios con parametri ottimizzati
    test_scenarios = [
        {
            "name": "MAROSO Efficienza Reale",
            "autoclave_id": 3,  # Assumendo che MAROSO sia ID 3
            "odl_ids": [1, 2, 3, 4, 5],  # ODL misti per test reale
            "target_efficiency": 60.0,  # Target realistico per MAROSO
            "description": "Test con ODL misti per efficienza reale MAROSO"
        },
        {
            "name": "PANINI Alto Rendimento", 
            "autoclave_id": 1,  # Assumendo che PANINI sia ID 1
            "odl_ids": [2, 4, 5, 6],  # Senza ODL 2 per evitare rotazione forzata
            "target_efficiency": 75.0,  # Target alto per PANINI
            "description": "Test ottimizzato senza rotazione forzata"
        },
        {
            "name": "ISMAR Compattazione",
            "autoclave_id": 2,  # Assumendo che ISMAR sia ID 2
            "odl_ids": [1, 3, 4],  # Test con 3 ODL per compattazione
            "target_efficiency": 70.0,  # Target medio-alto
            "description": "Test compattazione ultra-aggressiva"
        },
        {
            "name": "Multi-ODL Aerospace",
            "autoclave_id": 1,  # PANINI per test multi-ODL
            "odl_ids": None,  # Tutti gli ODL disponibili
            "target_efficiency": 65.0,  # Target realistico per molti ODL
            "description": "Test con tutti gli ODL disponibili"
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"📋 Test: {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Target: {scenario['target_efficiency']:.1f}% efficienza")
        
        # Payload con parametri ottimizzati
        payload = {
            "autoclave_id": scenario["autoclave_id"],
            "odl_ids": scenario["odl_ids"],
            "padding_mm": 0.2,  # 🎯 OTTIMIZZATO: Ultra-aggressivo
            "min_distance_mm": 0.2,  # 🎯 OTTIMIZZATO: Ultra-ridotto
            "vacuum_lines_capacity": 20,  # Massima flessibilità
            "allow_heuristic": True,  # 🚀 GRASP heuristic attiva
            "timeout_override": 90,  # Tempo adeguato per ottimizzazione
            "heavy_piece_threshold_kg": 100.0  # Soglia alta per maggiore libertà
        }
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{API_BASE_URL}/api/batch_nesting/solve",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=API_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                metrics = result.get('metrics', {})
                
                # Estrai metriche chiave
                efficiency = metrics.get('efficiency_score', 0)
                area_pct = metrics.get('area_utilization_pct', 0)
                positioned = metrics.get('pieces_positioned', 0)
                excluded = metrics.get('pieces_excluded', 0)
                algorithm = metrics.get('algorithm_status', 'UNKNOWN')
                time_ms = metrics.get('time_solver_ms', 0)
                fallback_used = metrics.get('fallback_used', False)
                rotation_used = metrics.get('rotation_used', False)
                
                # Valutazione risultato
                success_icon = "✅" if efficiency >= scenario['target_efficiency'] else "⚠️"
                
                print(f"   {success_icon} Risultato:")
                print(f"      Efficienza: {efficiency:.1f}% (target: {scenario['target_efficiency']:.1f}%)")
                print(f"      Area utilizzata: {area_pct:.1f}%")
                print(f"      Tool posizionati: {positioned} (esclusi: {excluded})")
                print(f"      Algoritmo: {algorithm}")
                print(f"      Tempo API: {elapsed:.1f}s, Solver: {time_ms:.0f}ms")
                print(f"      Fallback: {'Sì' if fallback_used else 'No'}")
                print(f"      Rotazione: {'Sì' if rotation_used else 'No'}")
                
                # Analisi miglioramenti
                if efficiency >= scenario['target_efficiency']:
                    improvement = efficiency - 25.3  # vs baseline MAROSO
                    print(f"      🎯 SUCCESSO: +{improvement:.1f}% vs baseline 25.3%")
                else:
                    gap = scenario['target_efficiency'] - efficiency
                    print(f"      📉 Gap target: -{gap:.1f}%")
                
                # Salva risultato
                results.append({
                    'scenario': scenario['name'],
                    'autoclave_id': scenario['autoclave_id'],
                    'efficiency': efficiency,
                    'area_pct': area_pct,
                    'positioned': positioned,
                    'excluded': excluded,
                    'algorithm': algorithm,
                    'success': efficiency >= scenario['target_efficiency'],
                    'improvement': efficiency - 25.3,
                    'api_time': elapsed,
                    'solver_time_ms': time_ms,
                    'fallback_used': fallback_used,
                    'rotation_used': rotation_used
                })
                
            else:
                print(f"   ❌ ERRORE API: {response.status_code}")
                print(f"      Response: {response.text[:200]}...")
                
                results.append({
                    'scenario': scenario['name'],
                    'autoclave_id': scenario['autoclave_id'],
                    'efficiency': 0,
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'api_time': elapsed
                })
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT dopo {API_TIMEOUT}s")
            results.append({
                'scenario': scenario['name'],
                'autoclave_id': scenario['autoclave_id'],
                'efficiency': 0,
                'success': False,
                'error': "API Timeout"
            })
            
        except Exception as e:
            print(f"   ❌ ERRORE: {str(e)}")
            results.append({
                'scenario': scenario['name'],
                'autoclave_id': scenario['autoclave_id'],
                'efficiency': 0,
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # Riepilogo finale
    print("📊 RIEPILOGO OTTIMIZZAZIONI")
    print("=" * 50)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    if successful_tests:
        avg_efficiency = sum(r['efficiency'] for r in successful_tests) / len(successful_tests)
        avg_improvement = sum(r.get('improvement', 0) for r in successful_tests) / len(successful_tests)
        best_result = max(successful_tests, key=lambda x: x['efficiency'])
        
        print(f"✅ TEST RIUSCITI: {len(successful_tests)}/{len(results)}")
        print(f"📈 Efficienza media: {avg_efficiency:.1f}%")
        print(f"🎯 Miglioramento medio: +{avg_improvement:.1f}% vs baseline")
        print(f"🏆 Miglior risultato: {best_result['scenario']} - {best_result['efficiency']:.1f}%")
        
        # Verifica algoritmi utilizzati
        algorithms_used = set(r.get('algorithm', 'N/A') for r in successful_tests)
        fallback_count = sum(1 for r in successful_tests if r.get('fallback_used', False))
        rotation_count = sum(1 for r in successful_tests if r.get('rotation_used', False))
        
        print(f"🔧 Algoritmi: {', '.join(algorithms_used)}")
        print(f"🔄 Fallback utilizzato: {fallback_count}/{len(successful_tests)} volte")
        print(f"🔄 Rotazione utilizzata: {rotation_count}/{len(successful_tests)} volte")
        
        # Valutazione ottimizzazioni
        if avg_efficiency >= 70.0:
            print("🎉 OTTIMIZZAZIONI ECCELLENTI! Target aerospace raggiunto")
        elif avg_efficiency >= 60.0:
            print("✅ OTTIMIZZAZIONI BUONE! Efficienza industriale raggiunta")
        elif avg_efficiency >= 45.0:
            print("⚠️ OTTIMIZZAZIONI MODERATE. Miglioramento significativo ma non target")
        else:
            print("❌ OTTIMIZZAZIONI INSUFFICIENTI. Rivedere parametri")
            
    else:
        print("❌ NESSUN TEST RIUSCITO")
        
    if failed_tests:
        print(f"\n❌ TEST FALLITI: {len(failed_tests)}")
        for test in failed_tests:
            error = test.get('error', 'Errore sconosciuto')
            print(f"   • {test['scenario']}: {error}")
    
    # Salva risultati su file per analisi
    output_file = "efficiency_optimization_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'test_timestamp': time.time(),
            'optimization_version': '2.0',
            'parameters_used': {
                'padding_mm': 0.2,
                'min_distance_mm': 0.2,
                'vacuum_lines_capacity': 20,
                'allow_heuristic': True,
                'timeout_override': 90
            },
            'baseline_efficiency': 25.3,
            'target_efficiency_range': '60-75%',
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Risultati salvati in: {output_file}")
    
    return results

def test_parameter_comparison():
    """Test comparativo tra parametri conservativi e ottimizzati"""
    
    print("\n🔬 TEST COMPARATIVO PARAMETRI")
    print("=" * 40)
    
    # Test su autoclave di riferimento
    autoclave_id = 1  # PANINI
    odl_ids = [2, 4, 5]  # ODL senza problemi di rotazione
    
    # Parametri conservativi (baseline)
    conservative_params = {
        "autoclave_id": autoclave_id,
        "odl_ids": odl_ids,
        "padding_mm": 20,  # Conservativo
        "min_distance_mm": 15,  # Conservativo
        "vacuum_lines_capacity": 10,  # Limitato
        "allow_heuristic": False,  # Disabilitato
        "timeout_override": 30  # Limitato
    }
    
    # Parametri ottimizzati
    optimized_params = {
        "autoclave_id": autoclave_id,
        "odl_ids": odl_ids,
        "padding_mm": 0.2,  # Ultra-aggressivo
        "min_distance_mm": 0.2,  # Ultra-ridotto
        "vacuum_lines_capacity": 20,  # Flessibile
        "allow_heuristic": True,  # Abilitato
        "timeout_override": 90  # Esteso
    }
    
    results = {}
    
    for param_name, params in [("CONSERVATIVI", conservative_params), ("OTTIMIZZATI", optimized_params)]:
        print(f"📋 Test con parametri {param_name}:")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/batch_nesting/solve",
                json=params,
                headers={"Content-Type": "application/json"},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                metrics = result.get('metrics', {})
                
                efficiency = metrics.get('efficiency_score', 0)
                area_pct = metrics.get('area_utilization_pct', 0)
                positioned = metrics.get('pieces_positioned', 0)
                algorithm = metrics.get('algorithm_status', 'UNKNOWN')
                time_ms = metrics.get('time_solver_ms', 0)
                
                print(f"   Efficienza: {efficiency:.1f}%")
                print(f"   Area: {area_pct:.1f}%")
                print(f"   Tool: {positioned}")
                print(f"   Algoritmo: {algorithm}")
                print(f"   Tempo: {time_ms:.0f}ms")
                
                results[param_name] = {
                    'efficiency': efficiency,
                    'area_pct': area_pct,
                    'positioned': positioned,
                    'algorithm': algorithm,
                    'time_ms': time_ms
                }
                
            else:
                print(f"   ❌ ERRORE: {response.status_code}")
                results[param_name] = {'error': response.status_code}
                
        except Exception as e:
            print(f"   ❌ ERRORE: {str(e)}")
            results[param_name] = {'error': str(e)}
        
        print()
    
    # Confronto risultati
    if 'CONSERVATIVI' in results and 'OTTIMIZZATI' in results:
        cons = results['CONSERVATIVI']
        opt = results['OTTIMIZZATI']
        
        if 'efficiency' in cons and 'efficiency' in opt:
            improvement = opt['efficiency'] - cons['efficiency']
            print(f"🎯 MIGLIORAMENTO OTTIMIZZAZIONI:")
            print(f"   Efficienza: +{improvement:.1f}% ({cons['efficiency']:.1f}% → {opt['efficiency']:.1f}%)")
            print(f"   Area: +{opt['area_pct'] - cons['area_pct']:.1f}%")
            print(f"   Tool aggiuntivi: +{opt['positioned'] - cons['positioned']}")
            
            if improvement > 10:
                print("   🎉 MIGLIORAMENTO SIGNIFICATIVO!")
            elif improvement > 5:
                print("   ✅ Miglioramento moderato")
            else:
                print("   ⚠️ Miglioramento limitato")
    
    return results

if __name__ == "__main__":
    try:
        print("🚀 AVVIO TEST EFFICIENCY OPTIMIZATION")
        print("Verifica che il backend sia attivo su localhost:8000...")
        
        # Test connessione API
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Backend non risponde correttamente")
            exit(1)
        
        print("✅ Backend attivo, avvio test...\n")
        
        # Esegui test principali
        optimization_results = test_optimized_efficiency()
        
        # Esegui test comparativo
        comparison_results = test_parameter_comparison()
        
        print("\n🎯 TEST COMPLETATI!")
        print("Verifica i risultati e l'efficienza ottenuta.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotti dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante i test: {str(e)}") 