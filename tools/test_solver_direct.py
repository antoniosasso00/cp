#!/usr/bin/env python3
"""
Test diretto del solver per verificare pre-filtering
"""

import sys
import logging
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test diretto del solver"""
    logger.info("🧪 TEST DIRETTO SOLVER - PEZZO GIGANTE")
    logger.info("=" * 50)
    
    # Crea tool gigante (come nel database)
    giant_tool = ToolInfo(
        odl_id=1,
        width=2500.0,   # lunghezza_piano dal database
        height=1500.0,  # larghezza_piano dal database  
        weight=100.0,
        lines_needed=5,
        priority=5
    )
    
    # Crea autoclave (come nel database)
    autoclave = AutoclaveInfo(
        id=1,
        width=2000.0,   # lunghezza dal database
        height=1200.0,  # larghezza_piano dal database
        max_weight=800.0,
        max_lines=10
    )
    
    logger.info(f"🔍 Tool: {giant_tool.width}x{giant_tool.height}mm, {giant_tool.weight}kg")
    logger.info(f"🏭 Autoclave: {autoclave.width}x{autoclave.height}mm, {autoclave.max_weight}kg")
    
    # Test pre-filtering manuale
    margin = 15  # min_distance_mm
    fits_normal = (giant_tool.width + margin <= autoclave.width and 
                   giant_tool.height + margin <= autoclave.height)
    fits_rotated = (giant_tool.height + margin <= autoclave.width and 
                    giant_tool.width + margin <= autoclave.height)
    
    logger.info(f"🧮 Pre-filtering manuale:")
    logger.info(f"   Fits normal: {fits_normal} ({giant_tool.width + margin} <= {autoclave.width} && {giant_tool.height + margin} <= {autoclave.height})")
    logger.info(f"   Fits rotated: {fits_rotated} ({giant_tool.height + margin} <= {autoclave.width} && {giant_tool.width + margin} <= {autoclave.height})")
    
    if not fits_normal and not fits_rotated:
        logger.info("   ✅ CORRETTO: Tool dovrebbe essere escluso")
    else:
        logger.info("   ❌ PROBLEMA: Tool potrebbe essere accettato")
    
    # Test solver completo
    parameters = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=10,
        allow_heuristic=False,
        timeout_override=30
    )
    
    solver = NestingModel(parameters)
    
    logger.info("🚀 Esecuzione solver...")
    solution = solver.solve([giant_tool], autoclave)
    
    logger.info(f"📊 Risultato solver:")
    logger.info(f"   Successo: {solution.success}")
    logger.info(f"   Algoritmo: {solution.algorithm_status}")
    logger.info(f"   Pezzi posizionati: {solution.metrics.positioned_count}")
    logger.info(f"   Pezzi esclusi: {solution.metrics.excluded_count}")
    logger.info(f"   Efficienza: {solution.metrics.efficiency_score:.1f}%")
    
    if solution.excluded_odls:
        logger.info("🚫 Motivi esclusione:")
        for exc in solution.excluded_odls:
            logger.info(f"   - ODL {exc.get('odl_id')}: {exc.get('motivo')}")
    
    if solution.layouts:
        logger.info("📋 Layout posizionati:")
        for layout in solution.layouts:
            logger.info(f"   - ODL {layout.odl_id}: {layout.x},{layout.y} {layout.width}x{layout.height}mm")

if __name__ == "__main__":
    main() 