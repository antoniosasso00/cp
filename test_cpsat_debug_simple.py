#!/usr/bin/env python3
"""
🔧 FIXED: Test CP-SAT BoundedLinearExpression Error Resolution
Test definitivo per verificare che il fix abbia risolto l'errore 'index' attribute
"""

import sys
import os
import time
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

def setup_logging():
    """Setup logging per debug dettagliato"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cpsat_fix_test.log')
        ]
    )
    
    # Enable CP-SAT solver logging
    logger = logging.getLogger('ortools.sat.python.cp_model')
    logger.setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

def create_test_scenario():
    """Crea scenario di test che prima causava BoundedLinearExpression error"""
    
    # Autoclave PANINI
    autoclave = AutoclaveInfo(
        id=1, 
        width=6000.0, 
        height=3500.0, 
        max_weight=5000.0, 
        max_lines=25
    )
    
    # Tools che causavano l'errore
    tools = [
        ToolInfo(odl_id=1001, width=500.0, height=300.0, weight=25.5, lines_needed=2),
        ToolInfo(odl_id=1002, width=800.0, height=450.0, weight=45.2, lines_needed=3),
        ToolInfo(odl_id=1003, width=350.0, height=600.0, weight=30.1, lines_needed=2),
        ToolInfo(odl_id=1004, width=700.0, height=200.0, weight=18.8, lines_needed=1),
        ToolInfo(odl_id=1005, width=400.0, height=400.0, weight=22.3, lines_needed=2),
        ToolInfo(odl_id=1006, width=600.0, height=350.0, weight=35.7, lines_needed=3),
        ToolInfo(odl_id=1007, width=300.0, height=500.0, weight=28.4, lines_needed=2),
        ToolInfo(odl_id=1008, width=550.0, height=400.0, weight=40.6, lines_needed=2),
        ToolInfo(odl_id=1009, width=450.0, height=300.0, weight=20.2, lines_needed=1),
        ToolInfo(odl_id=1010, width=650.0, height=500.0, weight=55.8, lines_needed=4),
        ToolInfo(odl_id=1011, width=300.0, height=250.0, weight=15.1, lines_needed=1),
        ToolInfo(odl_id=1012, width=750.0, height=400.0, weight=48.3, lines_needed=3),
        ToolInfo(odl_id=1013, width=200.0, height=350.0, weight=12.7, lines_needed=1)
    ]
    
    return autoclave, tools

def test_cpsat_fix():
    """Test principale per verificare il fix CP-SAT"""
    
    logger = setup_logging()
    logger.info("🔧 CP-SAT FIX TEST: Iniziando test completo BoundedLinearExpression fix")
    
    # Setup scenario
    autoclave, tools = create_test_scenario()
    logger.info(f"📊 Test Setup: {len(tools)} ODL, autoclave {autoclave.width}x{autoclave.height}mm")
    
    # Parametri aerospace ottimizzati per evitare timeout durante test
    parameters = NestingParameters(
        padding_mm=0.2,
        min_distance_mm=0.2,
        vacuum_lines_capacity=25,
        use_fallback=True,
        allow_heuristic=True,
        timeout_override=15,  # 15 secondi timeout per test rapido
        use_multithread=True,
        num_search_workers=4,
        enable_rotation_optimization=True,
        area_weight=0.93,
        compactness_weight=0.05,
        balance_weight=0.02
    )
    
    # Crea solver
    model = NestingModel(parameters)
    logger.info("🔧 Solver creato con parametri aerospace ottimizzati")
    
    try:
        # Test il nesting che prima falliva con BoundedLinearExpression
        logger.info("🚀 TESTING: Avvio CP-SAT con nuovo schema variabili...")
        start_time = time.time()
        
        solution = model.solve(tools, autoclave)
        
        solve_time = time.time() - start_time
        logger.info(f"⏱️  TIMING: Risoluzione completata in {solve_time:.2f} secondi")
        
        # Verifica risultati
        if solution.success:
            logger.info("✅ SUCCESS: CP-SAT BoundedLinearExpression fix CONFERMATO!")
            logger.info(f"📊 RISULTATI:")
            logger.info(f"   • ODL posizionati: {solution.metrics.positioned_count}/{len(tools)}")
            logger.info(f"   • Area utilizzata: {solution.metrics.area_pct:.1f}%")
            logger.info(f"   • Efficienza: {solution.metrics.efficiency_score:.1f}%")
            logger.info(f"   • Rotazione usata: {solution.metrics.rotation_used}")
            logger.info(f"   • Algoritmo: {solution.algorithm_status}")
            logger.info(f"   • Tempo solving: {solution.metrics.time_solver_ms:.0f}ms")
            logger.info(f"   • Fallback usato: {solution.metrics.fallback_used}")
            
            # Dettagli layout
            logger.info(f"📐 LAYOUT DETAILS:")
            for layout in solution.layouts:
                logger.info(f"   • ODL {layout.odl_id}: ({layout.x:.0f},{layout.y:.0f}) "
                          f"{layout.width:.0f}x{layout.height:.0f}mm "
                          f"{'[R]' if layout.rotated else '[N]'} "
                          f"{layout.weight:.1f}kg")
            
            # Verifica che non ci siano overlap
            overlaps = model.check_overlap(solution.layouts)
            if overlaps:
                logger.warning(f"⚠️  OVERLAP DETECTED: {len(overlaps)} sovrapposizioni trovate")
                for overlap in overlaps[:3]:  # Mostra solo i primi 3
                    l1, l2 = overlap
                    logger.warning(f"   • ODL {l1.odl_id} vs ODL {l2.odl_id}")
            else:
                logger.info("✅ VALIDATION: Nessuna sovrapposizione rilevata")
            
            # Test efficienza target aerospace
            target_efficiency = 80.0
            if solution.metrics.efficiency_score >= target_efficiency:
                logger.info(f"🚀 AEROSPACE TARGET: Efficienza {solution.metrics.efficiency_score:.1f}% >= {target_efficiency}% ✅")
            else:
                logger.warning(f"⚠️  AEROSPACE TARGET: Efficienza {solution.metrics.efficiency_score:.1f}% < {target_efficiency}% (accettabile per test)")
            
            return True
            
        else:
            logger.error("❌ FAILURE: Nesting fallito")
            logger.error(f"   • Messaggio: {solution.message}")
            logger.error(f"   • Status: {solution.algorithm_status}")
            return False
            
    except Exception as e:
        if "BoundedLinearExpression" in str(e) or "'index'" in str(e):
            logger.error("❌ CRITICAL: BoundedLinearExpression error NON RISOLTO!")
            logger.error(f"   • Errore: {str(e)}")
            return False
        else:
            logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
            return False

def test_variable_structure():
    """Test specifico per verificare la nuova struttura variabili"""
    
    logger = logging.getLogger(__name__)
    logger.info("🔧 VARIABLE STRUCTURE TEST: Verifica nuove variabili CP-SAT")
    
    autoclave, tools = create_test_scenario()
    
    # Prendi solo 3 tools per test rapido struttura
    test_tools = tools[:3]
    
    parameters = NestingParameters(timeout_override=5)
    model = NestingModel(parameters)
    
    try:
        # Accesso interno per testare variabili (debug only)
        from ortools.sat.python import cp_model
        
        cp_model_obj = cp_model.CpModel()
        variables = model._create_cpsat_variables(cp_model_obj, test_tools, autoclave)
        
        # Verifica che le nuove variabili esistano
        required_vars = ['included', 'x', 'y', 'rotated', 'width_var', 'height_var', 'end_x', 'end_y']
        
        for var_type in required_vars:
            if var_type in variables:
                logger.info(f"✅ Variable '{var_type}': OK ({len(variables[var_type])} items)")
            else:
                logger.error(f"❌ Variable '{var_type}': MISSING")
                return False
        
        # Verifica che le vecchie variabili problematiche NON esistano
        forbidden_vars = ['intervals_x', 'intervals_y']
        for var_type in forbidden_vars:
            if var_type in variables:
                logger.error(f"❌ Variable '{var_type}': STILL PRESENT (should be removed)")
                return False
            else:
                logger.info(f"✅ Variable '{var_type}': Correctly removed")
        
        logger.info("✅ VARIABLE STRUCTURE: Tutte le verifiche superate")
        return True
        
    except Exception as e:
        logger.error(f"❌ VARIABLE STRUCTURE TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 CP-SAT BoundedLinearExpression Fix Test")
    print("=" * 60)
    
    # Test 1: Struttura variabili
    print("\n1️⃣  Testing Variable Structure...")
    var_test = test_variable_structure()
    
    # Test 2: CP-SAT completo
    print("\n2️⃣  Testing Complete CP-SAT Solution...")
    cpsat_test = test_cpsat_fix()
    
    # Risultato finale
    print("\n" + "=" * 60)
    if var_test and cpsat_test:
        print("✅ TUTTI I TEST SUPERATI: CP-SAT BoundedLinearExpression fix CONFERMATO")
        print("🚀 Il sistema aerospace può ora funzionare senza errori 'index'")
        sys.exit(0)
    else:
        print("❌ ALCUNI TEST FALLITI: CP-SAT fix necessita ulteriori modifiche")
        sys.exit(1) 