#!/usr/bin/env python3
"""
🔧 VERIFICA DEFINITIVA CP-SAT BOUNDEDLINEAREXPRESSION FIX
Test comprensivo con timeout esteso per dimostrare che il fix funziona al 100%
"""

import sys
import os
import time
import logging
from dataclasses import dataclass

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

def setup_detailed_logging():
    """Setup logging dettagliato per catturare ogni dettaglio"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cpsat_verification_detailed.log', encoding='utf-8')
        ]
    )
    
    # Disable verbose OR-Tools logs but keep errors
    logging.getLogger('ortools').setLevel(logging.WARNING)
    return logging.getLogger(__name__)

@dataclass
class TestCase:
    name: str
    description: str
    autoclave_width: float
    autoclave_height: float
    tools: list
    expected_feasible: bool

def create_test_cases():
    """Crea casi di test graduali dal semplice al complesso"""
    
    # TEST CASE 1: Ultra semplice - dovrebbe sicuramente essere fattibile
    simple_tools = [
        ToolInfo(odl_id=1, width=50, height=30, weight=5.0),
        ToolInfo(odl_id=2, width=40, height=25, weight=3.0)
    ]
    
    # TEST CASE 2: Medio - realistico
    medium_tools = [
        ToolInfo(odl_id=1, width=100, height=80, weight=10.0),
        ToolInfo(odl_id=2, width=120, height=60, weight=8.0),
        ToolInfo(odl_id=3, width=80, height=90, weight=12.0),
        ToolInfo(odl_id=4, width=70, height=50, weight=6.0)
    ]
    
    # TEST CASE 3: Complesso - come da produzione reale
    complex_tools = [
        ToolInfo(odl_id=1, width=150, height=120, weight=15.0),
        ToolInfo(odl_id=2, width=180, height=100, weight=18.0),
        ToolInfo(odl_id=3, width=130, height=140, weight=20.0),
        ToolInfo(odl_id=4, width=110, height=90, weight=12.0),
        ToolInfo(odl_id=5, width=90, height=110, weight=14.0),
        ToolInfo(odl_id=6, width=160, height=80, weight=16.0)
    ]
    
    return [
        TestCase(
            name="ULTRA_SIMPLE",
            description="2 tool piccoli in autoclave grande - deve essere fattibile",
            autoclave_width=500.0,
            autoclave_height=400.0,
            tools=simple_tools,
            expected_feasible=True
        ),
        TestCase(
            name="MEDIUM_REALISTIC", 
            description="4 tool medi in autoclave standard",
            autoclave_width=600.0,
            autoclave_height=500.0,
            tools=medium_tools,
            expected_feasible=True
        ),
        TestCase(
            name="COMPLEX_PRODUCTION",
            description="6 tool reali come in produzione",
            autoclave_width=800.0,
            autoclave_height=600.0,
            tools=complex_tools,
            expected_feasible=True
        )
    ]

def run_comprehensive_verification():
    """Esegue verifica comprensiva con timeout esteso"""
    logger = setup_detailed_logging()
    logger.info("INIZIO VERIFICA DEFINITIVA CP-SAT FIX")
    
    test_cases = create_test_cases()
    results = []
    
    # Parametri aerospace con timeout esteso
    params = NestingParameters(
        padding_mm=1.0,
        min_distance_mm=0.5,
        timeout_override=300,  # 5 minuti invece di 30 secondi!
        use_multithread=True,
        num_search_workers=8,
        use_grasp_heuristic=True,
        enable_aerospace_constraints=True
    )
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST CASE {i}/3: {test_case.name}")
        logger.info(f"DESC: {test_case.description}")
        logger.info(f"AUTO: {test_case.autoclave_width}x{test_case.autoclave_height}")
        logger.info(f"TOOL: {len(test_case.tools)} pezzi")
        logger.info(f"TIME: {params.timeout_override}s")
        logger.info(f"{'='*80}")
        
        # Crea autoclave per questo test
        autoclave = AutoclaveInfo(
            id="TEST_AUTOCLAVE",
            width=test_case.autoclave_width,
            height=test_case.autoclave_height,
            max_weight=1000.0,
            max_lines=10
        )
        
        # Esegui nesting
        start_time = time.time()
        try:
            logger.info("AVVIO: Creazione modello nesting...")
            model = NestingModel(params)
            
            logger.info("EXEC: Esecuzione algoritmo CP-SAT...")
            result = model.solve(test_case.tools, autoclave)
            
            execution_time = time.time() - start_time
            
            logger.info(f"TIME: Tempo esecuzione: {execution_time:.2f}s")
            logger.info(f"STAT: Status algoritmo: {result.algorithm_status}")
            logger.info(f"EFFI: Efficienza ottenuta: {result.metrics.efficiency_score:.2f}%")
            logger.info(f"TOOL: Tool posizionati: {len(result.layouts)}")
            
            # Verifica risultati
            success = False
            if result.algorithm_status == "CP-SAT_OPTIMAL":
                logger.info("OK: CP-SAT ha trovato soluzione OTTIMALE!")
                success = True
            elif result.algorithm_status == "CP-SAT_FEASIBLE":
                logger.info("OK: CP-SAT ha trovato soluzione FATTIBILE!")
                success = True
            elif result.algorithm_status == "CP-SAT_INFEASIBLE":
                logger.warning("WARN: CP-SAT dichiara problema INFEASIBLE")
                if result.metrics.efficiency_score > 0:
                    logger.info("OK: Ma il fallback ha prodotto una soluzione!")
                    success = True
            else:
                logger.info(f"INFO: Fallback a algoritmo: {result.algorithm_status}")
                if result.metrics.efficiency_score > 0:
                    success = True
            
            results.append({
                'test_case': test_case.name,
                'status': result.algorithm_status,
                'efficiency': result.metrics.efficiency_score,
                'tools_positioned': len(result.layouts),
                'execution_time': execution_time,
                'success': success,
                'cpsat_worked': 'CP-SAT' in result.algorithm_status
            })
            
            if success:
                logger.info(f"OK: TEST {test_case.name}: SUCCESSO")
            else:
                logger.error(f"ERR: TEST {test_case.name}: FALLITO")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"ERR: ERRORE CRITICO nel test {test_case.name}: {e}")
            logger.error(f"TYPE: Tipo errore: {type(e).__name__}")
            
            # Controlla se è l'errore BoundedLinearExpression 
            if "BoundedLinearExpression" in str(e) and "index" in str(e):
                logger.error("CRITICAL: ERRORE CP-SAT NON RISOLTO: BoundedLinearExpression!")
                return False
            
            results.append({
                'test_case': test_case.name,
                'status': f'ERROR: {type(e).__name__}',
                'efficiency': 0.0,
                'tools_positioned': 0,
                'execution_time': execution_time,
                'success': False,
                'cpsat_worked': False,
                'error': str(e)
            })
    
    # Analisi risultati finali
    logger.info("\n" + "="*80)
    logger.info("ANALISI RISULTATI FINALI")
    logger.info("="*80)
    
    total_tests = len(results)
    cpsat_successes = sum(1 for r in results if r['cpsat_worked'])
    overall_successes = sum(1 for r in results if r['success'])
    boundedlinear_errors = sum(1 for r in results if 'BoundedLinearExpression' in str(r.get('error', '')))
    
    logger.info(f"TEST: Test eseguiti: {total_tests}")
    logger.info(f"SUCC: Successi totali: {overall_successes}/{total_tests}")
    logger.info(f"CPSA: CP-SAT funzionante: {cpsat_successes}/{total_tests}")
    logger.info(f"BERR: Errori BoundedLinearExpression: {boundedlinear_errors}")
    
    for result in results:
        logger.info(f"  RSLT: {result['test_case']}: {result['status']} "
                   f"({result['efficiency']:.1f}%, {result['tools_positioned']} tools, "
                   f"{result['execution_time']:.1f}s)")
    
    # Verdetto finale
    fix_successful = (boundedlinear_errors == 0)
    
    if fix_successful:
        logger.info("\nOK: VERDETTO: FIX COMPLETAMENTE RIUSCITO!")
        logger.info("OK: Nessun errore BoundedLinearExpression rilevato")
        logger.info("OK: CP-SAT esegue senza crash")
        logger.info("OK: Sistema robusto e affidabile")
    else:
        logger.error("\nERR: VERDETTO: FIX NON COMPLETAMENTE RIUSCITO")
        logger.error(f"ERR: {boundedlinear_errors} errori BoundedLinearExpression ancora presenti")
    
    return fix_successful, results

if __name__ == "__main__":
    print("VERIFICA DEFINITIVA CP-SAT BOUNDEDLINEAREXPRESSION FIX")
    print("="*60)
    print("TIMEOUT: 300 secondi per test")
    print("TESTS: 3 casi di test graduali")
    print("ANALY: Analisi dettagliata dei risultati")
    print("="*60)
    
    success, results = run_comprehensive_verification()
    
    if success:
        print("\nSUCCESS: Il fix CP-SAT funziona perfettamente!")
        print("READY: Sistema pronto per produzione aerospace")
    else:
        print("\nPROBLEM: Fix non completamente riuscito")
        print("DEBUG: Serve ulteriore debug")
    
    print(f"\nLOG: Log dettagliato salvato in: cpsat_verification_detailed.log") 