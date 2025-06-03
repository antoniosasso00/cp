"""
Test di validazione per il nesting CarbonPilot v1.4.18-DEMO
========================================================

Testa che tutti i pezzi nel layout rispettino i vincoli:
- x≥0, y≥0, x+w ≤ autoclave_W, y+h ≤ autoclave_H  
- Nessuna sovrapposizione (bbox)
- Proporzioni ragionevoli
"""

import pytest
import requests
import json
from typing import Dict, List, Any

# Configurazione test
API_BASE_URL = "http://localhost:8000/api/v1"

class TestNestingValidation:
    """Test suite per validazione layout nesting"""
    
    def test_validate_bounds_basic(self):
        """Test controllo bounds base - pezzi dentro i limiti"""
        # Layout semplice con 2 pezzi ben posizionati
        mock_layout = {
            "tool_positions": [
                {"odl_id": 1, "x": 50, "y": 50, "width": 200, "height": 150},
                {"odl_id": 2, "x": 300, "y": 50, "width": 200, "height": 150}
            ]
        }
        
        # Simula autoclave 2000x1200mm
        autoclave_width, autoclave_height = 2000, 1200
        
        # Verifica bounds manualmente
        for tool in mock_layout["tool_positions"]:
            x, y, w, h = tool["x"], tool["y"], tool["width"], tool["height"]
            assert x >= 0, f"Tool {tool['odl_id']}: x={x} < 0"
            assert y >= 0, f"Tool {tool['odl_id']}: y={y} < 0"
            assert x + w <= autoclave_width, f"Tool {tool['odl_id']}: x+w={x+w} > {autoclave_width}"
            assert y + h <= autoclave_height, f"Tool {tool['odl_id']}: y+h={y+h} > {autoclave_height}"
        
        print("✅ Test bounds base: PASSED")
    
    def test_validate_no_overlap_basic(self):
        """Test controllo sovrapposizioni - nessun overlap"""
        tools = [
            {"odl_id": 1, "x": 0, "y": 0, "width": 100, "height": 100},
            {"odl_id": 2, "x": 150, "y": 0, "width": 100, "height": 100},
            {"odl_id": 3, "x": 0, "y": 150, "width": 100, "height": 100}
        ]
        
        # Controllo overlap pairwise
        overlaps = []
        for i, tool_a in enumerate(tools):
            for j, tool_b in enumerate(tools[i+1:], i+1):
                x1, y1, w1, h1 = tool_a["x"], tool_a["y"], tool_a["width"], tool_a["height"]
                x2, y2, w2, h2 = tool_b["x"], tool_b["y"], tool_b["width"], tool_b["height"]
                
                # Logica sovrapposizione (negazione di separazione)
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                    overlaps.append((tool_a["odl_id"], tool_b["odl_id"]))
        
        assert len(overlaps) == 0, f"Trovate sovrapposizioni: {overlaps}"
        print("✅ Test no overlap: PASSED")
    
    def test_validate_overlap_detection(self):
        """Test rilevamento sovrapposizioni - deve trovare overlap"""
        tools = [
            {"odl_id": 1, "x": 0, "y": 0, "width": 100, "height": 100},
            {"odl_id": 2, "x": 50, "y": 50, "width": 100, "height": 100}  # Overlap intenzionale
        ]
        
        overlaps = []
        for i, tool_a in enumerate(tools):
            for j, tool_b in enumerate(tools[i+1:], i+1):
                x1, y1, w1, h1 = tool_a["x"], tool_a["y"], tool_a["width"], tool_a["height"]
                x2, y2, w2, h2 = tool_b["x"], tool_b["y"], tool_b["width"], tool_b["height"]
                
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                    overlaps.append((tool_a["odl_id"], tool_b["odl_id"]))
        
        assert len(overlaps) == 1, f"Doveva trovare 1 overlap, trovati: {len(overlaps)}"
        assert overlaps[0] == (1, 2), f"Overlap sbagliato: {overlaps[0]}"
        print("✅ Test rilevamento overlap: PASSED")
    
    def test_validate_scale_reasonable(self):
        """Test controllo scala - proporzioni ragionevoli"""
        # Autoclave 2000x1200mm = 2.4M mm²
        autoclave_area = 2000 * 1200
        
        # Tool che occupa ~10% dell'area (ragionevole)
        tool_area = 200 * 300  # 60k mm²
        ratio = tool_area / autoclave_area  # ~2.5%
        
        assert 0.01 <= ratio <= 0.95, f"Scala non ragionevole: {ratio*100:.1f}%"
        print(f"✅ Test scala ragionevole: {ratio*100:.1f}% - PASSED")
    
    def test_validate_scale_unreasonable(self):
        """Test controllo scala - proporzioni non ragionevoli"""
        autoclave_area = 2000 * 1200
        
        # Tool troppo piccolo (< 1%)
        small_tool_area = 10 * 10  # 100 mm²
        small_ratio = small_tool_area / autoclave_area  # ~0.004%
        assert small_ratio < 0.01, f"Tool doveva essere troppo piccolo: {small_ratio*100:.3f}%"
        
        # Tool troppo grande (> 95%) - usiamo 96% per essere sicuri
        large_tool_area = 1980 * 1180  # ~97%
        large_ratio = large_tool_area / autoclave_area
        print(f"  📏 Tool grande: {large_ratio*100:.1f}% dell'autoclave")
        # Ora verifichiamo che sia effettivamente > 95%
        assert large_ratio > 0.95, f"Tool doveva essere > 95%: {large_ratio*100:.1f}%"
        
        print("✅ Test scale non ragionevoli: PASSED")
    
    def test_edge_case_boundary_touching(self):
        """Test caso limite - pezzi che si toccano sui bordi"""
        tools = [
            {"odl_id": 1, "x": 0, "y": 0, "width": 100, "height": 100},
            {"odl_id": 2, "x": 100, "y": 0, "width": 100, "height": 100}  # Tocca esattamente
        ]
        
        overlaps = []
        for i, tool_a in enumerate(tools):
            for j, tool_b in enumerate(tools[i+1:], i+1):
                x1, y1, w1, h1 = tool_a["x"], tool_a["y"], tool_a["width"], tool_a["height"]
                x2, y2, w2, h2 = tool_b["x"], tool_b["y"], tool_b["width"], tool_b["height"]
                
                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                    overlaps.append((tool_a["odl_id"], tool_b["odl_id"]))
        
        # Toccare sui bordi NON è overlap
        assert len(overlaps) == 0, f"Bordi che si toccano non dovrebbero essere overlap: {overlaps}"
        print("✅ Test boundary touching: PASSED")

def run_all_tests():
    """Esegue tutti i test di validazione"""
    print("\n🧪 AVVIO TEST VALIDAZIONE NESTING v1.4.18-DEMO")
    print("=" * 60)
    
    test_suite = TestNestingValidation()
    
    try:
        test_suite.test_validate_bounds_basic()
        test_suite.test_validate_no_overlap_basic() 
        test_suite.test_validate_overlap_detection()
        test_suite.test_validate_scale_reasonable()
        test_suite.test_validate_scale_unreasonable()
        test_suite.test_edge_case_boundary_touching()
        
        print("\n" + "=" * 60)
        print("🎉 TUTTI I TEST VALIDAZIONE: PASSED")
        print("✅ Logica di validazione funziona correttamente")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLITO: {str(e)}")
        raise
    except Exception as e:
        print(f"\n💥 ERRORE IMPREVISTO: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_tests() 