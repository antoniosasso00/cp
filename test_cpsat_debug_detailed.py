#!/usr/bin/env python3
"""
Test debug dettagliato per isolare l'errore BoundedLinearExpression
"""
import sys
import os

# Aggiungi il path di backend al PYTHONPATH
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    print("🔧 === TEST DEBUG DETTAGLIATO CP-SAT ===")
    
    # Import 
    print("\n📋 IMPORT...")
    from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo
    print("✅ Import OK")
    
    # Dati minimi
    print("\n📋 DATI MINIMI...")
    
    params = NestingParameters(
        padding_mm=1.0,
        min_distance_mm=1.0,
        vacuum_lines_capacity=10,
        use_fallback=True,
        allow_heuristic=False,  # Disabilita GRASP per semplicità
        use_multithread=False   # Disabilita multithread per debugging
    )
    
    # Singolo tool semplice
    tool = ToolInfo(
        odl_id=1,
        width=100.0,
        height=80.0,
        weight=2.0,
        lines_needed=1,
        ciclo_cura_id=None,
        priority=1
    )
    
    autoclave = AutoclaveInfo(
        id=1,
        width=1000.0,
        height=800.0,
        max_weight=100.0,
        max_lines=10
    )
    
    print(f"Tool: {tool.width}x{tool.height}, peso {tool.weight}kg")
    print(f"Autoclave: {autoclave.width}x{autoclave.height}, peso max {autoclave.max_weight}kg")
    
    # Test solver con debugging dettagliato
    print("\n📋 TEST SOLVER...")
    solver = NestingModel(params)
    
    # Modifica temporanea: disabilita CP-SAT e usa solo greedy per test
    original_use_fallback = params.use_fallback
    params.use_fallback = True
    
    print("🔧 TEST 1: Solo fallback greedy (no CP-SAT)...")
    try:
        result = solver._solve_greedy_fallback_aerospace([tool], autoclave, 0.0)
        print(f"✅ Greedy OK: {len(result.layouts)} tool posizionati, efficienza {result.metrics.efficiency_score:.1f}%")
    except Exception as e:
        print(f"❌ Greedy ERROR: {str(e)}")
        raise
    
    print("\n🔧 TEST 2: CP-SAT con timeout basso...")
    try:
        result = solver._solve_cpsat_aerospace([tool], autoclave, 5.0, 0.0)
        print(f"✅ CP-SAT OK: {len(result.layouts)} tool posizionati, efficienza {result.metrics.efficiency_score:.1f}%")
        if result.success:
            print("🎯 CP-SAT SUCCESS - Nessun errore BoundedLinearExpression!")
        else:
            print(f"⚠️ CP-SAT Failed: {result.message}")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ CP-SAT ERROR: {error_msg}")
        
        if 'BoundedLinearExpression' in error_msg and 'index' in error_msg:
            print("🚨 CONFERMATO: Errore BoundedLinearExpression persiste")
            
            # Debug specifico per individuare la causa
            import traceback
            print("\n🔧 TRACEBACK COMPLETO:")
            traceback.print_exc()
        else:
            print(f"🔧 Errore diverso: {error_msg}")
    
    print("\n🔧 TEST 3: Solo solve principale...")
    try:
        result = solver.solve([tool], autoclave)
        print(f"✅ SOLVE OK: {len(result.layouts)} tool posizionati")
        print(f"   - Successo: {result.success}")
        print(f"   - Algoritmo: {result.algorithm_status}")
        print(f"   - Efficienza: {result.metrics.efficiency_score:.1f}%")
        print(f"   - Fallback usato: {result.metrics.fallback_used}")
    except Exception as e:
        print(f"❌ SOLVE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ ERRORE GENERALE: {str(e)}")
    import traceback
    print("🔧 Traceback:")
    traceback.print_exc()

finally:
    print("\n🔧 === FINE TEST DEBUG DETTAGLIATO ===") 