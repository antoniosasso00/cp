#!/usr/bin/env python3
"""
🔍 CarbonPilot - Diagnosi Problema Cavalletti 2L
Analizza perché i tool su livello 1 sono fisicamente incorretti (sospesi, un solo appoggio)
"""

import sys
import os
import json
sys.path.append('backend')

from services.nesting.solver_2l import (
    NestingModel2L, 
    NestingParameters2L, 
    ToolInfo2L, 
    AutoclaveInfo2L,
    CavallettiConfiguration,
    NestingLayout2L,
    CavallettoPosition,
    CavallettoFixedPosition
)

def analyze_sample_data():
    """Analizza i dati del file sample_2l_corrected_data.json"""
    print("🔍 ANALISI DATI SAMPLE")
    print("=" * 60)
    
    with open('sample_2l_corrected_data.json', 'r') as f:
        data = json.load(f)
    
    positioned_tools = data['positioned_tools']
    cavalletti = data['cavalletti']
    canvas_width = data['canvas_width']
    canvas_height = data['canvas_height']
    
    print(f"📏 Canvas: {canvas_width} × {canvas_height} mm")
    print(f"🔧 Tool posizionati: {len(positioned_tools)}")
    print(f"🏗️ Cavalletti: {len(cavalletti)}")
    print()
    
    # Analizza tool su livello 1
    level_1_tools = [t for t in positioned_tools if t['level'] == 1]
    print(f"🎯 TOOL SU LIVELLO 1: {len(level_1_tools)}")
    print("-" * 40)
    
    for tool in level_1_tools:
        odl_id = tool['odl_id']
        x, y = tool['x'], tool['y']
        width, height = tool['width'], tool['height']
        
        print(f"ODL {odl_id}: ({x},{y}) {width}×{height}mm")
        
        # Trova cavalletti per questo tool
        tool_cavalletti = [c for c in cavalletti if c['tool_odl_id'] == odl_id]
        print(f"  Cavalletti: {len(tool_cavalletti)}")
        
        if len(tool_cavalletti) < 2:
            print(f"  ❌ PROBLEMA FISICO: Solo {len(tool_cavalletti)} supporto(i), richiesti ≥2")
        
        # Analizza posizione cavalletti
        for i, cav in enumerate(tool_cavalletti):
            cx, cy = cav['x'], cav['y'] 
            cw, ch = cav['width'], cav['height']
            print(f"    Cavalletto {i+1}: ({cx},{cy}) {cw}×{ch}mm")
            
            # Verifica se il cavalletto supporta realmente il tool
            overlap_x = not (x + width <= cx or cx + cw <= x)
            overlap_y = not (y + height <= cy or cy + ch <= y)
            
            if not (overlap_x and overlap_y):
                print(f"    ❌ NESSUN OVERLAP: Cavalletto non sotto il tool!")
            else:
                print(f"    ✅ Overlap corretto")
        
        # Analizza distribuzione cavalletti
        if len(tool_cavalletti) >= 2:
            tool_center_x = x + width / 2
            left_cavs = [c for c in tool_cavalletti if c['center_x'] < tool_center_x]
            right_cavs = [c for c in tool_cavalletti if c['center_x'] >= tool_center_x]
            
            print(f"  Distribuzione: {len(left_cavs)} sinistra, {len(right_cavs)} destra")
            if len(left_cavs) == 0 or len(right_cavs) == 0:
                print(f"  ❌ CLUSTERING: Tutti cavalletti da un lato!")
                
        print()

def analyze_cavalletti_as_fixed_vs_per_tool():
    """Analizza la differenza tra cavalletti fissi dell'autoclave vs cavalletti per tool"""
    print("🔍 ANALISI CONCETTO CAVALLETTI")
    print("=" * 60)
    
    solver = NestingModel2L(NestingParameters2L())
    
    # Autoclave di test
    autoclave = AutoclaveInfo2L(
        id=1,
        width=8000.0,
        height=1900.0,
        max_weight=5000.0,
        max_lines=20,
        has_cavalletti=True,
        max_cavalletti=4,
        cavalletto_thickness_mm=60.0
    )
    
    print("🏗️ CAVALLETTI FISSI AUTOCLAVE")
    print("-" * 30)
    cavalletti_fissi = solver.calcola_cavalletti_fissi_autoclave(autoclave)
    
    for i, cav_fisso in enumerate(cavalletti_fissi):
        print(f"Cavalletto fisso {i+1}: X={cav_fisso.x:.0f}-{cav_fisso.end_x:.0f}mm, attraversa tutta Y (0-{autoclave.height:.0f}mm)")
    
    print("\n🔧 CAVALLETTI PER TOOL INDIVIDUALE")
    print("-" * 30)
    
    config = CavallettiConfiguration(
        cavalletto_width=80.0,
        cavalletto_height=60.0,
        min_distance_from_edge=50.0,
        max_span_without_support=400.0
    )
    
    # Tool di test (da sample data)
    tool_layout = NestingLayout2L(
        odl_id=2,
        x=1000, y=200,
        width=900, height=600,
        weight=75.0,
        level=1
    )
    
    cavalletti_tool = solver.calcola_cavalletti_per_tool(tool_layout, config)
    
    for i, cav_tool in enumerate(cavalletti_tool):
        print(f"Cavalletto tool {i+1}: ({cav_tool.x:.0f},{cav_tool.y:.0f}) {cav_tool.width:.0f}×{cav_tool.height:.0f}mm")
    
    print("\n🚨 PROBLEMA IDENTIFICATO:")
    print("Il sistema genera DUE tipi di cavalletti diversi:")
    print("1. Cavalletti FISSI dell'autoclave (trasversali, attraversano tutta la larghezza)")
    print("2. Cavalletti per TOOL (sotto ogni tool, con dimensioni limitate)")
    print("Ma non verifica la CORRISPONDENZA tra i due!")

def test_physical_support_validation():
    """Testa la validazione del supporto fisico"""
    print("\n🔍 TEST VALIDAZIONE SUPPORTO FISICO")
    print("=" * 60)
    
    solver = NestingModel2L(NestingParameters2L())
    
    autoclave = AutoclaveInfo2L(
        id=1,
        width=8000.0,
        height=1900.0,
        max_weight=5000.0,
        max_lines=20,
        has_cavalletti=True,
        max_cavalletti=4,
        cavalletto_thickness_mm=60.0
    )
    
    # Test case: tool che dovrebbe essere supportato
    test_cases = [
        {"x": 1000, "y": 200, "width": 900, "height": 600, "desc": "Tool su cavalletti fissi"},
        {"x": 100, "y": 200, "width": 200, "height": 300, "desc": "Tool piccolo lontano da cavalletti"},
        {"x": 4000, "y": 500, "width": 1000, "height": 400, "desc": "Tool grande al centro"}
    ]
    
    for case in test_cases:
        has_support = solver._has_sufficient_fixed_support(
            case["x"], case["y"], case["width"], case["height"], autoclave
        )
        
        result = "✅" if has_support else "❌"
        print(f"{result} {case['desc']}: Supporto adeguato = {has_support}")

def diagnose_conceptual_error():
    """Diagnosi dell'errore concettuale"""
    print("\n🔍 DIAGNOSI ERRORE CONCETTUALE")
    print("=" * 60)
    
    print("❌ PROBLEMA PRINCIPALE IDENTIFICATO:")
    print()
    print("Il sistema attuale ha un ERRORE CONCETTUALE GRAVE:")
    print()
    print("1. 🏗️ CAVALLETTI REALI sono STRUTTURE FISSE dell'autoclave")
    print("   - Sono segmenti trasversali che attraversano tutta la larghezza")
    print("   - La loro posizione è FISSA e determinata dall'autoclave")
    print("   - I tool devono essere posizionati IN MODO da essere supportati da questi")
    print()
    print("2. 🔧 SISTEMA ATTUALE SBAGLIATO:")
    print("   - Calcola cavalletti 'virtuali' sotto ogni tool")
    print("   - Non considera i cavalletti fissi reali dell'autoclave")
    print("   - Permette posizionamento tool senza verifica supporto reale")
    print()
    print("3. 🎯 SOLUZIONE CORRETTA:")
    print("   - Calcolare PRIMA i cavalletti fissi dell'autoclave") 
    print("   - Posizionare i tool SOLO dove sono supportati da ≥2 cavalletti fissi")
    print("   - Eliminare il concetto di 'cavalletti per tool'")
    print()
    print("4. 🚨 RISULTATO ATTUALE:")
    print("   - Tool 'sospesi' senza supporto fisico reale")
    print("   - Tool con un solo appoggio (instabile)")
    print("   - Layout fisicamente impossibili")

def suggest_fix_approach():
    """Suggerisce l'approccio per il fix"""
    print("\n💡 APPROCCIO PER IL FIX")
    print("=" * 60)
    
    print("STEP 1: MODIFICA SOLVER VINCOLI")
    print("- Nel CP-SAT e Greedy, PRIMA calcolare cavalletti fissi")
    print("- Aggiungere vincolo: tool livello 1 DEVE essere supportato da ≥2 cavalletti fissi")
    print("- Eliminare generazione cavalletti 'virtuali' per tool")
    print()
    
    print("STEP 2: MODIFICA VALIDAZIONE POSIZIONE")
    print("- _has_sufficient_fixed_support() deve essere più rigorosa")
    print("- Verificare che ALMENO 2 cavalletti fissi attraversino il tool")
    print("- Verificare distribuzione bilanciata (non tutti da un lato)")
    print()
    
    print("STEP 3: MODIFICA VISUALIZZAZIONE")
    print("- Mostrare solo i cavalletti fissi dell'autoclave")
    print("- Non mostrare cavalletti 'virtuali' per tool")
    print("- Evidenziare problemi di supporto nell'interfaccia")
    print()
    
    print("STEP 4: TEST FISICO")
    print("- Verificare che ogni layout sia fisicamente realizzabile")
    print("- Test che un operatore possa realmente caricare la configurazione")
    print("- Validazione che nessun tool sia 'sospeso'")

if __name__ == "__main__":
    print("🔍 DIAGNOSI APPROFONDITA PROBLEMA CAVALLETTI 2L")
    print("=" * 80)
    
    try:
        analyze_sample_data()
        analyze_cavalletti_as_fixed_vs_per_tool()
        test_physical_support_validation() 
        diagnose_conceptual_error()
        suggest_fix_approach()
        
        print("\n🎯 CONCLUSIONE:")
        print("Il problema è CONCETTUALE: i cavalletti sono trattati come 'decorazioni'")
        print("sotto i tool invece che come VINCOLI FISICI REALI dell'autoclave.")
        print("Il fix richiede riscrittura delle logiche di posizionamento e validazione.")
        
    except Exception as e:
        print(f"❌ Errore durante diagnosi: {e}")
        import traceback
        traceback.print_exc() 