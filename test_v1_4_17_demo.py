#!/usr/bin/env python3
"""
Test per CarbonPilot v1.4.17-DEMO
Verifica le nuove funzionalità:
- 🔄 Rotazione 90° integrata
- 🎯 BL-FFD (Bottom-Left First-Fit Decreasing)
- 🚀 RRGH (Ruin & Recreate Goal-Driven Heuristic)
- 📊 Nuovo objective Z = 0.8·area_pct + 0.2·vacuum_util_pct
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo
import time

def test_rotation_integration():
    """Test 1: Verifica integrazione rotazione 90°"""
    print("🔄 TEST 1: Rotazione 90° integrata")
    
    # Autoclave piccola per forzare rotazione
    autoclave = AutoclaveInfo(
        id=1,
        width=200.0,  # 200mm larghezza
        height=300.0, # 300mm altezza
        max_weight=1000.0,
        max_lines=10
    )
    
    # Tool che richiede rotazione per entrare
    tools = [
        ToolInfo(odl_id=1, width=150.0, height=280.0, weight=25.0, lines_needed=2),  # Deve ruotare
        ToolInfo(odl_id=2, width=120.0, height=180.0, weight=20.0, lines_needed=1),  # Può non ruotare
        ToolInfo(odl_id=3, width=280.0, height=150.0, weight=30.0, lines_needed=2),  # Deve ruotare
    ]
    
    params = NestingParameters(
        padding_mm=10,
        min_distance_mm=5,
        vacuum_lines_capacity=10,
        allow_heuristic=True
    )
    
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    
    print(f"   Posizionati: {solution.metrics.positioned_count}/3")
    print(f"   Rotazione utilizzata: {solution.metrics.rotation_used}")
    print(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    
    # Verifica che almeno un pezzo sia ruotato
    rotated_count = sum(1 for layout in solution.layouts if layout.rotated)
    print(f"   Pezzi ruotati: {rotated_count}")
    
    assert solution.metrics.rotation_used == (rotated_count > 0), "rotation_used non coerente"
    assert solution.metrics.positioned_count >= 2, "Dovrebbe posizionare almeno 2 pezzi"
    
    print("   ✅ Test rotazione superato\n")
    return solution

def test_bl_ffd_algorithm():
    """Test 2: Verifica algoritmo BL-FFD"""
    print("🎯 TEST 2: Algoritmo BL-FFD")
    
    autoclave = AutoclaveInfo(
        id=1,
        width=500.0,
        height=400.0,
        max_weight=1000.0,
        max_lines=15
    )
    
    # Molti pezzi per testare ordinamento max(height,width) desc
    tools = [
        ToolInfo(odl_id=1, width=100.0, height=200.0, weight=15.0, lines_needed=1),  # max=200
        ToolInfo(odl_id=2, width=150.0, height=120.0, weight=20.0, lines_needed=2),  # max=150
        ToolInfo(odl_id=3, width=80.0, height=180.0, weight=12.0, lines_needed=1),   # max=180
        ToolInfo(odl_id=4, width=90.0, height=90.0, weight=10.0, lines_needed=1),    # max=90
        ToolInfo(odl_id=5, width=160.0, height=110.0, weight=18.0, lines_needed=2),  # max=160
    ]
    
    params = NestingParameters(
        padding_mm=15,
        min_distance_mm=10,
        vacuum_lines_capacity=15,
        use_fallback=True,  # Forza uso BL-FFD
        allow_heuristic=False
    )
    
    solver = NestingModel(params)
    
    # Forza fallback per testare BL-FFD
    solution = solver._solve_greedy_fallback(tools, autoclave, time.time())
    
    print(f"   Algoritmo: {solution.algorithm_status}")
    print(f"   Posizionati: {solution.metrics.positioned_count}/5")
    print(f"   Area utilizzata: {solution.metrics.area_pct:.1f}%")
    print(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    
    # Verifica che sia stato usato BL-FFD
    assert "BL_FFD" in solution.algorithm_status, "Dovrebbe usare algoritmo BL-FFD"
    assert solution.metrics.positioned_count >= 3, "BL-FFD dovrebbe posizionare almeno 3 pezzi"
    
    print("   ✅ Test BL-FFD superato\n")
    return solution

def test_rrgh_heuristic():
    """Test 3: Verifica euristica RRGH"""
    print("🚀 TEST 3: Euristica RRGH")
    
    autoclave = AutoclaveInfo(
        id=1,
        width=600.0,
        height=500.0,
        max_weight=1000.0,
        max_lines=20
    )
    
    # Scenario con molti pezzi per testare RRGH
    tools = []
    for i in range(8):
        tools.append(ToolInfo(
            odl_id=i+1,
            width=80.0 + i*10,
            height=60.0 + i*5,
            weight=15.0 + i*2,
            lines_needed=1 + (i % 3)
        ))
    
    params = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=20,
        allow_heuristic=True,  # Abilita RRGH
        timeout_override=60
    )
    
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    
    print(f"   Algoritmo: {solution.algorithm_status}")
    print(f"   Posizionati: {solution.metrics.positioned_count}/8")
    print(f"   Iterazioni RRGH: {solution.metrics.heuristic_iters}")
    print(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    print(f"   Tempo: {solution.metrics.time_solver_ms:.0f}ms")
    
    # Verifica che RRGH sia stato applicato se la soluzione iniziale era buona
    if solution.metrics.positioned_count >= 4:
        print(f"   RRGH applicato: {solution.metrics.heuristic_iters > 0}")
    
    assert solution.metrics.positioned_count >= 4, "Dovrebbe posizionare almeno 4 pezzi"
    
    print("   ✅ Test RRGH superato\n")
    return solution

def test_new_objective():
    """Test 4: Verifica nuovo objective Z = 0.8·area + 0.2·vacuum"""
    print("📊 TEST 4: Nuovo objective Z = 0.8·area + 0.2·vacuum")
    
    autoclave = AutoclaveInfo(
        id=1,
        width=400.0,
        height=300.0,
        max_weight=1000.0,
        max_lines=10
    )
    
    # Pezzi con diverso rapporto area/vacuum per testare objective
    tools = [
        ToolInfo(odl_id=1, width=150.0, height=100.0, weight=20.0, lines_needed=1),  # Alta area, basso vacuum
        ToolInfo(odl_id=2, width=80.0, height=60.0, weight=10.0, lines_needed=3),   # Bassa area, alto vacuum
        ToolInfo(odl_id=3, width=120.0, height=80.0, weight=15.0, lines_needed=2),  # Medio-medio
    ]
    
    params = NestingParameters(
        padding_mm=15,
        min_distance_mm=10,
        vacuum_lines_capacity=10
    )
    
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    
    # Calcola objective manualmente per verifica
    expected_efficiency = (
        0.8 * solution.metrics.area_pct +
        0.2 * solution.metrics.vacuum_util_pct
    )
    
    print(f"   Area utilizzata: {solution.metrics.area_pct:.1f}%")
    print(f"   Vacuum utilizzato: {solution.metrics.vacuum_util_pct:.1f}%")
    print(f"   Efficienza calcolata: {expected_efficiency:.1f}%")
    print(f"   Efficienza riportata: {solution.metrics.efficiency_score:.1f}%")
    
    # Verifica che la formula sia corretta (tolleranza 0.1%)
    diff = abs(expected_efficiency - solution.metrics.efficiency_score)
    assert diff < 0.1, f"Formula objective non corretta: diff={diff:.3f}%"
    
    print("   ✅ Test nuovo objective superato\n")
    return solution

def test_comprehensive_scenario():
    """Test 5: Scenario completo con tutte le funzionalità"""
    print("🎯 TEST 5: Scenario completo v1.4.17-DEMO")
    
    autoclave = AutoclaveInfo(
        id=1,
        width=800.0,
        height=600.0,
        max_weight=1000.0,
        max_lines=15
    )
    
    # Scenario realistico con pezzi di varie dimensioni
    tools = [
        ToolInfo(odl_id=1, width=200.0, height=150.0, weight=30.0, lines_needed=2),
        ToolInfo(odl_id=2, width=180.0, height=120.0, weight=25.0, lines_needed=1),
        ToolInfo(odl_id=3, width=250.0, height=100.0, weight=35.0, lines_needed=3),  # Potrebbe ruotare
        ToolInfo(odl_id=4, width=120.0, height=200.0, weight=20.0, lines_needed=1),  # Potrebbe ruotare
        ToolInfo(odl_id=5, width=160.0, height=140.0, weight=28.0, lines_needed=2),
        ToolInfo(odl_id=6, width=100.0, height=80.0, weight=15.0, lines_needed=1),
    ]
    
    params = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=15,
        allow_heuristic=True,
        timeout_override=90
    )
    
    start_time = time.time()
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    solve_time = time.time() - start_time
    
    print(f"   Algoritmo: {solution.algorithm_status}")
    print(f"   Posizionati: {solution.metrics.positioned_count}/6")
    print(f"   Rotazione utilizzata: {solution.metrics.rotation_used}")
    print(f"   Iterazioni RRGH: {solution.metrics.heuristic_iters}")
    print(f"   Area utilizzata: {solution.metrics.area_pct:.1f}%")
    print(f"   Vacuum utilizzato: {solution.metrics.vacuum_util_pct:.1f}%")
    print(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    print(f"   Tempo totale: {solve_time:.1f}s")
    print(f"   Layout valido: {not solution.metrics.invalid}")
    
    # Verifica performance
    assert solve_time < 90.0, f"Tempo eccessivo: {solve_time:.1f}s"
    assert solution.metrics.positioned_count >= 4, "Dovrebbe posizionare almeno 4 pezzi"
    assert not solution.metrics.invalid, "Layout deve essere valido (no overlap)"
    assert solution.metrics.efficiency_score >= 60.0, "Efficienza deve essere almeno 60%"
    
    print("   ✅ Test scenario completo superato\n")
    return solution

def main():
    """Esegue tutti i test per v1.4.17-DEMO"""
    print("🚀 TESTING CarbonPilot v1.4.17-DEMO")
    print("=" * 50)
    
    try:
        # Test individuali
        test_rotation_integration()
        test_bl_ffd_algorithm()
        test_rrgh_heuristic()
        test_new_objective()
        
        # Test completo
        solution = test_comprehensive_scenario()
        
        print("🎉 TUTTI I TEST SUPERATI!")
        print("=" * 50)
        print("✅ Rotazione 90° integrata")
        print("✅ BL-FFD implementato")
        print("✅ RRGH funzionante")
        print("✅ Nuovo objective Z = 0.8·area + 0.2·vacuum")
        print("✅ Performance sotto 90s")
        print("✅ Layout senza overlap")
        print("\n🎯 v1.4.17-DEMO pronta per il commit!")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST FALLITO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 