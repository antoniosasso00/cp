#!/usr/bin/env python3
"""
Debug test per rotazione 90° - CarbonPilot v1.4.17-DEMO
"""

import sys
sys.path.append('backend')

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

def debug_rotation():
    """Debug dettagliato per rotazione 90°"""
    print("🔍 DEBUG ROTAZIONE 90°")
    print("=" * 50)
    
    # Setup
    params = NestingParameters()
    model = NestingModel(params)
    
    # Scenario semplificato: 1 pezzo che richiede rotazione
    tools = [
        ToolInfo(odl_id=1, width=150, height=300, weight=10, lines_needed=1)
    ]
    
    autoclave = AutoclaveInfo(id=1, width=200, height=300, max_weight=1000, max_lines=10)
    
    print(f"Pezzo: 150x300mm")
    print(f"Autoclave: 200x300mm")
    print(f"Margin: {params.min_distance_mm}mm")
    print()
    
    # Verifica manuale fits
    margin = params.min_distance_mm
    fits_normal = (150 + margin <= 200 and 300 + margin <= 300)
    fits_rotated = (300 + margin <= 200 and 150 + margin <= 300)
    
    print(f"Fits normal: {fits_normal} ({150 + margin} <= 200 && {300 + margin} <= 300)")
    print(f"Fits rotated: {fits_rotated} ({300 + margin} <= 200 && {150 + margin} <= 300)")
    print()
    
    if not fits_normal and not fits_rotated:
        print("❌ PROBLEMA: Nessun orientamento possibile!")
        return
    
    # Test pre-filtering
    print("🔍 Test Pre-filtering:")
    valid_tools, excluded_tools = model._prefilter_tools(tools, autoclave)
    
    print(f"Valid tools: {len(valid_tools)}")
    print(f"Excluded tools: {len(excluded_tools)}")
    
    if excluded_tools:
        for exc in excluded_tools:
            print(f"  Escluso ODL {exc['odl_id']}: {exc['motivo']} - {exc['dettagli']}")
    
    if not valid_tools:
        print("❌ PROBLEMA: Tool escluso nel pre-filtering!")
        return
    
    # Test completo
    print("\n🧪 Test Completo:")
    try:
        solution = model.solve(tools, autoclave)
        
        print(f"Successo: {solution.success}")
        print(f"Posizionati: {solution.metrics.positioned_count}")
        print(f"Rotazione usata: {solution.metrics.rotation_used}")
        print(f"Algoritmo: {solution.algorithm_status}")
        print(f"Messaggio: {solution.message}")
        
        if solution.layouts:
            for layout in solution.layouts:
                print(f"Layout ODL {layout.odl_id}: ({layout.x}, {layout.y}) - {layout.width}x{layout.height}mm, rotated={layout.rotated}")
        
        if solution.excluded_odls:
            print("Esclusi:")
            for exc in solution.excluded_odls:
                print(f"  ODL {exc['odl_id']}: {exc['motivo']}")
                
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rotation() 