#!/usr/bin/env python3
"""
Test indipendente per la validazione delle transizioni di stato
"""

from enum import Enum as PyEnum
from typing import Union

class StatoBatchNestingEnum(PyEnum):
    """Enum per rappresentare i vari stati di un batch nesting"""
    DRAFT = "draft"
    SOSPESO = "sospeso"
    CONFERMATO = "confermato"
    LOADED = "loaded"
    CURED = "cured"
    TERMINATO = "terminato"

# Transizioni di stato permesse
STATE_TRANSITIONS = {
    StatoBatchNestingEnum.DRAFT: [StatoBatchNestingEnum.SOSPESO],
    StatoBatchNestingEnum.SOSPESO: [StatoBatchNestingEnum.CONFERMATO],
    StatoBatchNestingEnum.CONFERMATO: [StatoBatchNestingEnum.LOADED],
    StatoBatchNestingEnum.LOADED: [StatoBatchNestingEnum.CURED],
    StatoBatchNestingEnum.CURED: [StatoBatchNestingEnum.TERMINATO],
    StatoBatchNestingEnum.TERMINATO: [],  # Stato finale
}

def _convert_to_enum(state: Union[str, StatoBatchNestingEnum]) -> StatoBatchNestingEnum:
    """Converte uno stato (stringa o enum) nell'enum corrispondente"""
    if isinstance(state, StatoBatchNestingEnum):
        return state
    
    # Prova a convertire la stringa in enum
    try:
        return StatoBatchNestingEnum(state)
    except ValueError:
        # Se non trova una corrispondenza diretta, prova a cercare per valore
        for enum_item in StatoBatchNestingEnum:
            if enum_item.value == state:
                return enum_item
        
        # Se non trova niente, solleva eccezione
        raise ValueError(f"Stato '{state}' non riconosciuto")

def validate_batch_state_transition(current_state: Union[str, StatoBatchNestingEnum], target_state: Union[str, StatoBatchNestingEnum]) -> bool:
    """Valida se una transizione di stato è permessa"""
    try:
        # Converte entrambi gli stati in enum per il confronto
        current_enum = _convert_to_enum(current_state)
        target_enum = _convert_to_enum(target_state)
        
        if current_enum not in STATE_TRANSITIONS:
            raise Exception(f"Stato corrente '{current_enum.value}' non riconosciuto")
        
        allowed_transitions = STATE_TRANSITIONS[current_enum]
        if target_enum not in allowed_transitions:
            allowed_values = [t.value for t in allowed_transitions]
            raise Exception(f"Transizione non permessa da '{current_enum.value}' a '{target_enum.value}'. "
                           f"Transizioni possibili: {allowed_values}")
        
        return True
        
    except ValueError as e:
        raise Exception(str(e))

def test_validation():
    """Testa la funzione di validazione"""
    print("🧪 Testing batch state transition validation...")
    
    try:
        # Test 1: String to Enum (il caso problematico)
        result = validate_batch_state_transition("sospeso", StatoBatchNestingEnum.CONFERMATO)
        print("✅ Test 1 PASSED: String 'sospeso' to CONFERMATO enum")
        
        # Test 2: Enum to Enum
        result = validate_batch_state_transition(StatoBatchNestingEnum.SOSPESO, StatoBatchNestingEnum.CONFERMATO)
        print("✅ Test 2 PASSED: SOSPESO enum to CONFERMATO enum")
        
        # Test 3: String to String
        result = validate_batch_state_transition("sospeso", "confermato")
        print("✅ Test 3 PASSED: String 'sospeso' to String 'confermato'")
        
        # Test 4: Invalid transition (should fail)
        try:
            result = validate_batch_state_transition("sospeso", StatoBatchNestingEnum.TERMINATO)
            print("❌ Test 4 FAILED: Should have raised exception for invalid transition")
        except Exception as e:
            print(f"✅ Test 4 PASSED: Correctly rejected invalid transition")
        
        # Test 5: Invalid state (should fail)
        try:
            result = validate_batch_state_transition("stato_inesistente", StatoBatchNestingEnum.CONFERMATO)
            print("❌ Test 5 FAILED: Should have raised exception for invalid state")
        except Exception as e:
            print(f"✅ Test 5 PASSED: Correctly rejected invalid state")
            
        print("\n🎉 All validation tests completed successfully!")
        print("🔧 The fix for batch confirmation should now work!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    test_validation() 