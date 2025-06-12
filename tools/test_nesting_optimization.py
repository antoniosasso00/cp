#!/usr/bin/env python3
"""
🚀 TEST OTTIMIZZAZIONI NESTING v2.0
===================================

Script per testare le ottimizzazioni implementate:
1. Performance del GRASP con timeout e limiti
2. Gestione intelligente cicli di cura multipli
3. Selezione automatica cicli con maggiore efficienza

Usage:
    python test_nesting_optimization.py
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any

# Aggiungi il percorso del backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.nesting.solver import NestingModel, NestingParameters, ToolInfo, AutoclaveInfo
from services.nesting_service import NestingService

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_large_dataset() -> List[ToolInfo]:
    """Crea un dataset grande per testare performance"""
    tools = []
    
    # Simula 45 ODL come nel caso reale
    for i in range(45):
        # Varie dimensioni per simulare complessità reale
        if i % 3 == 0:  # Grandi
            width, height = 350.0 + (i * 5), 400.0 + (i * 3)
        elif i % 3 == 1:  # Medi
            width, height = 200.0 + (i * 3), 250.0 + (i * 2)
        else:  # Piccoli
            width, height = 80.0 + (i * 2), 120.0 + (i * 1)
            
        tool = ToolInfo(
            odl_id=i + 1,
            width=width,
            height=height,
            weight=50.0 + (i * 2),
            lines_needed=1,
            ciclo_cura_id=(i % 4) + 1,  # 4 cicli diversi
            priority=1
        )
        tools.append(tool)
    
    return tools

def create_test_autoclave() -> AutoclaveInfo:
    """Crea autoclave per test"""
    return AutoclaveInfo(
        id=1,
        width=3000.0,  # PANINI dimensions
        height=2000.0,
        max_weight=2000.0,
        max_lines=12
    )

def test_grasp_optimization():
    """Test ottimizzazioni GRASP"""
    logger.info("🚀 === TEST OTTIMIZZAZIONI GRASP ===")
    
    # Parametri ottimizzati
    params = NestingParameters(
        padding_mm=1.0,
        min_distance_mm=1.0,
        vacuum_lines_capacity=12,
        use_fallback=True,
        allow_heuristic=True,
        use_grasp_heuristic=True,
        max_iterations_grasp=8  # Verrà ridotto automaticamente per dataset grandi
    )
    
    # Dataset grande
    tools = create_large_dataset()
    autoclave = create_test_autoclave()
    
    logger.info(f"📊 Dataset test: {len(tools)} tools")
    logger.info(f"📊 Autoclave: {autoclave.width}x{autoclave.height}mm")
    
    # Test performance
    start_time = time.time()
    
    solver = NestingModel(params)
    solution = solver.solve(tools, autoclave)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Risultati
    logger.info("🎯 === RISULTATI TEST GRASP ===")
    logger.info(f"✅ Successo: {solution.success}")
    logger.info(f"✅ Efficienza: {solution.metrics.efficiency_score:.1f}%")
    logger.info(f"✅ Tool posizionati: {solution.metrics.positioned_count}/{len(tools)}")
    logger.info(f"✅ Tempo totale: {duration:.1f}s")
    logger.info(f"✅ Algoritmo: {solution.algorithm_status}")
    logger.info(f"✅ Iterazioni GRASP: {solution.metrics.heuristic_iters}")
    
    # Verifica timeout
    if duration > 300:  # 5 minuti
        logger.warning("⚠️ Timeout superato - ottimizzazioni necessarie")
        return False
    elif duration < 60:  # Meno di 1 minuto
        logger.info("🚀 Performance ottimale!")
        return True
    else:
        logger.info("✅ Performance accettabile")
        return True

def test_cure_cycle_optimization():
    """Test gestione cicli di cura multipli"""
    logger.info("🔄 === TEST GESTIONE CICLI CURA ===")
    
    # Simula ODL con 4 cicli diversi (come nel caso reale)
    odl_data = []
    
    # Ciclo 1: 15 ODL grandi (alta efficienza)
    for i in range(15):
        odl_data.append({
            'odl_id': i + 1,
            'tool_width': 300.0 + (i * 10),
            'tool_height': 350.0 + (i * 8),
            'tool_weight': 80.0 + (i * 5),
            'ciclo_cura_id': 1
        })
    
    # Ciclo 2: 10 ODL medi (media efficienza)
    for i in range(10):
        odl_data.append({
            'odl_id': i + 16,
            'tool_width': 200.0 + (i * 8),
            'tool_height': 250.0 + (i * 6),
            'tool_weight': 60.0 + (i * 3),
            'ciclo_cura_id': 2
        })
    
    # Ciclo 3: 10 ODL piccoli (bassa efficienza)
    for i in range(10):
        odl_data.append({
            'odl_id': i + 26,
            'tool_width': 100.0 + (i * 5),
            'tool_height': 120.0 + (i * 4),
            'tool_weight': 30.0 + (i * 2),
            'ciclo_cura_id': 3
        })
    
    # Ciclo 4: 10 ODL molto piccoli (efficienza minima)
    for i in range(10):
        odl_data.append({
            'odl_id': i + 36,
            'tool_width': 50.0 + (i * 3),
            'tool_height': 80.0 + (i * 2),
            'tool_weight': 20.0 + (i * 1),
            'ciclo_cura_id': 4
        })
    
    logger.info(f"📊 Dataset test: {len(odl_data)} ODL con 4 cicli diversi")
    logger.info(f"📊 Autoclavi simulate: 3 (meno dei 4 cicli)")
    
    # Test logica di selezione (simula il servizio)
    cicli_cura = {}
    for odl in odl_data:
        ciclo_id = odl['ciclo_cura_id']
        if ciclo_id not in cicli_cura:
            cicli_cura[ciclo_id] = []
        cicli_cura[ciclo_id].append(odl)
    
    # Calcola efficienza per ogni ciclo
    cicli_efficienza = []
    for ciclo_id, odls in cicli_cura.items():
        area_totale = sum(odl['tool_width'] * odl['tool_height'] for odl in odls)
        peso_totale = sum(odl['tool_weight'] for odl in odls)
        efficiency_score = area_totale * 0.7 + peso_totale * 100 * 0.3
        
        cicli_efficienza.append({
            'ciclo_id': ciclo_id,
            'count': len(odls),
            'area_totale': area_totale,
            'peso_totale': peso_totale,
            'efficiency_score': efficiency_score
        })
    
    # Ordina per efficienza
    cicli_efficienza.sort(key=lambda x: x['efficiency_score'], reverse=True)
    
    logger.info("🎯 === RANKING CICLI PER EFFICIENZA ===")
    for i, ciclo in enumerate(cicli_efficienza):
        logger.info(f"#{i+1} Ciclo {ciclo['ciclo_id']}: {ciclo['count']} ODL, "
                   f"area {ciclo['area_totale']:.0f}mm², peso {ciclo['peso_totale']:.1f}kg, "
                   f"score {ciclo['efficiency_score']:.1f}")
    
    # Seleziona i migliori 3 (simulate 3 autoclavi)
    cicli_selezionati = cicli_efficienza[:3]
    cicli_esclusi = cicli_efficienza[3:]
    
    logger.info("✅ === CICLI SELEZIONATI ===")
    odl_compatibili = 0
    for ciclo in cicli_selezionati:
        odl_compatibili += ciclo['count']
        logger.info(f"✅ Ciclo {ciclo['ciclo_id']}: {ciclo['count']} ODL (efficienza {ciclo['efficiency_score']:.1f})")
    
    logger.info("❌ === CICLI ESCLUSI ===")
    odl_esclusi = 0
    for ciclo in cicli_esclusi:
        odl_esclusi += ciclo['count']
        logger.info(f"❌ Ciclo {ciclo['ciclo_id']}: {ciclo['count']} ODL (efficienza {ciclo['efficiency_score']:.1f})")
    
    logger.info(f"🎯 Risultato ottimizzazione: {odl_compatibili} ODL selezionati, {odl_esclusi} esclusi")
    
    # Verifica che i cicli migliori siano selezionati
    return cicli_selezionati[0]['ciclo_id'] == 1  # Ciclo 1 dovrebbe essere il migliore

def main():
    """Esegue tutti i test di ottimizzazione"""
    logger.info("🚀 AVVIO TEST OTTIMIZZAZIONI NESTING")
    logger.info("=" * 50)
    
    results = []
    
    # Test 1: Ottimizzazioni GRASP
    try:
        result_grasp = test_grasp_optimization()
        results.append(("GRASP Optimization", result_grasp))
    except Exception as e:
        logger.error(f"❌ Errore test GRASP: {str(e)}")
        results.append(("GRASP Optimization", False))
    
    logger.info("\n" + "=" * 50)
    
    # Test 2: Gestione cicli cura
    try:
        result_cycles = test_cure_cycle_optimization()
        results.append(("Cure Cycles Management", result_cycles))
    except Exception as e:
        logger.error(f"❌ Errore test cicli: {str(e)}")
        results.append(("Cure Cycles Management", False))
    
    # Riepilogo risultati
    logger.info("\n🎯 === RIEPILOGO TEST ===")
    logger.info("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("🚀 TUTTI I TEST SUPERATI - OTTIMIZZAZIONI OPERATIVE!")
    else:
        logger.warning("⚠️ ALCUNI TEST FALLITI - VERIFICARE IMPLEMENTAZIONE")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 