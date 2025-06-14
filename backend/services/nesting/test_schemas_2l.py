"""
Test script per verificare la serializzazione degli schemi Pydantic 2L
Verifica che l'output JSON contenga il campo level per ogni tool e l'elenco dei cavalletti
"""

import json
import sys
import os

# Aggiungi il percorso del backend per gli import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.nesting.solver_2l import NestingModel2L, NestingParameters2L, AutoclaveInfo2L
from schemas.batch_nesting import (
    PosizionamentoTool2L, 
    CavallettoPosizionamento, 
    NestingMetrics2L,
    NestingSolveResponse2L,
    NestingToolPositionCompat
)


def test_example_solution_serialization():
    """Test della serializzazione di una soluzione di esempio"""
    print("🧪 Test serializzazione schemi 2L...")
    
    # Crea il solver
    parameters = NestingParameters2L(
        use_cavalletti=True,
        cavalletto_height_mm=100.0,
        max_weight_per_level_kg=200.0
    )
    solver = NestingModel2L(parameters)
    
    # Genera soluzione di esempio
    solution = solver.create_example_solution_2l()
    
    # Serializza in JSON
    solution_json = solution.model_dump()
    
    print("✅ Soluzione serializzata con successo!")
    print(f"📊 Tool posizionati: {len(solution.positioned_tools)}")
    print(f"🔧 Cavalletti utilizzati: {len(solution.cavalletti)}")
    
    # Verifica che ogni tool abbia il campo level
    for i, tool in enumerate(solution.positioned_tools):
        level = tool.level
        print(f"   Tool {i+1} (ODL {tool.odl_id}): level={level}, z_position={tool.z_position}mm")
        assert hasattr(tool, 'level'), f"Tool {i+1} manca il campo 'level'"
        assert level in [0, 1], f"Tool {i+1} ha level={level} non valido (deve essere 0 o 1)"
    
    # Verifica cavalletti
    for i, cavalletto in enumerate(solution.cavalletti):
        print(f"   Cavalletto {i+1}: supporta ODL {cavalletto.tool_odl_id}, pos=({cavalletto.x}, {cavalletto.y})")
        assert hasattr(cavalletto, 'tool_odl_id'), f"Cavalletto {i+1} manca il campo 'tool_odl_id'"
        assert hasattr(cavalletto, 'x'), f"Cavalletto {i+1} manca il campo 'x'"
        assert hasattr(cavalletto, 'y'), f"Cavalletto {i+1} manca il campo 'y'"
    
    # Verifica metriche specifiche 2L
    metrics = solution.metrics
    print(f"📈 Metriche 2L:")
    print(f"   Level 0 count: {metrics.level_0_count}")
    print(f"   Level 1 count: {metrics.level_1_count}")
    print(f"   Cavalletti used: {metrics.cavalletti_used}")
    print(f"   Coverage: {metrics.cavalletti_coverage_pct:.1f}%")
    
    return solution_json


def test_schema_validation():
    """Test di validazione degli schemi"""
    print("\n🧪 Test validazione schemi...")
    
    # Test PosizionamentoTool2L
    tool_2l = PosizionamentoTool2L(
        odl_id=5,
        tool_id=12,
        x=100.0,
        y=200.0,
        width=300.0,
        height=250.0,
        rotated=False,
        weight_kg=25.5,
        level=1,  # Su cavalletto
        z_position=100.0,
        lines_used=2
    )
    print(f"✅ PosizionamentoTool2L validato: ODL {tool_2l.odl_id}, level={tool_2l.level}")
    
    # Test CavallettoPosizionamento
    cavalletto = CavallettoPosizionamento(
        x=120.0,
        y=220.0,
        width=80.0,
        height=60.0,
        tool_odl_id=5,
        tool_id=12,
        sequence_number=0,
        center_x=160.0,
        center_y=250.0,
        support_area_mm2=4800.0
    )
    print(f"✅ CavallettoPosizionamento validato: supporta ODL {cavalletto.tool_odl_id}")
    
    # Test schema di compatibilità
    tool_compat = NestingToolPositionCompat(
        odl_id=7,
        tool_id=15,
        x=150.0,
        y=300.0,
        width=200.0,
        height=180.0,
        rotated=True,
        weight_kg=18.5,
        plane=2  # Formato legacy
    )
    
    # Converti a formato 2L
    tool_2l_converted = tool_compat.to_2l_format()
    print(f"✅ Conversione legacy->2L: plane={tool_compat.plane} -> level={tool_2l_converted.level}")
    assert tool_2l_converted.level == 1, "Conversione plane=2 -> level=1 fallita"


def test_json_output():
    """Test dell'output JSON finale"""
    print("\n🧪 Test output JSON...")
    
    parameters = NestingParameters2L()
    solver = NestingModel2L(parameters)
    solution = solver.create_example_solution_2l()
    
    # Serializza in JSON con indentazione
    json_output = json.dumps(solution.model_dump(), indent=2, ensure_ascii=False)
    
    # Verifica campi chiave nel JSON
    assert '"level":' in json_output, "Campo 'level' mancante nel JSON"
    assert '"cavalletti":' in json_output, "Campo 'cavalletti' mancante nel JSON"
    assert '"tool_odl_id":' in json_output, "Campo 'tool_odl_id' mancante nel JSON"
    assert '"level_0_count":' in json_output, "Campo 'level_0_count' mancante nel JSON"
    assert '"level_1_count":' in json_output, "Campo 'level_1_count' mancante nel JSON"
    
    print("✅ Tutti i campi richiesti presenti nel JSON")
    
    # Salva JSON di esempio
    with open('nesting_2l_example.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    print("💾 JSON di esempio salvato in 'nesting_2l_example.json'")
    
    return json_output


def test_backward_compatibility():
    """Test di compatibilità backward con schemi esistenti"""
    print("\n🧪 Test compatibilità backward...")
    
    # Crea tool con formato legacy
    legacy_tool_data = {
        "odl_id": 8,
        "tool_id": 20,
        "x": 200.0,
        "y": 400.0,
        "width": 250.0,
        "height": 200.0,
        "rotated": False,
        "weight_kg": 30.0,
        "plane": 1  # Formato legacy
    }
    
    # Carica con schema compatibile
    tool_compat = NestingToolPositionCompat(**legacy_tool_data)
    
    # Converti a 2L
    tool_2l = tool_compat.to_2l_format()
    
    print(f"✅ Tool legacy caricato: plane={tool_compat.plane}")
    print(f"✅ Tool 2L convertito: level={tool_2l.level}, z_position={tool_2l.z_position}")
    
    assert tool_2l.level == 0, "Conversione plane=1 -> level=0 fallita"
    assert tool_2l.z_position == 0.0, "Z position per level=0 dovrebbe essere 0.0"


def main():
    """Esegue tutti i test"""
    print("🚀 Avvio test schemi Pydantic 2L\n")
    
    try:
        # Test serializzazione
        solution_json = test_example_solution_serialization()
        
        # Test validazione
        test_schema_validation()
        
        # Test output JSON
        json_output = test_json_output()
        
        # Test compatibilità
        test_backward_compatibility()
        
        print("\n🎉 Tutti i test completati con successo!")
        print("📋 Riepilogo:")
        print("   ✅ Serializzazione schemi 2L")
        print("   ✅ Validazione campi obbligatori")
        print("   ✅ Output JSON corretto")
        print("   ✅ Compatibilità backward")
        print("\n📊 La soluzione contiene:")
        print(f"   • Tool con campo 'level': ✅")
        print(f"   • Cavalletti con coordinate: ✅")
        print(f"   • Metriche 2L complete: ✅")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test fallito: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 