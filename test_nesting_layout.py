#!/usr/bin/env python3
"""
Test script per verificare l'API del layout del nesting
"""

import sys
import os

# Aggiungi la directory backend al path
sys.path.append('./backend')

from fastapi.testclient import TestClient
from backend.main import app
import json

def test_nesting_layout_api():
    """Test dell'endpoint layout del nesting"""
    client = TestClient(app)
    
    try:
        # Prima prova a ottenere la lista dei nesting
        print("=== TEST NESTING LAYOUT API ===")
        response = client.get('/api/v1/nesting/')
        
        if response.status_code == 200:
            nesting_list = response.json()
            print(f"Trovati {len(nesting_list)} nesting nel database")
            
            if nesting_list and len(nesting_list) > 0:
                nesting_id = nesting_list[0]['id']
                print(f"Testando nesting ID: {nesting_id}")
                
                # Ora prova l'endpoint layout
                layout_response = client.get(f'/api/v1/nesting/{nesting_id}/layout')
                
                if layout_response.status_code == 200:
                    layout_data = layout_response.json()
                    print("\n=== LAYOUT RESPONSE ===")
                    
                    if 'layout_data' in layout_data:
                        ld = layout_data['layout_data']
                        
                        # Informazioni autoclave
                        autoclave = ld["autoclave"]
                        print(f"Autoclave: {autoclave['nome']}")
                        print(f"Dimensioni: {autoclave['lunghezza']}x{autoclave['larghezza_piano']}mm")
                        
                        # Informazioni ODL
                        print(f"ODL count: {len(ld['odl_list'])}")
                        if ld['odl_list']:
                            for i, odl in enumerate(ld['odl_list'][:3]):  # primi 3
                                tool = odl['tool']
                                print(f"  ODL {odl['id']}: Tool {tool['part_number_tool']} - {tool['lunghezza_piano']}x{tool['larghezza_piano']}mm")
                        
                        # Informazioni posizioni
                        print(f"Posizioni count: {len(ld['posizioni_tool'])}")
                        if ld['posizioni_tool']:
                            for i, pos in enumerate(ld['posizioni_tool'][:3]):  # prime 3
                                print(f"  Pos {i+1}: ODL {pos['odl_id']} at ({pos['x']:.1f}, {pos['y']:.1f}) size {pos['width']:.1f}x{pos['height']:.1f}mm")
                                if 'rotated' in pos:
                                    print(f"    Ruotato: {pos['rotated']}")
                                if 'piano' in pos:
                                    print(f"    Piano: {pos['piano']}")
                        
                        print("\n✅ API layout funziona correttamente!")
                        return True
                    else:
                        print("❌ No layout_data in response")
                        print(f"Response keys: {list(layout_data.keys())}")
                        return False
                else:
                    print(f"❌ Layout endpoint error: {layout_response.status_code}")
                    print(f"Response: {layout_response.text}")
                    return False
            else:
                print("❌ No nesting found in database")
                return False
        else:
            print(f"❌ Nesting list error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_nesting_layout_api() 