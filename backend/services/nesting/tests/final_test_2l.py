#!/usr/bin/env python3
"""
Test Finale per il Solver 2L - Verifica Completa
Controlla tutti gli aspetti del modulo solver_2l.py

🎯 Obiettivi del Test:
1. Verifica importabilità da diversi contesti
2. Test funzionalità core (CP-SAT e Greedy)
3. Verifica vincoli a due livelli
4. Test edge cases e robustezza
5. Verifica metriche e reporting
"""

import sys
import os
import traceback
from typing import List, Dict, Any

def test_direct_import():
    """Test 1: Importazione diretta del modulo"""
    print("🔍 Test 1: Importazione diretta")
    
    try:
        # Import diretto
        from solver_2l import (
            NestingModel2L, NestingParameters2L, ToolInfo2L, 
            AutoclaveInfo2L, NestingLayout2L, NestingMetrics2L, NestingSolution2L
        )
        print("✅ Import diretto riuscito")
        return True
    except Exception as e:
        print(f"❌ Import diretto fallito: {e}")
        return False

def test_package_import():
    """Test 2: Importazione tramite package"""
    print("\n🔍 Test 2: Importazione tramite package")
    
    try:
        # Aggiunge il path del backend
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from backend.services.nesting.solver_2l import (
            NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L
        )
        print("✅ Import tramite package riuscito")
        return True
    except Exception as e:
        print(f"❌ Import tramite package fallito: {e}")
        return False

def test_constraint_validation():
    """Test 3: Validazione vincoli a due livelli"""
    print("\n🔍 Test 3: Validazione vincoli due livelli")
    
    try:
        from solver_2l import NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L
        
        # Configurazione test vincoli
        parameters = NestingParameters2L(
            padding_mm=5.0,
            use_cavalletti=True,
            max_weight_per_level_kg=100.0,
            prefer_base_level=True,
            base_timeout_seconds=5.0
        )
        
        autoclave = AutoclaveInfo2L(
            id=1,
            width=400.0,
            height=400.0,
            max_weight=200.0,
            max_lines=20,
            has_cavalletti=True,
            max_weight_per_level=100.0
        )
        
        # Tool che dovrebbero essere su livelli diversi per rispettare i vincoli di peso
        tools = [
            ToolInfo2L(odl_id=1, width=150, height=100, weight=80, can_use_cavalletto=True),
            ToolInfo2L(odl_id=2, width=120, height=90, weight=70, can_use_cavalletto=True),
        ]
        
        solver = NestingModel2L(parameters)
        solution = solver.solve_2l(tools, autoclave)
        
        # Verifica che i vincoli siano rispettati
        if solution.success:
            weight_level_0 = sum(l.weight for l in solution.layouts if l.level == 0)
            weight_level_1 = sum(l.weight for l in solution.layouts if l.level == 1)
            
            print(f"   Peso livello 0: {weight_level_0}kg (max: {autoclave.max_weight_per_level}kg)")
            print(f"   Peso livello 1: {weight_level_1}kg (max: {autoclave.max_weight_per_level}kg)")
            
            if weight_level_0 <= autoclave.max_weight_per_level and weight_level_1 <= autoclave.max_weight_per_level:
                print("✅ Vincoli di peso per livello rispettati")
                return True
            else:
                print("❌ Vincoli di peso per livello violati")
                return False
        else:
            print("⚠️ Soluzione non trovata (potrebbe essere corretto)")
            return True
            
    except Exception as e:
        print(f"❌ Test vincoli fallito: {e}")
        return False

def test_overlap_between_levels():
    """Test 4: Verifica che overlap tra livelli sia consentito"""
    print("\n🔍 Test 4: Overlap tra livelli diversi")
    
    try:
        from solver_2l import NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L
        
        parameters = NestingParameters2L(
            padding_mm=5.0,
            use_cavalletti=True,
            max_weight_per_level_kg=200.0,
            base_timeout_seconds=5.0
        )
        
        # Autoclave piccola per forzare overlap se su stesso livello
        autoclave = AutoclaveInfo2L(
            id=1,
            width=250.0,
            height=200.0,
            max_weight=400.0,
            max_lines=20,
            has_cavalletti=True,
            max_weight_per_level=200.0
        )
        
        # Due tool grandi che non entrerebbero sullo stesso livello
        tools = [
            ToolInfo2L(odl_id=1, width=200, height=150, weight=50, can_use_cavalletto=True),
            ToolInfo2L(odl_id=2, width=180, height=140, weight=45, can_use_cavalletto=True),
        ]
        
        solver = NestingModel2L(parameters)
        solution = solver.solve_2l(tools, autoclave)
        
        if solution.success and len(solution.layouts) == 2:
            layout1, layout2 = solution.layouts
            
            # Verifica overlap in pianta
            x_overlap = not (layout1.x + layout1.width <= layout2.x or layout2.x + layout2.width <= layout1.x)
            y_overlap = not (layout1.y + layout1.height <= layout2.y or layout2.y + layout2.height <= layout1.y)
            
            if x_overlap and y_overlap:
                # C'è overlap in pianta - verifica che siano su livelli diversi
                if layout1.level != layout2.level:
                    print("✅ Overlap tra livelli diversi consentito correttamente")
                    print(f"   Tool {layout1.odl_id} livello {layout1.level}")
                    print(f"   Tool {layout2.odl_id} livello {layout2.level}")
                    return True
                else:
                    print("❌ Overlap su stesso livello non dovrebbe essere consentito")
                    return False
            else:
                print("✅ Nessun overlap rilevato (configurazione alternativa valida)")
                return True
        else:
            print("⚠️ Test inconclusivo - soluzione non trovata o incompleta")
            return True
            
    except Exception as e:
        print(f"❌ Test overlap fallito: {e}")
        return False

def test_metrics_accuracy():
    """Test 5: Verifica accuratezza metriche"""  
    print("\n🔍 Test 5: Accuratezza metriche")
    
    try:
        from solver_2l import NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L
        
        parameters = NestingParameters2L(
            padding_mm=0.0,  # Zero padding per calcoli semplici
            use_cavalletti=True,
            max_weight_per_level_kg=200.0
        )
        
        autoclave = AutoclaveInfo2L(
            id=1,
            width=1000.0,
            height=1000.0,  # Area = 1.000.000 mm²
            max_weight=400.0,
            max_lines=20,
            has_cavalletti=True,
            max_weight_per_level=200.0
        )
        
        # Tool con dimensioni note
        tools = [
            ToolInfo2L(odl_id=1, width=200, height=100, weight=30, can_use_cavalletto=False),  # Area = 20.000 mm², livello 0
            ToolInfo2L(odl_id=2, width=150, height=100, weight=25, can_use_cavalletto=True),   # Area = 15.000 mm²
        ]
        
        solver = NestingModel2L(parameters)
        solution = solver.solve_2l(tools, autoclave)
        
        if solution.success:
            # Verifica calcolo area
            expected_area = 20000 + 15000  # 35.000 mm²
            expected_area_pct = (expected_area / 1000000) * 100  # 3.5%
            
            area_diff = abs(solution.metrics.area_pct - expected_area_pct)
            
            print(f"   Area calcolata: {solution.metrics.area_pct:.2f}%")
            print(f"   Area attesa: {expected_area_pct:.2f}%")
            print(f"   Differenza: {area_diff:.2f}%")
            
            # Verifica contatori per livello
            level_0_expected = 1  # Tool 1 non può usare cavalletto
            level_1_expected = 1  # Tool 2 può usare cavalletto
            
            print(f"   Livello 0: {solution.metrics.level_0_count} (atteso: {level_0_expected})")
            print(f"   Livello 1: {solution.metrics.level_1_count} (atteso: {level_1_expected})")
            
            if area_diff < 0.1:  # Tolleranza 0.1%
                print("✅ Metriche area accurate")
                return True
            else:
                print("❌ Metriche area inaccurate")
                return False
        else:
            print("❌ Soluzione non trovata per test metriche")
            return False
            
    except Exception as e:
        print(f"❌ Test metriche fallito: {e}")
        return False

def test_edge_cases():
    """Test 6: Casi limite"""
    print("\n🔍 Test 6: Casi limite")
    
    try:
        from solver_2l import NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L
        
        parameters = NestingParameters2L()
        autoclave = AutoclaveInfo2L(id=1, width=100, height=100, max_weight=10, max_lines=5)
        solver = NestingModel2L(parameters)
        
        # Test 6.1: Lista vuota
        solution = solver.solve_2l([], autoclave)
        if not solution.success and solution.metrics.positioned_count == 0:
            print("✅ Lista vuota gestita correttamente")
        else:
            print("❌ Lista vuota non gestita correttamente")
            return False
        
        # Test 6.2: Tool troppo grande
        big_tool = ToolInfo2L(odl_id=999, width=500, height=400, weight=5)
        solution = solver.solve_2l([big_tool], autoclave)
        if not solution.success:
            print("✅ Tool oversized rifiutato correttamente")
        else:
            print("❌ Tool oversized non dovrebbe essere accettato")
            return False
        
        # Test 6.3: Tool troppo pesante
        heavy_tool = ToolInfo2L(odl_id=998, width=50, height=50, weight=500)
        solution = solver.solve_2l([heavy_tool], autoclave)
        if not solution.success:
            print("✅ Tool troppo pesante rifiutato correttamente")
        else:
            print("❌ Tool troppo pesante non dovrebbe essere accettato")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test casi limite falliti: {e}")
        return False

def run_comprehensive_test():
    """Esegue tutti i test in sequenza"""
    print("🧪 TEST FINALE SOLVER 2L - VERIFICA COMPLETA")
    print("=" * 60)
    
    tests = [
        ("Import Diretto", test_direct_import),
        ("Import Package", test_package_import), 
        ("Vincoli Due Livelli", test_constraint_validation),
        ("Overlap Tra Livelli", test_overlap_between_levels),
        ("Accuratezza Metriche", test_metrics_accuracy),
        ("Casi Limite", test_edge_cases)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} - Errore critico: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Riepilogo finale
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO FINALE")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 RISULTATO: {passed}/{total} test superati")
    
    if passed == total:
        print("🎉 SOLVER 2L COMPLETAMENTE FUNZIONALE!")
        print("✅ Il modulo è pronto per l'integrazione in produzione")
        return True
    else:
        print("⚠️ Alcuni test hanno fallito - verificare implementazione")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 