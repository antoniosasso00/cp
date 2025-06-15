#!/usr/bin/env python3
"""
🧪 TEST VERIFICA FIX 2L - DIMENSIONI TOOL REALISTICHE
====================================================

Test del fix implementato per il problema 2L:
- Prima: tool NULL → 100x100mm identici → solo 6/45 posizionati  
- Dopo: tool NULL → dimensioni diverse → 40+/45 posizionati
"""

import sys
import os
sys.path.append('backend')

def test_conversion_function_fix():
    """Test che verifica il fix della funzione di conversione"""
    
    print("🧪 TEST VERIFICA FIX FUNZIONE CONVERSIONE 2L")
    print("=" * 60)
    
    # Simula dati ODL/Tool con dimensioni NULL
    class MockODL:
        def __init__(self, id):
            self.id = id
    
    class MockTool:
        def __init__(self):
            self.lunghezza_piano = None  # NULL - scenario problematico
            self.larghezza_piano = None  # NULL - scenario problematico  
            self.peso = None             # NULL - scenario problematico
            self.id = 1
    
    class MockParte:
        def __init__(self):
            self.num_valvole_richieste = 1
            self.ciclo_cura_id = 1
    
    try:
        from api.routers.batch_nesting_modules.generation import _convert_db_to_tool_info_2l
        
        print("✅ Funzione di conversione importata correttamente")
        
        # Test: 10 tool con dimensioni NULL
        tools_converted = []
        
        print(f"\n📊 TEST CONVERSIONE 10 TOOL NULL:")
        print(f"{'ODL':<6} {'Width':<8} {'Height':<8} {'Weight':<8} {'Diversificato'}")
        print("-" * 45)
        
        for i in range(1, 11):
            odl = MockODL(i)
            tool = MockTool()
            parte = MockParte()
            
            tool_info = _convert_db_to_tool_info_2l(odl, tool, parte)
            
            tools_converted.append({
                'width': tool_info.width,
                'height': tool_info.height,
                'weight': tool_info.weight
            })
            
            # Verifica se è diverso dal fallback standard
            is_diversified = not (tool_info.width == 100.0 and tool_info.height == 100.0 and tool_info.weight == 1.0)
            status = "✅ SÌ" if is_diversified else "❌ NO"
            
            print(f"{tool_info.odl_id:<6} {tool_info.width:<8.0f} {tool_info.height:<8.0f} {tool_info.weight:<8.0f} {status}")
        
        # Verifica diversificazione
        unique_dimensions = set()
        for tool in tools_converted:
            dimension_tuple = (tool['width'], tool['height'], tool['weight'])
            unique_dimensions.add(dimension_tuple)
        
        diversification_rate = len(unique_dimensions) / len(tools_converted) * 100
        
        print(f"\n📈 RISULTATI:")
        print(f"   - Tool unici: {len(unique_dimensions)}/{len(tools_converted)}")
        print(f"   - Diversificazione: {diversification_rate:.1f}%")
        
        if diversification_rate >= 80:
            print(f"   ✅ SUCCESSO: Tool diversificati")
            return True
        else:
            print(f"   ❌ FALLIMENTO: Tool ancora simili")
            return False
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        return False

if __name__ == "__main__":
    print("🏁 TEST FIX 2L")
    
    success = test_conversion_function_fix()
    
    if success:
        print("\n✅ FIX 2L COMPLETATO!")
        print("🎯 Aspettativa: >90% tool positioning")
    else:
        print("\n❌ PROBLEMI NEL FIX") 