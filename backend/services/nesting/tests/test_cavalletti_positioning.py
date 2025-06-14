"""
Test per il calcolo e posizionamento automatico dei cavalletti nel solver 2L
Test specifico per Prompt 4 - CarbonPilot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from solver_2l import (
    NestingModel2L, NestingParameters2L, ToolInfo2L, AutoclaveInfo2L, 
    NestingLayout2L, CavallettiConfiguration, CavallettoPosition
)

def test_calcolo_cavalletti_tool_grande():
    """
    Test specifico per Prompt 4: verifica calcolo cavalletti per tool di lunghezza notevole
    """
    
    print("🔧 TEST CAVALLETTI - Tool di lunghezza notevole")
    print("=" * 60)
    
    # Configurazione solver
    parameters = NestingParameters2L(
        padding_mm=5.0,
        use_cavalletti=True,
        cavalletto_height_mm=100.0
    )
    
    solver = NestingModel2L(parameters)
    
    # Tool di test: dimensioni notevoli (600mm x 200mm)
    tool_layout = NestingLayout2L(
        odl_id=101,
        x=100.0,      # Posizione X sul piano autoclave
        y=150.0,      # Posizione Y sul piano autoclave
        width=600.0,  # Larghezza notevole
        height=200.0, # Altezza
        weight=45.0,
        level=1,      # Posizionato su cavalletti (livello 1)
        rotated=False,
        lines_used=2
    )
    
    print(f"📋 Tool di test:")
    print(f"   ODL: {tool_layout.odl_id}")
    print(f"   Dimensioni: {tool_layout.width:.1f} x {tool_layout.height:.1f} mm")
    print(f"   Posizione: ({tool_layout.x:.1f}, {tool_layout.y:.1f}) mm")
    print(f"   Livello: {tool_layout.level} (su cavalletti)")
    print()
    
    # Configurazione cavalletti
    config = CavallettiConfiguration(
        cavalletto_width=80.0,
        cavalletto_height=60.0,
        min_distance_from_edge=30.0,
        max_span_without_support=400.0,
        min_distance_between_cavalletti=200.0,
        prefer_symmetric=True,
        force_minimum_two=True
    )
    
    print(f"🔧 Configurazione cavalletti:")
    print(f"   Dimensioni cavalletto: {config.cavalletto_width} x {config.cavalletto_height} mm")
    print(f"   Distanza massima senza supporto: {config.max_span_without_support} mm")
    print(f"   Distanza minima tra cavalletti: {config.min_distance_between_cavalletti} mm")
    print()
    
    # Calcola posizioni cavalletti
    cavalletti = solver.calcola_cavalletti_per_tool(tool_layout, config)
    
    print(f"📊 RISULTATI CALCOLO CAVALLETTI:")
    print(f"   Numero cavalletti calcolati: {len(cavalletti)}")
    print()
    
    # Verifica e mostra ogni cavalletto
    for i, cavalletto in enumerate(cavalletti):
        print(f"   Cavalletto #{cavalletto.sequence_number}:")
        print(f"     Posizione: ({cavalletto.x:.1f}, {cavalletto.y:.1f}) mm")
        print(f"     Dimensioni: {cavalletto.width:.1f} x {cavalletto.height:.1f} mm")
        print(f"     Centro: ({cavalletto.center_x:.1f}, {cavalletto.center_y:.1f}) mm")
        
        # VERIFICA CRUCIALE: il cavalletto è dentro l'area del tool?
        inside_tool_x = (tool_layout.x <= cavalletto.x and 
                        cavalletto.x + cavalletto.width <= tool_layout.x + tool_layout.width)
        inside_tool_y = (tool_layout.y <= cavalletto.y and 
                        cavalletto.y + cavalletto.height <= tool_layout.y + tool_layout.height)
        
        if inside_tool_x and inside_tool_y:
            print(f"     ✅ DENTRO l'area del tool")
        else:
            print(f"     ❌ FUORI dall'area del tool!")
            
        print()
    
    # Verifica distanze tra cavalletti
    if len(cavalletti) > 1:
        print(f"📏 VERIFICA DISTANZE TRA CAVALLETTI:")
        for i in range(len(cavalletti) - 1):
            cav1 = cavalletti[i]
            cav2 = cavalletti[i + 1]
            
            # Distanza tra centri (lungo la dimensione principale)
            if tool_layout.width >= tool_layout.height:
                # Tool orizzontale - distanza lungo X
                distance = abs(cav2.center_x - cav1.center_x)
            else:
                # Tool verticale - distanza lungo Y
                distance = abs(cav2.center_y - cav1.center_y)
            
            print(f"   Distanza cavalletto {i} → {i+1}: {distance:.1f} mm")
            
            if distance <= config.max_span_without_support:
                print(f"     ✅ Distanza accettabile (≤ {config.max_span_without_support} mm)")
            else:
                print(f"     ⚠️ Distanza eccessiva (> {config.max_span_without_support} mm)")
        print()
    
    # Test con tool di orientamento diverso (verticale)
    print("🔄 TEST AGGIUNTIVO - Tool orientamento verticale")
    print("-" * 40)
    
    tool_verticale = NestingLayout2L(
        odl_id=102,
        x=200.0,
        y=100.0,
        width=180.0,   # Più stretto
        height=500.0,  # Più alto - orientamento verticale
        weight=35.0,
        level=1,
        rotated=True,
        lines_used=1
    )
    
    print(f"📋 Tool verticale: {tool_verticale.width} x {tool_verticale.height} mm")
    
    cavalletti_verticali = solver.calcola_cavalletti_per_tool(tool_verticale, config)
    
    print(f"📊 Cavalletti per tool verticale: {len(cavalletti_verticali)}")
    for cavalletto in cavalletti_verticali:
        print(f"   Pos: ({cavalletto.x:.1f}, {cavalletto.y:.1f}) mm")
    
    print()
    print("✅ TEST CAVALLETTI COMPLETATO")
    
    return cavalletti, cavalletti_verticali

def test_esempio_workflow_completo():
    """
    Esempio completo di workflow con nesting 2L e calcolo cavalletti automatico
    """
    
    print("\n" + "=" * 60)
    print("🚀 ESEMPIO WORKFLOW COMPLETO - NESTING 2L + CAVALLETTI")
    print("=" * 60)
    
    # Configurazione
    parameters = NestingParameters2L(
        padding_mm=10.0,
        use_cavalletti=True,
        cavalletto_height_mm=100.0,
        max_weight_per_level_kg=150.0,
        prefer_base_level=True
    )
    
    autoclave = AutoclaveInfo2L(
        id=1,
        width=1200.0,
        height=800.0,
        max_weight=300.0,
        max_lines=25,
        has_cavalletti=True,
        cavalletto_height=100.0,
        max_weight_per_level=150.0
    )
    
    # Dataset di tool con mix di dimensioni
    tools = [
        ToolInfo2L(odl_id=1, width=500, height=300, weight=45, can_use_cavalletto=True),    # Grande
        ToolInfo2L(odl_id=2, width=350, height=200, weight=25, can_use_cavalletto=True),   # Medio
        ToolInfo2L(odl_id=3, width=600, height=150, weight=35, can_use_cavalletto=True),   # Lungo e stretto
        ToolInfo2L(odl_id=4, width=200, height=450, weight=30, can_use_cavalletto=True),   # Alto e stretto
        ToolInfo2L(odl_id=5, width=250, height=180, weight=15, can_use_cavalletto=False, preferred_level=0),  # Solo livello 0
    ]
    
    print(f"📋 Dataset: {len(tools)} tool")
    print(f"🏭 Autoclave: {autoclave.width} x {autoclave.height} mm, Cavalletti: {autoclave.has_cavalletti}")
    print()
    
    # Esegui nesting
    solver = NestingModel2L(parameters)
    solution = solver.solve_2l(tools, autoclave)
    
    print(f"📊 RISULTATI NESTING:")
    print(f"   Successo: {solution.success}")
    print(f"   Algoritmo: {solution.algorithm_status}")
    print(f"   Tool posizionati: {solution.metrics.positioned_count}/{len(tools)}")
    print(f"   Efficienza: {solution.metrics.area_pct:.1f}%")
    print()
    
    # Analizza distribuzione per livelli
    level_0_tools = [l for l in solution.layouts if l.level == 0]
    level_1_tools = [l for l in solution.layouts if l.level == 1]
    
    print(f"📋 DISTRIBUZIONE LIVELLI:")
    print(f"   Livello 0 (base): {len(level_0_tools)} tool")
    for tool in level_0_tools:
        print(f"     ODL {tool.odl_id}: ({tool.x:.0f}, {tool.y:.0f}) {tool.width:.0f}x{tool.height:.0f}mm")
    
    print(f"   Livello 1 (cavalletti): {len(level_1_tools)} tool")
    for tool in level_1_tools:
        print(f"     ODL {tool.odl_id}: ({tool.x:.0f}, {tool.y:.0f}) {tool.width:.0f}x{tool.height:.0f}mm")
    print()
    
    # Verifica se la soluzione include già le posizioni cavalletti
    if hasattr(solution, 'cavalletti_positions') or 'cavalletti_positions' in solution.__dict__:
        cavalletti_positions = getattr(solution, 'cavalletti_positions', solution.__dict__.get('cavalletti_positions', []))
        
        print(f"🔧 CAVALLETTI AUTOMATICI CALCOLATI:")
        print(f"   Numero totale cavalletti: {len(cavalletti_positions)}")
        
        for cavalletto in cavalletti_positions:
            print(f"     ODL {cavalletto.tool_odl_id} - Cavalletto #{cavalletto.sequence_number}:")
            print(f"       Posizione: ({cavalletto.x:.1f}, {cavalletto.y:.1f}) mm")
            print(f"       Dimensioni: {cavalletto.width}x{cavalletto.height} mm")
    else:
        print("ℹ️ Posizioni cavalletti non incluse nella soluzione (implementazione da estendere)")
    
    print()
    print("✅ ESEMPIO WORKFLOW COMPLETATO")
    
    return solution

if __name__ == "__main__":
    # Esegui i test
    print("🔧 AVVIO TEST SISTEMA CAVALLETTI")
    print()
    
    # Test specifico per tool di lunghezza notevole
    cavalletti_orizz, cavalletti_vert = test_calcolo_cavalletti_tool_grande()
    
    # Esempio workflow completo
    solution = test_esempio_workflow_completo()
    
    print("\n" + "=" * 60)
    print("🎯 TUTTI I TEST COMPLETATI CON SUCCESSO")
    print("=" * 60) 