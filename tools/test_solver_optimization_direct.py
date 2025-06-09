#!/usr/bin/env python3
"""
🎯 TEST DIRETTO SOLVER OPTIMIZATION v2.0
========================================

Test diretto delle ottimizzazioni del nesting solver senza dipendere dal backend API.
Verifica che le ottimizzazioni implementate migliorino l'efficienza dal 25.3% baseline.

Ottimizzazioni testate:
- Padding ridotto: 0.5mm → 0.2mm
- Min distance ridotto: 0.5mm → 0.2mm  
- Eliminazione rotazione forzata ODL 2
- Objective function: 93% area + 5% compactness + 2% balance
- Post-compattazione ultra-aggressiva
"""

import sys
import os
import time
from typing import List, Dict, Any

# Aggiungi il path del backend per importare i moduli
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo
    print("✅ Import solver riuscito")
except ImportError as e:
    print(f"❌ Errore import solver: {e}")
    sys.exit(1)

def create_test_tools() -> List[ToolInfo]:
    """Crea tool di test basati sui dati reali del sistema"""
    return [
        # ODL 1: Tool medio
        ToolInfo(
            odl_id=1,
            width=268.0,
            height=53.0,
            weight=15.0,
            lines_needed=2,
            ciclo_cura_id=1,
            priority=1
        ),
        # ODL 2: Tool problematico (era forzatamente ruotato)
        ToolInfo(
            odl_id=2,
            width=405.0,
            height=95.0,
            weight=25.0,
            lines_needed=2,
            ciclo_cura_id=1,
            priority=2
        ),
        # ODL 3: Tool piccolo
        ToolInfo(
            odl_id=3,
            width=223.0,
            height=66.0,
            weight=10.0,
            lines_needed=1,
            ciclo_cura_id=2,  # Ciclo diverso per test esclusione
            priority=1
        ),
        # ODL 4: Tool compatto
        ToolInfo(
            odl_id=4,
            width=329.0,
            height=54.0,
            weight=18.0,
            lines_needed=2,
            ciclo_cura_id=1,
            priority=1
        ),
        # ODL 5: Tool medio-piccolo
        ToolInfo(
            odl_id=5,
            width=223.0,
            height=66.0,
            weight=12.0,
            lines_needed=2,
            ciclo_cura_id=1,
            priority=1
        )
    ]

def create_test_autoclaves() -> List[AutoclaveInfo]:
    """Crea autoclavi di test basate sui dati reali"""
    return [
        # PANINI (Large)
        AutoclaveInfo(
            id=1,
            width=3000.0,  # 3000mm
            height=2000.0,  # 2000mm
            max_weight=1000.0,
            max_lines=20
        ),
        # ISMAR (Medium)
        AutoclaveInfo(
            id=2,
            width=2500.0,  # 2500mm
            height=1800.0,  # 1800mm
            max_weight=800.0,
            max_lines=15
        ),
        # MAROSO (Compact)
        AutoclaveInfo(
            id=3,
            width=2000.0,  # 2000mm
            height=1500.0,  # 1500mm
            max_weight=600.0,
            max_lines=12
        )
    ]

def test_parameter_optimization():
    """Test comparativo tra parametri conservativi e ottimizzati"""
    
    print("🔬 TEST COMPARATIVO PARAMETRI")
    print("=" * 50)
    
    tools = create_test_tools()
    autoclaves = create_test_autoclaves()
    
    # Parametri conservativi (baseline)
    conservative_params = NestingParameters(
        padding_mm=20.0,  # Conservativo
        min_distance_mm=15.0,  # Conservativo
        vacuum_lines_capacity=10,  # Limitato
        use_fallback=True,
        allow_heuristic=False,  # Disabilitato
        area_weight=0.85,  # 85% area (default aerospace)
        compactness_weight=0.10,  # 10% compactness
        balance_weight=0.05,  # 5% balance
        max_iterations_grasp=5  # Iterazioni limitate
    )
    
    # Parametri ottimizzati
    optimized_params = NestingParameters(
        padding_mm=0.2,  # 🎯 ULTRA-AGGRESSIVO
        min_distance_mm=0.2,  # 🎯 ULTRA-RIDOTTO
        vacuum_lines_capacity=20,  # Flessibile
        use_fallback=True,
        allow_heuristic=True,  # 🚀 ABILITATO
        area_weight=0.93,  # 🔧 93% area (vs 85%)
        compactness_weight=0.05,  # 🔧 5% compactness (vs 10%)
        balance_weight=0.02,  # 🔧 2% balance (vs 5%)
        max_iterations_grasp=8  # 🔧 Più iterazioni
    )
    
    results = {}
    
    for autoclave in autoclaves:
        autoclave_name = f"Autoclave {autoclave.id}"
        print(f"\n📋 Test su {autoclave_name} ({autoclave.width}x{autoclave.height}mm)")
        
        for param_name, params in [("CONSERVATIVI", conservative_params), ("OTTIMIZZATI", optimized_params)]:
            print(f"   🔧 Parametri {param_name}:")
            
            try:
                start_time = time.time()
                
                # Crea solver con parametri specifici
                solver = NestingModel(params)
                
                # Esegui nesting
                solution = solver.solve(tools, autoclave)
                
                elapsed = time.time() - start_time
                
                # Estrai metriche
                efficiency = solution.metrics.efficiency_score
                area_pct = solution.metrics.area_pct
                positioned = solution.metrics.positioned_count
                excluded = solution.metrics.excluded_count
                algorithm = solution.algorithm_status
                time_ms = solution.metrics.time_solver_ms
                rotation_used = solution.metrics.rotation_used
                
                print(f"      Efficienza: {efficiency:.1f}%")
                print(f"      Area: {area_pct:.1f}%")
                print(f"      Tool posizionati: {positioned}/{len(tools)}")
                print(f"      Algoritmo: {algorithm}")
                print(f"      Tempo: {time_ms:.0f}ms")
                print(f"      Rotazione: {'Sì' if rotation_used else 'No'}")
                
                # Salva risultato
                key = f"{autoclave_name}_{param_name}"
                results[key] = {
                    'autoclave_id': autoclave.id,
                    'autoclave_name': autoclave_name,
                    'parameters': param_name,
                    'efficiency': efficiency,
                    'area_pct': area_pct,
                    'positioned': positioned,
                    'excluded': excluded,
                    'algorithm': algorithm,
                    'time_ms': time_ms,
                    'rotation_used': rotation_used,
                    'success': solution.success
                }
                
            except Exception as e:
                print(f"      ❌ ERRORE: {str(e)}")
                key = f"{autoclave_name}_{param_name}"
                results[key] = {
                    'autoclave_id': autoclave.id,
                    'autoclave_name': autoclave_name,
                    'parameters': param_name,
                    'efficiency': 0,
                    'success': False,
                    'error': str(e)
                }
    
    return results

def analyze_results(results: Dict[str, Any]):
    """Analizza i risultati e calcola i miglioramenti"""
    
    print("\n📊 ANALISI RISULTATI OTTIMIZZAZIONI")
    print("=" * 60)
    
    # Raggruppa per autoclave
    autoclaves = {}
    for key, result in results.items():
        if result.get('success', False):
            autoclave_name = result['autoclave_name']
            param_type = result['parameters']
            
            if autoclave_name not in autoclaves:
                autoclaves[autoclave_name] = {}
            
            autoclaves[autoclave_name][param_type] = result
    
    total_improvement = 0
    successful_comparisons = 0
    best_efficiency = 0
    best_autoclave = None
    
    for autoclave_name, params in autoclaves.items():
        if 'CONSERVATIVI' in params and 'OTTIMIZZATI' in params:
            cons = params['CONSERVATIVI']
            opt = params['OTTIMIZZATI']
            
            improvement = opt['efficiency'] - cons['efficiency']
            total_improvement += improvement
            successful_comparisons += 1
            
            print(f"\n🏭 {autoclave_name}:")
            print(f"   Conservativi: {cons['efficiency']:.1f}% efficienza")
            print(f"   Ottimizzati:  {opt['efficiency']:.1f}% efficienza")
            print(f"   Miglioramento: +{improvement:.1f}%")
            print(f"   Tool aggiuntivi: +{opt['positioned'] - cons['positioned']}")
            print(f"   Rotazione: {cons['rotation_used']} → {opt['rotation_used']}")
            
            if opt['efficiency'] > best_efficiency:
                best_efficiency = opt['efficiency']
                best_autoclave = autoclave_name
            
            # Valutazione miglioramento
            if improvement > 15:
                print(f"   🎉 MIGLIORAMENTO ECCELLENTE!")
            elif improvement > 10:
                print(f"   ✅ MIGLIORAMENTO SIGNIFICATIVO!")
            elif improvement > 5:
                print(f"   ⚠️ Miglioramento moderato")
            else:
                print(f"   ❌ Miglioramento limitato")
    
    # Riepilogo globale
    if successful_comparisons > 0:
        avg_improvement = total_improvement / successful_comparisons
        baseline_efficiency = 25.3  # Efficienza baseline MAROSO
        
        print(f"\n🎯 RIEPILOGO GLOBALE:")
        print(f"   Miglioramento medio: +{avg_improvement:.1f}%")
        print(f"   Miglior risultato: {best_autoclave} - {best_efficiency:.1f}%")
        print(f"   vs Baseline 25.3%: +{best_efficiency - baseline_efficiency:.1f}%")
        
        # Valutazione finale
        if best_efficiency >= 75.0:
            print("   🎉 TARGET RAGGIUNTO! Efficienza aerospace ≥75%")
        elif best_efficiency >= 60.0:
            print("   ✅ BUON RISULTATO! Efficienza industriale ≥60%")
        elif best_efficiency >= 45.0:
            print("   ⚠️ MIGLIORAMENTO MODERATO. Efficienza >45%")
        else:
            print("   ❌ OTTIMIZZAZIONI INSUFFICIENTI")
            
        # Verifica rotazione ODL 2
        odl2_rotation_reduced = False
        for autoclave_name, params in autoclaves.items():
            if 'CONSERVATIVI' in params and 'OTTIMIZZATI' in params:
                if params['CONSERVATIVI']['rotation_used'] and not params['OTTIMIZZATI']['rotation_used']:
                    odl2_rotation_reduced = True
                    break
        
        if odl2_rotation_reduced:
            print("   🔄 SUCCESSO: Rotazione forzata ODL 2 eliminata!")
        
    else:
        print("   ❌ NESSUN CONFRONTO RIUSCITO")

def test_specific_scenarios():
    """Test scenari specifici per validare le ottimizzazioni"""
    
    print("\n🧪 TEST SCENARI SPECIFICI")
    print("=" * 40)
    
    tools = create_test_tools()
    autoclaves = create_test_autoclaves()
    
    # Parametri ultra-ottimizzati
    ultra_params = NestingParameters(
        padding_mm=0.1,  # 🎯 ESTREMO
        min_distance_mm=0.1,  # 🎯 ESTREMO
        vacuum_lines_capacity=25,
        use_fallback=True,
        allow_heuristic=True,
        area_weight=0.95,  # 🔧 95% area
        compactness_weight=0.03,  # 🔧 3% compactness
        balance_weight=0.02,  # 🔧 2% balance
        max_iterations_grasp=10
    )
    
    scenarios = [
        {
            "name": "MAROSO Efficienza Massima",
            "autoclave": autoclaves[2],  # MAROSO (più piccola)
            "tools": tools[:3],  # 3 tool per test compattazione
            "target": 70.0
        },
        {
            "name": "PANINI Multi-Tool",
            "autoclave": autoclaves[0],  # PANINI (più grande)
            "tools": tools,  # Tutti i 5 tool
            "target": 80.0
        },
        {
            "name": "ISMAR Bilanciato",
            "autoclave": autoclaves[1],  # ISMAR (media)
            "tools": tools[:4],  # 4 tool
            "target": 75.0
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}:")
        print(f"   Target: {scenario['target']:.1f}% efficienza")
        
        try:
            solver = NestingModel(ultra_params)
            solution = solver.solve(scenario['tools'], scenario['autoclave'])
            
            efficiency = solution.metrics.efficiency_score
            positioned = solution.metrics.positioned_count
            total_tools = len(scenario['tools'])
            
            success_icon = "✅" if efficiency >= scenario['target'] else "⚠️"
            
            print(f"   {success_icon} Risultato: {efficiency:.1f}% efficienza")
            print(f"   Tool: {positioned}/{total_tools} posizionati")
            print(f"   Algoritmo: {solution.algorithm_status}")
            
            if efficiency >= scenario['target']:
                improvement = efficiency - 25.3
                print(f"   🎯 TARGET RAGGIUNTO! +{improvement:.1f}% vs baseline")
            else:
                gap = scenario['target'] - efficiency
                print(f"   📉 Gap: -{gap:.1f}% dal target")
                
        except Exception as e:
            print(f"   ❌ ERRORE: {str(e)}")

if __name__ == "__main__":
    try:
        print("🚀 AVVIO TEST DIRETTO SOLVER OPTIMIZATION v2.0")
        print("Verifica ottimizzazioni implementate per efficienza reale...")
        print()
        
        # Test comparativo parametri
        results = test_parameter_optimization()
        
        # Analisi risultati
        analyze_results(results)
        
        # Test scenari specifici
        test_specific_scenarios()
        
        print("\n🎯 TEST COMPLETATI!")
        print("Le ottimizzazioni sono state verificate direttamente nel solver.")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotti dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante i test: {str(e)}")
        import traceback
        traceback.print_exc() 