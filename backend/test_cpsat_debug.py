#!/usr/bin/env python3
"""
Test di debug specifico per CP-SAT BoundedLinearExpression error
Identifica esattamente dove avviene l'errore per risolverlo definitivamente
"""

import logging
import sys
import os

# Aggiungi il percorso del backend al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

# Configurazione logging dettagliato
logging.basicConfig(
    level=logging.INFO,  # Meno verbose per output chiaro
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_cpsat_bounded_linear_expression():
    """Test specifico per identificare l'errore BoundedLinearExpression"""
    
    print("🔧 DEBUG CP-SAT - Test BoundedLinearExpression Error")
    print("=" * 60)
    
    # Parametri minimali per test
    parameters = NestingParameters(
        padding_mm=0.5,
        min_distance_mm=0.5,
        use_multithread=False,  # Single thread per debugging
        timeout_override=5      # 5 secondi timeout ridotto
    )
    
    # Tool di test semplice
    tools = [
        ToolInfo(
            odl_id=1,
            width=100.0,
            height=100.0,
            weight=10.0,
            lines_needed=1
        )
    ]
    
    # Autoclave di test
    autoclave = AutoclaveInfo(
        id=1,
        width=500.0,
        height=400.0,
        max_weight=100.0,
        max_lines=10
    )
    
    print(f"🔧 Tools: {len(tools)} pezzi")
    print(f"🔧 Autoclave: {autoclave.width}x{autoclave.height}mm")
    
    # Inizializza il solver
    solver = NestingModel(parameters)
    
    try:
        print("\n🚀 Avvio test CP-SAT con timeout ridotto...")
        
        # Prova diretta con CP-SAT per catturare l'errore esatto
        result = solver.solve(tools, autoclave)
        
        print(f"\n✅ RISULTATO:")
        print(f"   Success: {result.success}")
        print(f"   Algorithm: {result.algorithm_status}")
        print(f"   Layouts: {len(result.layouts)}")
        print(f"   Efficienza: {result.metrics.area_pct:.1f}%")
        print(f"   Message: {result.message}")
        
        if "CP-SAT" in result.algorithm_status and result.success:
            print("🎯 ✅ CP-SAT FUNZIONA CORRETTAMENTE!")
            return True
        elif "ERROR" in result.algorithm_status:
            print("🚨 ❌ CP-SAT ERROR - ERRORE PERSISTENTE")
            print(f"🚨 Message: {result.message}")
            return False
        else:
            print("⚠️ 🔄 CP-SAT ha attivato il fallback")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"\n🚨 ERRORE CATTURATO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Messaggio: {error_msg}")
        
        if "BoundedLinearExpression" in error_msg:
            print("🚨 CONFERMATO: Errore BoundedLinearExpression ancora presente!")
            
            # Stampa l'intero traceback per debugging
            import traceback
            print("\n🔍 TRACEBACK COMPLETO:")
            traceback.print_exc()
            return False
        else:
            print("🔧 Errore diverso da BoundedLinearExpression")
            return False
    
    print("\n" + "=" * 60)
    print("🔧 DEBUG CP-SAT completato")

if __name__ == "__main__":
    success = test_cpsat_bounded_linear_expression()
    if success:
        print("🎯 ✅ SUCCESS: CP-SAT funziona correttamente!")
        exit(0)
    else:
        print("🚨 ❌ FAILED: CP-SAT ha ancora problemi")
        exit(1) 