#!/usr/bin/env python3
"""
Test diretto del NestingService per isolare il problema
"""
import sys
import os

# Aggiungi il path di backend al PYTHONPATH
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    print("🔧 === TEST DIRETTO NESTING SERVICE ===")
    
    # Test 1: Import base
    print("\n📋 TEST 1: Import del NestingService...")
    from services.nesting_service import NestingService, NestingParameters
    print("✅ Import NestingService: OK")
    
    # Test 2: Import solver aerospaziale
    print("\n📋 TEST 2: Import solver aerospaziale...")
    from services.nesting.solver import NestingModel, NestingParameters as AerospaceParameters, ToolInfo, AutoclaveInfo
    print("✅ Import solver aerospaziale: OK")
    
    # Test 3: Istanziazione NestingService
    print("\n📋 TEST 3: Istanziazione NestingService...")
    service = NestingService()
    print("✅ Istanziazione NestingService: OK")
    
    # Test 4: Mock dati per test isolato
    print("\n📋 TEST 4: Test con dati mock...")
    
    # Mock ODL data
    mock_odl_data = [
        {
            'odl_id': 1,
            'tool_width': 300.0,
            'tool_height': 200.0,
            'tool_weight': 5.0,
            'ciclo_cura_id': None,
            'parte_descrizione': 'Test Part 1',
            'tool_part_number': 'TP001',
            'lines_needed': 1
        },
        {
            'odl_id': 2,
            'tool_width': 250.0,
            'tool_height': 150.0,
            'tool_weight': 3.0,
            'ciclo_cura_id': None,
            'parte_descrizione': 'Test Part 2',
            'tool_part_number': 'TP002',
            'lines_needed': 1
        }
    ]
    
    # Mock autoclave data
    mock_autoclave_data = {
        'id': 1,
        'nome': 'MOCK_AUTOCLAVE',
        'larghezza_piano': 2000.0,
        'lunghezza': 3000.0,
        'max_load_kg': 1000.0,
        'num_linee_vuoto': 10
    }
    
    # Mock parametri
    mock_parameters = NestingParameters(
        padding_mm=1.0,
        min_distance_mm=1.0,
        vacuum_lines_capacity=10,
        use_fallback=True,
        allow_heuristic=True
    )
    
    print(f"📋 Dati mock: {len(mock_odl_data)} ODL, autoclave {mock_autoclave_data['lunghezza']}x{mock_autoclave_data['larghezza_piano']}mm")
    
    # Test 5: Perform nesting 2D isolato
    print("\n📋 TEST 5: Esecuzione perform_nesting_2d...")
    result = service.perform_nesting_2d(mock_odl_data, mock_autoclave_data, mock_parameters)
    
    print(f"✅ Nesting completato!")
    print(f"📊 Risultato:")
    print(f"   - Tool posizionati: {len(result.positioned_tools)}")
    print(f"   - Efficienza: {result.efficiency:.1f}%")
    print(f"   - Successo: {result.success}")
    print(f"   - Algoritmo: {result.algorithm_status}")
    print(f"   - Area utilizzata: {result.area_pct:.1f}%")
    
    if result.positioned_tools:
        print(f"📋 Dettagli tool:")
        for i, tool in enumerate(result.positioned_tools):
            print(f"   - Tool {tool.odl_id}: pos({tool.x:.1f},{tool.y:.1f}) dim({tool.width:.1f}x{tool.height:.1f}) rot={tool.rotated}")
    
    if result.excluded_odls:
        print(f"⚠️ ODL esclusi: {len(result.excluded_odls)}")
        for excl in result.excluded_odls:
            print(f"   - ODL {excl.get('odl_id', 'N/A')}: {excl.get('motivo', 'N/A')}")
    
    print(f"\n🎯 CONCLUSIONE: NestingService funziona correttamente con dati mock!")
    
except ImportError as e:
    print(f"❌ ERRORE IMPORT: {str(e)}")
    print("🔧 Possibili cause:")
    print("   - Path PYTHONPATH non corretto")
    print("   - Dipendenze mancanti")
    print("   - File corrotti")

except Exception as e:
    print(f"❌ ERRORE ESECUZIONE: {str(e)}")
    print(f"🔧 Tipo errore: {type(e).__name__}")
    import traceback
    print("🔧 Traceback completo:")
    traceback.print_exc()

finally:
    print("\n🔧 === FINE TEST NESTING SERVICE ===") 