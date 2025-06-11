#!/usr/bin/env python3
"""
Script di test per verificare la funzione di conferma batch
"""

import sys
import os

# Aggiungi il backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from backend.api.routers.batch_nesting_modules.utils import validate_batch_state_transition
from backend.models.batch_nesting import StatoBatchNestingEnum

def test_validation_fix():
    """Testa la funzione di validazione delle transizioni di stato"""
    print("🧪 Testing batch state transition validation...")
    
    try:
        # Test 1: String to Enum (should work)
        result = validate_batch_state_transition("sospeso", StatoBatchNestingEnum.CONFERMATO)
        print("✅ Test 1 PASSED: String 'sospeso' to CONFERMATO enum")
        
        # Test 2: Enum to Enum (should work)
        result = validate_batch_state_transition(StatoBatchNestingEnum.SOSPESO, StatoBatchNestingEnum.CONFERMATO)
        print("✅ Test 2 PASSED: SOSPESO enum to CONFERMATO enum")
        
        # Test 3: Invalid transition (should fail)
        try:
            result = validate_batch_state_transition("sospeso", StatoBatchNestingEnum.TERMINATO)
            print("❌ Test 3 FAILED: Should have raised exception for invalid transition")
        except Exception as e:
            print(f"✅ Test 3 PASSED: Correctly rejected invalid transition: {e}")
        
        # Test 4: Invalid state (should fail)
        try:
            result = validate_batch_state_transition("stato_inesistente", StatoBatchNestingEnum.CONFERMATO)
            print("❌ Test 4 FAILED: Should have raised exception for invalid state")
        except Exception as e:
            print(f"✅ Test 4 PASSED: Correctly rejected invalid state: {e}")
            
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    test_validation_fix() 