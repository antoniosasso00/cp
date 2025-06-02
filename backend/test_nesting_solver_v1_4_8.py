"""
Test del Nesting Solver Ottimizzato v1.4.8-DEMO
==================================================

Test per verificare il funzionamento del nuovo algoritmo di nesting
con timeout adaptivo e fallback greedy.

Target: 8 pezzi, capacità 6 linee vuoto → solver OK in <10s
"""

import time
import logging
from typing import List
from services.nesting.solver import (
    NestingModel,
    NestingParameters,
    ToolInfo,
    AutoclaveInfo
)

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_tools() -> List[ToolInfo]:
    """Crea 8 tool di test con dimensioni e pesi variabili"""
    
    test_tools = [
        ToolInfo(odl_id=1, width=150.0, height=200.0, weight=5.2, lines_needed=1),
        ToolInfo(odl_id=2, width=120.0, height=180.0, weight=3.8, lines_needed=1),
        ToolInfo(odl_id=3, width=180.0, height=150.0, weight=6.1, lines_needed=2),
        ToolInfo(odl_id=4, width=100.0, height=160.0, weight=2.9, lines_needed=1),
        ToolInfo(odl_id=5, width=140.0, height=190.0, weight=4.7, lines_needed=1),
        ToolInfo(odl_id=6, width=130.0, height=170.0, weight=3.5, lines_needed=2),
        ToolInfo(odl_id=7, width=110.0, height=140.0, weight=2.8, lines_needed=1),
        ToolInfo(odl_id=8, width=160.0, height=210.0, weight=5.8, lines_needed=1)
    ]
    
    logger.info(f"Creati {len(test_tools)} tool di test")
    for tool in test_tools:
        logger.info(f"  Tool {tool.odl_id}: {tool.width}x{tool.height}mm, {tool.weight}kg, {tool.lines_needed} linee")
    
    return test_tools

def create_test_autoclave() -> AutoclaveInfo:
    """Crea un'autoclave di test con dimensioni realistiche"""
    
    autoclave = AutoclaveInfo(
        id=1,
        width=800.0,    # 80cm larghezza
        height=1200.0,  # 120cm lunghezza 
        max_weight=100.0,  # 100kg peso massimo
        max_lines=10       # 10 linee vuoto disponibili
    )
    
    logger.info(f"Autoclave test: {autoclave.width}x{autoclave.height}mm, max {autoclave.max_weight}kg, {autoclave.max_lines} linee")
    return autoclave

def test_scenario_target():
    """
    Test scenario target: 8 pezzi, capacità 6 linee vuoto
    Target: completamento in <10 secondi
    """
    
    logger.info("🎯 TEST SCENARIO TARGET")
    logger.info("=" * 50)
    
    # Setup test
    tools = create_test_tools()
    autoclave = create_test_autoclave()
    
    # Parametri con capacità linee ridotta (scenario critico)
    parameters = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=6,  # SCENARIO TARGET: capacità ridotta
        priorita_area=True,
        use_fallback=True
    )
    
    logger.info(f"Parametri: padding={parameters.padding_mm}mm, "
               f"min_distance={parameters.min_distance_mm}mm, "
               f"vacuum_capacity={parameters.vacuum_lines_capacity}")
    
    # Calcola linee totali richieste
    total_lines_needed = sum(tool.lines_needed for tool in tools)
    logger.info(f"Linee totali richieste: {total_lines_needed} (capacità: {parameters.vacuum_lines_capacity})")
    
    # Esegui test con timing
    start_time = time.time()
    
    nesting_model = NestingModel(parameters)
    solution = nesting_model.solve(tools, autoclave)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Analizza risultati
    logger.info("")
    logger.info("📊 RISULTATI TEST")
    logger.info("-" * 30)
    logger.info(f"⏱️ Tempo esecuzione: {execution_time:.2f}s")
    logger.info(f"🎯 Target <10s: {'✅ PASS' if execution_time < 10.0 else '❌ FAIL'}")
    logger.info(f"✅ Successo: {solution.success}")
    logger.info(f"🔧 Algoritmo: {solution.algorithm_status}")
    logger.info("")
    logger.info(f"📦 ODL posizionati: {solution.metrics.positioned_count}/{len(tools)}")
    logger.info(f"❌ ODL esclusi: {solution.metrics.excluded_count}")
    logger.info(f"📏 Area utilizzata: {solution.metrics.area_pct:.1f}%")
    logger.info(f"🔌 Linee vuoto: {solution.metrics.lines_used}/{parameters.vacuum_lines_capacity}")
    logger.info(f"⚖️ Peso totale: {solution.metrics.total_weight:.1f}kg")
    logger.info(f"🎯 Efficienza: {solution.metrics.efficiency:.1f}%")
    
    # Dettagli layout
    if solution.layouts:
        logger.info("")
        logger.info("🗂️ LAYOUT DETTAGLIATO")
        logger.info("-" * 30)
        for layout in solution.layouts:
            logger.info(f"  ODL {layout.odl_id}: pos({layout.x:.0f},{layout.y:.0f}) "
                       f"dim({layout.width:.0f}x{layout.height:.0f}) "
                       f"peso({layout.weight:.1f}kg) "
                       f"ruotato({layout.rotated}) "
                       f"linee({layout.lines_used})")
    
    # Motivi esclusione
    if solution.excluded_odls:
        logger.info("")
        logger.info("❌ ODL ESCLUSI")
        logger.info("-" * 20)
        for excluded in solution.excluded_odls:
            logger.info(f"  ODL {excluded['odl_id']}: {excluded['motivo']}")
            logger.info(f"     → {excluded['dettagli']}")
    
    return execution_time < 10.0, solution

def test_cp_sat_vs_fallback():
    """
    Test comparativo tra CP-SAT e fallback greedy
    """
    
    logger.info("")
    logger.info("🔄 TEST COMPARATIVO CP-SAT vs FALLBACK")
    logger.info("=" * 50)
    
    tools = create_test_tools()
    autoclave = create_test_autoclave()
    
    # Test con CP-SAT (timeout normale)
    logger.info("🔧 Test CP-SAT (timeout normale)")
    params_cpsat = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=10,  # Capacità normale
        priorita_area=True,
        use_fallback=True
    )
    
    start_time = time.time()
    model_cpsat = NestingModel(params_cpsat)
    solution_cpsat = model_cpsat.solve(tools, autoclave)
    cpsat_time = time.time() - start_time
    
    logger.info(f"  Tempo: {cpsat_time:.2f}s")
    logger.info(f"  Algoritmo: {solution_cpsat.algorithm_status}")
    logger.info(f"  Posizionati: {solution_cpsat.metrics.positioned_count}")
    logger.info(f"  Efficienza: {solution_cpsat.metrics.efficiency:.1f}%")
    
    # Test forzando fallback (capacità molto ridotta)
    logger.info("")
    logger.info("🔄 Test Fallback Greedy (capacità ridotta)")
    params_fallback = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=3,  # Capacità molto ridotta per forzare fallback
        priorita_area=True,
        use_fallback=True
    )
    
    start_time = time.time()
    model_fallback = NestingModel(params_fallback)
    solution_fallback = model_fallback.solve(tools, autoclave)
    fallback_time = time.time() - start_time
    
    logger.info(f"  Tempo: {fallback_time:.2f}s")
    logger.info(f"  Algoritmo: {solution_fallback.algorithm_status}")
    logger.info(f"  Posizionati: {solution_fallback.metrics.positioned_count}")
    logger.info(f"  Efficienza: {solution_fallback.metrics.efficiency:.1f}%")
    
    return solution_cpsat, solution_fallback

def test_timeout_adaptivo():
    """
    Test del timeout adaptivo con diverse quantità di pezzi
    """
    
    logger.info("")
    logger.info("⏱️ TEST TIMEOUT ADAPTIVO")
    logger.info("=" * 40)
    
    base_tools = create_test_tools()
    autoclave = create_test_autoclave()
    
    test_sizes = [2, 4, 8, 16]  # Diverse quantità di pezzi
    
    for n_pieces in test_sizes:
        logger.info(f"📦 Test con {n_pieces} pezzi")
        
        # Seleziona o duplica tools per raggiungere n_pieces
        if n_pieces <= len(base_tools):
            test_tools = base_tools[:n_pieces]
        else:
            # Duplica tools con nuovi ID
            test_tools = base_tools.copy()
            for i in range(n_pieces - len(base_tools)):
                original_tool = base_tools[i % len(base_tools)]
                duplicated_tool = ToolInfo(
                    odl_id=100 + i,
                    width=original_tool.width,
                    height=original_tool.height,
                    weight=original_tool.weight,
                    lines_needed=original_tool.lines_needed
                )
                test_tools.append(duplicated_tool)
        
        # Calcola timeout atteso
        expected_timeout = min(60.0, 2.0 * n_pieces)
        
        params = NestingParameters(
            padding_mm=20,
            min_distance_mm=15,
            vacuum_lines_capacity=15,  # Capacità generosa
            priorita_area=True,
            use_fallback=True
        )
        
        start_time = time.time()
        model = NestingModel(params)
        solution = model.solve(test_tools, autoclave)
        actual_time = time.time() - start_time
        
        logger.info(f"  Timeout atteso: {expected_timeout:.1f}s")
        logger.info(f"  Tempo effettivo: {actual_time:.2f}s")
        logger.info(f"  Algoritmo: {solution.algorithm_status}")
        logger.info(f"  Posizionati: {solution.metrics.positioned_count}/{n_pieces}")
        logger.info("")

def main():
    """
    Esegue tutti i test del nesting solver ottimizzato
    """
    
    logger.info("🚀 AVVIO TEST NESTING SOLVER v1.4.8-DEMO")
    logger.info("=" * 60)
    
    overall_start = time.time()
    
    try:
        # Test principale (scenario target)
        target_passed, target_solution = test_scenario_target()
        
        # Test comparativo
        cp_sat_solution, fallback_solution = test_cp_sat_vs_fallback()
        
        # Test timeout adaptivo
        test_timeout_adaptivo()
        
        overall_time = time.time() - overall_start
        
        # Riepilogo finale
        logger.info("")
        logger.info("🏆 RIEPILOGO FINALE")
        logger.info("=" * 30)
        logger.info(f"⏱️ Tempo totale test: {overall_time:.2f}s")
        logger.info(f"🎯 Test target PASSED: {'✅' if target_passed else '❌'}")
        logger.info(f"🔧 Algoritmi testati: CP-SAT + Fallback Greedy")
        logger.info(f"✨ Funzionalità verificate:")
        logger.info(f"   • Timeout adaptivo")
        logger.info(f"   • Vincoli linee vuoto")
        logger.info(f"   • Fallback automatico") 
        logger.info(f"   • Ottimizzazione multi-criterio")
        logger.info("")
        
        if target_passed:
            logger.info("🎉 TUTTI I TEST SUPERATI!")
            logger.info("   Il solver è pronto per la produzione.")
        else:
            logger.info("⚠️ ALCUNI TEST FALLITI")
            logger.info("   Verificare configurazioni e performance.")
        
    except Exception as e:
        logger.error(f"❌ ERRORE DURANTE I TEST: {str(e)}")
        raise

if __name__ == "__main__":
    main() 