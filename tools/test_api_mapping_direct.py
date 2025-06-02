#!/usr/bin/env python3
"""
Test diretto del mapping API → Solver
Simula esattamente quello che fa l'API per verificare i fix
"""

import sys
import logging
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from api.database import get_db
from models.odl import ODL
from models.autoclave import Autoclave
from sqlalchemy.orm import joinedload
from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test diretto del mapping API → Solver con fix applicati"""
    logger.info("🧪 TEST MAPPING API → SOLVER CON FIX")
    logger.info("=" * 50)
    
    db = next(get_db())
    
    # 1. Recupera dati esattamente come fa l'API
    logger.info("📋 Recupero dati come API...")
    
    # Recupera autoclave
    autoclave = db.query(Autoclave).filter(Autoclave.id == 1).first()
    if not autoclave:
        logger.error("❌ Autoclave non trovata")
        return
    
    logger.info(f"🏭 Autoclave database: lunghezza={autoclave.lunghezza}, larghezza_piano={autoclave.larghezza_piano}")
    
    # Recupera ODL scenario A con "Attesa Cura" (nuovo filtro)
    odl_list = db.query(ODL).filter(
        ODL.id == 1,  # ODL scenario A
        ODL.status == "Attesa Cura"  # Nuovo filtro fix
    ).options(
        joinedload(ODL.parte),
        joinedload(ODL.tool)
    ).all()
    
    if not odl_list:
        logger.info("⚠️ Nessun ODL trovato con status 'Attesa Cura' - testando con qualsiasi status")
        
        # Prova con qualsiasi status per testare il mapping
        odl_list = db.query(ODL).filter(ODL.id == 1).options(
            joinedload(ODL.parte),
            joinedload(ODL.tool)
        ).all()
        
        if not odl_list:
            logger.error("❌ ODL ID 1 non esiste nel database")
            return
        else:
            logger.info(f"📋 ODL ID 1 trovato con status: '{odl_list[0].status}' - procedo con test mapping")
    
    logger.info(f"📋 Trovati {len(odl_list)} ODL per test mapping")
    
    # 2. Applica il mapping API → Solver (con FIX applicato)
    logger.info("🔄 Applicazione mapping API → Solver...")
    
    odl = odl_list[0]
    logger.info(f"🔍 Tool database: lunghezza_piano={odl.tool.lunghezza_piano}, larghezza_piano={odl.tool.larghezza_piano}")
    
    # ✅ MAPPING CORRETTO (POST-FIX)
    tool_info = ToolInfo(
        odl_id=odl.id,
        width=odl.tool.lunghezza_piano,   # FIX: lunghezza → width
        height=odl.tool.larghezza_piano,  # FIX: larghezza → height  
        weight=odl.tool.peso or 0.0,
        lines_needed=odl.parte.num_valvole_richieste or 1,
        ciclo_cura_id=odl.parte.ciclo_cura_id,
        priority=odl.priorita or 1
    )
    
    autoclave_info = AutoclaveInfo(
        id=autoclave.id,
        width=autoclave.lunghezza,         # FIX: lunghezza → width
        height=autoclave.larghezza_piano,  # FIX: larghezza_piano → height
        max_weight=autoclave.max_load_kg or 1000.0,
        max_lines=autoclave.num_linee_vuoto or 10
    )
    
    logger.info("📊 RISULTATO MAPPING:")
    logger.info(f"   Tool:      {tool_info.width}x{tool_info.height}mm ({tool_info.weight}kg)")
    logger.info(f"   Autoclave: {autoclave_info.width}x{autoclave_info.height}mm ({autoclave_info.max_weight}kg)")
    
    # 3. Verifica pre-filtering manuale
    logger.info("🧮 Test pre-filtering...")
    margin = 15
    fits_normal = (tool_info.width + margin <= autoclave_info.width and 
                   tool_info.height + margin <= autoclave_info.height)
    fits_rotated = (tool_info.height + margin <= autoclave_info.width and 
                    tool_info.width + margin <= autoclave_info.height)
    
    logger.info(f"   Fits normal:  {fits_normal} ({tool_info.width + margin} <= {autoclave_info.width} && {tool_info.height + margin} <= {autoclave_info.height})")
    logger.info(f"   Fits rotated: {fits_rotated} ({tool_info.height + margin} <= {autoclave_info.width} && {tool_info.width + margin} <= {autoclave_info.height})")
    
    should_be_excluded = not fits_normal and not fits_rotated
    logger.info(f"   Dovrebbe essere escluso: {should_be_excluded}")
    
    # 4. Test solver completo
    logger.info("🚀 Test solver con mapping corretto...")
    
    parameters = NestingParameters(
        padding_mm=20,
        min_distance_mm=15,
        vacuum_lines_capacity=10,
        allow_heuristic=False,
        timeout_override=30
    )
    
    solver = NestingModel(parameters)
    solution = solver.solve([tool_info], autoclave_info)
    
    logger.info("📊 RISULTATO FINALE:")
    logger.info(f"   Successo:           {solution.success}")
    logger.info(f"   Algoritmo:          {solution.algorithm_status}")
    logger.info(f"   Pezzi posizionati:  {solution.metrics.positioned_count}")
    logger.info(f"   Pezzi esclusi:      {solution.metrics.excluded_count}")
    logger.info(f"   Efficienza:         {solution.metrics.efficiency_score:.1f}%")
    
    if solution.excluded_odls:
        logger.info("🚫 Motivi esclusione:")
        for exc in solution.excluded_odls:
            logger.info(f"   - ODL {exc.get('odl_id')}: {exc.get('motivo')}")
    
    # 5. Valutazione finale
    logger.info("=" * 50)
    if should_be_excluded and not solution.success:
        logger.info("✅ FIX MAPPING CONFERMATO: Tool gigante correttamente escluso!")
        logger.info("✅ Il pre-filtering funziona con il mapping corretto")
    elif should_be_excluded and solution.success:
        logger.error("❌ PROBLEMA: Tool gigante dovrebbe essere escluso ma è stato posizionato")
        logger.error("❌ Il mapping o il pre-filtering hanno ancora problemi")
    else:
        logger.info("⚠️ Scenario non standard - verificare manualmente")
    
    db.close()

if __name__ == "__main__":
    main() 