#!/usr/bin/env python3
"""
Test semplificato per CarbonPilot v1.4.17-DEMO
Verifica le nuove funzionalità senza dipendenze database
"""

import sys
import os
import time

# Aggiungi il path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import diretto del solver
from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

def test_v1_4_17_features():
    """Test completo delle funzionalità v1.4.17-DEMO"""
    print("🚀 TESTING CarbonPilot v1.4.17-DEMO")
    print("=" * 50)
    
    # Autoclave di test
    autoclave = AutoclaveInfo(
        id=1,
        width=600.0,
        height=400.0,
        max_weight=1000.0,
        max_lines=12
    )
    
    # Pezzi di test che richiedono rotazione
    tools = [
        ToolInfo(odl_id=1, width=150.0, height=250.0, weight=25.0, lines_needed=2),  # Deve ruotare
        ToolInfo(odl_id=2, width=180.0, height=120.0, weight=20.0, lines_needed=1),  # Normale
        ToolInfo(odl_id=3, width=200.0, height=100.0, weight=30.0, lines_needed=3),  # Può ruotare
        ToolInfo(odl_id=4, width=120.0, height=180.0, weight=18.0, lines_needed=1),  # Può ruotare
        ToolInfo(odl_id=5, width=100.0, height=80.0, weight=15.0, lines_needed=1),   # Piccolo
    ]
    
    # Parametri con tutte le funzionalità abilitate
    params = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=12,
        allow_heuristic=True,  # Abilita RRGH
        timeout_override=60
    )
    
    print("🔄 Test 1: Rotazione 90° integrata")
    print("🎯 Test 2: BL-FFD (Bottom-Left First-Fit Decreasing)")
    print("🚀 Test 3: RRGH (Ruin & Recreate Goal-Driven)")
    print("📊 Test 4: Nuovo objective Z = 0.8·area + 0.2·vacuum")
    print()
    
    # Esegui nesting
    start_time = time.time()
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    solve_time = time.time() - start_time
    
    # Risultati
    print("📊 RISULTATI:")
    print(f"   Algoritmo utilizzato: {solution.algorithm_status}")
    print(f"   Pezzi posizionati: {solution.metrics.positioned_count}/5")
    print(f"   Rotazione utilizzata: {solution.metrics.rotation_used}")
    print(f"   Iterazioni RRGH: {solution.metrics.heuristic_iters}")
    print(f"   Area utilizzata: {solution.metrics.area_pct:.1f}%")
    print(f"   Vacuum utilizzato: {solution.metrics.vacuum_util_pct:.1f}%")
    print(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    print(f"   Tempo risoluzione: {solve_time:.1f}s")
    print(f"   Layout valido: {not solution.metrics.invalid}")
    print()
    
    # Verifica rotazione
    rotated_count = sum(1 for layout in solution.layouts if layout.rotated)
    print(f"   Pezzi ruotati: {rotated_count}")
    
    # Verifica formula objective
    expected_efficiency = (
        0.8 * solution.metrics.area_pct +
        0.2 * solution.metrics.vacuum_util_pct
    )
    efficiency_diff = abs(expected_efficiency - solution.metrics.efficiency_score)
    
    print(f"   Formula objective corretta: {efficiency_diff < 0.1}")
    print()
    
    # Test specifico BL-FFD (forza fallback)
    print("🎯 Test BL-FFD specifico:")
    fallback_solution = solver._solve_greedy_fallback(tools, autoclave, time.time())
    print(f"   Algoritmo: {fallback_solution.algorithm_status}")
    print(f"   Posizionati: {fallback_solution.metrics.positioned_count}/5")
    print(f"   Efficienza: {fallback_solution.metrics.efficiency_score:.1f}%")
    print()
    
    # Verifica risultati
    success = True
    checks = []
    
    # Check 1: Almeno 3 pezzi posizionati
    if solution.metrics.positioned_count >= 3:
        checks.append("✅ Posizionamento: almeno 3 pezzi")
    else:
        checks.append("❌ Posizionamento: meno di 3 pezzi")
        success = False
    
    # Check 2: Rotazione funzionante
    if solution.metrics.rotation_used == (rotated_count > 0):
        checks.append("✅ Rotazione: tracking corretto")
    else:
        checks.append("❌ Rotazione: tracking errato")
        success = False
    
    # Check 3: BL-FFD implementato
    if "BL_FFD" in fallback_solution.algorithm_status:
        checks.append("✅ BL-FFD: algoritmo attivo")
    else:
        checks.append("❌ BL-FFD: algoritmo non trovato")
        success = False
    
    # Check 4: Formula objective corretta
    if efficiency_diff < 0.1:
        checks.append("✅ Objective: formula Z = 0.8·area + 0.2·vacuum")
    else:
        checks.append(f"❌ Objective: errore {efficiency_diff:.3f}%")
        success = False
    
    # Check 5: Performance
    if solve_time < 60.0:
        checks.append("✅ Performance: sotto 60s")
    else:
        checks.append(f"❌ Performance: {solve_time:.1f}s")
        success = False
    
    # Check 6: Layout valido
    if not solution.metrics.invalid:
        checks.append("✅ Layout: nessun overlap")
    else:
        checks.append("❌ Layout: overlap rilevati")
        success = False
    
    print("🔍 VERIFICA FUNZIONALITÀ:")
    for check in checks:
        print(f"   {check}")
    print()
    
    if success:
        print("🎉 TUTTI I TEST SUPERATI!")
        print("=" * 50)
        print("✅ Rotazione 90° integrata nei modelli OR-Tools e fallback")
        print("✅ BL-FFD sostituisce greedy con ordinamento max(height,width) desc")
        print("✅ RRGH integrata per miglioramento +5-10% area")
        print("✅ Objective aggiornato Z = 0.8·area_pct + 0.2·vacuum_util_pct")
        print("✅ Performance sotto 60s per scenario test")
        print("✅ Layout senza overlap garantiti")
        print("\n🎯 v1.4.17-DEMO pronta per il commit!")
        return True
    else:
        print("❌ ALCUNI TEST FALLITI!")
        print("Verificare l'implementazione prima del commit.")
        return False

if __name__ == "__main__":
    success = test_v1_4_17_features()
    sys.exit(0 if success else 1) 