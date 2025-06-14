#!/usr/bin/env python3
"""
Test script per il Solver 2L (Nesting a Due Livelli)
Verifica l'importabilità e il funzionamento base del nuovo modulo
"""

import sys
import os

# Aggiunge il path del backend per gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_import():
    """Test di importazione del modulo"""
    try:
        from backend.services.nesting.solver_2l import (
            NestingModel2L, 
            NestingParameters2L, 
            ToolInfo2L, 
            AutoclaveInfo2L,
            NestingLayout2L,
            NestingMetrics2L,
            NestingSolution2L
        )
        print("✅ Import del modulo solver_2l riuscito")
        return True
    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False

def test_basic_functionality():
    """Test delle funzionalità base"""
    try:
        from backend.services.nesting.solver_2l import (
            NestingModel2L, 
            NestingParameters2L, 
            ToolInfo2L, 
            AutoclaveInfo2L
        )
        
        print("\n🔧 Test funzionalità base...")
        
        # 1. Test creazione parametri
        parameters = NestingParameters2L(
            padding_mm=10.0,
            use_cavalletti=True,
            cavalletto_height_mm=100.0,
            max_weight_per_level_kg=200.0
        )
        print("✅ Creazione NestingParameters2L")
        
        # 2. Test creazione autoclave
        autoclave = AutoclaveInfo2L(
            id=1,
            width=1000.0,
            height=800.0,
            max_weight=400.0,
            max_lines=25,
            has_cavalletti=True,
            cavalletto_height=100.0,
            max_weight_per_level=200.0
        )
        print("✅ Creazione AutoclaveInfo2L")
        
        # 3. Test creazione tool
        tool = ToolInfo2L(
            odl_id=1,
            width=200.0,
            height=150.0,
            weight=50.0,
            can_use_cavalletto=True
        )
        print("✅ Creazione ToolInfo2L")
        print(f"   Area tool: {tool.area:.1f}mm²")
        print(f"   Aspect ratio: {tool.aspect_ratio:.2f}")
        
        # 4. Test creazione solver
        solver = NestingModel2L(parameters)
        print("✅ Creazione NestingModel2L")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test funzionalità: {e}")
        return False

def test_simple_solve():
    """Test di risoluzione semplice"""
    try:
        from backend.services.nesting.solver_2l import (
            NestingModel2L, 
            NestingParameters2L, 
            ToolInfo2L, 
            AutoclaveInfo2L
        )
        
        print("\n🚀 Test risoluzione semplice...")
        
        # Parametri conservativi per test
        parameters = NestingParameters2L(
            padding_mm=5.0,
            use_cavalletti=True,
            max_weight_per_level_kg=100.0,
            prefer_base_level=True,
            base_timeout_seconds=10.0  # Timeout breve per test
        )
        
        # Autoclave di test
        autoclave = AutoclaveInfo2L(
            id=1,
            width=800.0,
            height=600.0,
            max_weight=200.0,
            max_lines=20,
            has_cavalletti=True,
            max_weight_per_level=100.0
        )
        
        # Tool semplici per test
        tools = [
            ToolInfo2L(odl_id=1, width=150, height=100, weight=20, can_use_cavalletto=True),
            ToolInfo2L(odl_id=2, width=120, height=80, weight=15, can_use_cavalletto=True),
        ]
        
        print(f"   Autoclave: {autoclave.width}x{autoclave.height}mm")
        print(f"   Cavalletti: {'Sì' if autoclave.has_cavalletti else 'No'}")
        print(f"   Tool: {len(tools)} pezzi")
        
        # Risoluzione
        solver = NestingModel2L(parameters)
        solution = solver.solve_2l(tools, autoclave)
        
        # Verifica risultato
        print(f"\n📊 Risultati test:")
        print(f"   Successo: {solution.success}")
        print(f"   Algoritmo: {solution.algorithm_status}")
        print(f"   Tool posizionati: {solution.metrics.positioned_count}/{len(tools)}")
        print(f"   Efficienza: {solution.metrics.area_pct:.1f}%")
        print(f"   Tempo: {solution.metrics.time_solver_ms:.1f}ms")
        print(f"   Livello 0: {solution.metrics.level_0_count} tool")
        print(f"   Livello 1: {solution.metrics.level_1_count} tool")
        print(f"   Messaggio: {solution.message}")
        
        if solution.layouts:
            print(f"\n📋 Posizionamenti:")
            for layout in solution.layouts:
                print(f"     ODL {layout.odl_id}: ({layout.x:.1f},{layout.y:.1f}) "
                      f"{layout.width:.1f}x{layout.height:.1f}mm L{layout.level}")
        
        return solution.success
        
    except Exception as e:
        print(f"❌ Errore test risoluzione: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test casi limite"""
    try:
        from backend.services.nesting.solver_2l import (
            NestingModel2L, 
            NestingParameters2L, 
            ToolInfo2L, 
            AutoclaveInfo2L
        )
        
        print("\n🔬 Test casi limite...")
        
        parameters = NestingParameters2L(use_cavalletti=False)  # Senza cavalletti
        
        # Autoclave piccola
        autoclave = AutoclaveInfo2L(
            id=1,
            width=200.0,
            height=200.0,
            max_weight=50.0,
            max_lines=5,
            has_cavalletti=False
        )
        
        # 1. Test con lista vuota
        solver = NestingModel2L(parameters)
        solution = solver.solve_2l([], autoclave)
        print(f"   Lista vuota: {solution.success} (atteso: False)")
        
        # 2. Test con tool troppo grande
        big_tool = ToolInfo2L(odl_id=999, width=500, height=400, weight=10)
        solution = solver.solve_2l([big_tool], autoclave)
        print(f"   Tool oversize: {solution.success} (atteso: False)")
        
        # 3. Test con tool che entra
        small_tool = ToolInfo2L(odl_id=1, width=100, height=80, weight=5)
        solution = solver.solve_2l([small_tool], autoclave)
        print(f"   Tool normale: {solution.success} (atteso: True)")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test casi limite: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("🧪 Test Suite per Solver 2L (Nesting a Due Livelli)")
    print("=" * 60)
    
    tests = [
        ("Import modulo", test_import),
        ("Funzionalità base", test_basic_functionality),
        ("Risoluzione semplice", test_simple_solve),
        ("Casi limite", test_edge_cases)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"Risultato: {status}")
        except Exception as e:
            print(f"❌ ERRORE: {e}")
            results.append((test_name, False))
    
    # Riepilogo finale
    print(f"\n🏁 RIEPILOGO TEST")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nRisultato: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 Tutti i test sono passati! Il solver_2l è operativo.")
        return True
    else:
        print("⚠️ Alcuni test sono falliti. Verificare l'implementazione.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 