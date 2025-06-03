#!/usr/bin/env python3
"""
Edge Single Test Tool per CarbonPilot v1.4.17-DEMO
Script per testare lo scenario C di performance con 50 pezzi misti

Scenario Test: 50 pezzi misti con timeout 90s
Aspettativa: time < 90s, overlaps=[], efficiency ≥ 70%
"""

import sys
import os
import logging
import time
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from models.database import SessionLocal, engine
from models.models import Autoclave, ODL, Parte, Tool, Catalogo, CicloCura
from sqlalchemy.orm import Session

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione API
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 120  # secondi

def clear_existing_test_data(db: Session):
    """Pulisce dati di test esistenti per evitare conflitti"""
    logger.info("🧹 Pulizia dati test esistenti...")
    
    # Rimuovi ODL di test (range 8000-8099 per scenario C)
    db.query(ODL).filter(ODL.id.between(8000, 8099)).delete(synchronize_session=False)
    
    # Rimuovi parti di test  
    db.query(Parte).filter(Parte.id.between(8000, 8099)).delete(synchronize_session=False)
    
    # Rimuovi tool di test
    db.query(Tool).filter(Tool.id.between(8000, 8099)).delete(synchronize_session=False)
    
    # Rimuovi catalogo di test
    db.query(Catalogo).filter(Catalogo.part_number.like('PERF-%')).delete(synchronize_session=False)
    
    # Rimuovi autoclave di test
    db.query(Autoclave).filter(Autoclave.id == 8000).delete(synchronize_session=False)
    
    # Rimuovi ciclo cura di test
    db.query(CicloCura).filter(CicloCura.id == 8000).delete(synchronize_session=False)
    
    db.commit()
    logger.info("✅ Pulizia completata")

def create_test_autoclave(db: Session) -> Autoclave:
    """Crea autoclave di test grande per 50 pezzi"""
    logger.info("🏭 Creazione autoclave test per performance...")
    
    autoclave = Autoclave(
        id=8000,
        nome="Test-Autoclave-Performance",
        codice="PERF-STRESS-001",
        larghezza_piano=1500.0,  # mm - autoclave grande
        lunghezza=2000.0,        # mm - per contenere molti pezzi
        max_load_kg=2000.0,      # kg - capacità alta
        num_linee_vuoto=20,      # linee vuoto abbondanti
        temperatura_max=220.0,
        pressione_max=10.0,
        produttore="Test-Performance",
        anno_produzione=2024,
        stato="DISPONIBILE",
        use_secondary_plane=False,
        note="Autoclave per test performance v1.4.17-DEMO - Scenario C"
    )
    
    db.add(autoclave)
    db.commit()
    db.refresh(autoclave)
    
    logger.info(f"✅ Autoclave creata: {autoclave.nome} ({autoclave.larghezza_piano}×{autoclave.lunghezza}mm)")
    return autoclave

def create_test_ciclo_cura(db: Session) -> CicloCura:
    """Crea ciclo di cura di test"""
    logger.info("🔄 Creazione ciclo cura test...")
    
    ciclo = CicloCura(
        id=8000,
        nome="Test-Ciclo-Performance",
        temperatura_stasi1=200.0,
        pressione_stasi1=8.0,
        durata_stasi1=45,
        attiva_stasi2=False,
        descrizione="Ciclo di test per performance v1.4.17-DEMO"
    )
    
    db.add(ciclo)
    db.commit()
    db.refresh(ciclo)
    
    logger.info(f"✅ Ciclo cura creato: {ciclo.nome}")
    return ciclo

def create_performance_test_data(db: Session):
    """
    Crea 50 pezzi misti per test di performance
    
    Mix di dimensioni:
    - 20 pezzi piccoli: 50×100mm
    - 20 pezzi medi: 150×200mm  
    - 10 pezzi grandi: 300×400mm
    
    Alcuni richiedono rotazione per testare l'algoritmo completo
    """
    logger.info("📦 Creazione 50 pezzi misti per test performance...")
    
    # Crea ciclo cura
    ciclo_cura = create_test_ciclo_cura(db)
    
    # Configurazioni pezzi (width, height, peso_base, lines, categoria)
    piece_configs = []
    
    # 20 pezzi piccoli (50×100mm)
    for i in range(20):
        piece_configs.append({
            'width': 50.0,
            'height': 100.0,
            'peso_base': 5.0,
            'lines': 1,
            'categoria': 'piccoli',
            'rotatable': i % 3 == 0  # 1/3 ruotabili per variazione
        })
    
    # 20 pezzi medi (150×200mm)  
    for i in range(20):
        piece_configs.append({
            'width': 150.0,
            'height': 200.0,
            'peso_base': 15.0,
            'lines': 1,
            'categoria': 'medi',
            'rotatable': i % 2 == 0  # 1/2 ruotabili
        })
    
    # 10 pezzi grandi (300×400mm)
    for i in range(10):
        piece_configs.append({
            'width': 300.0,
            'height': 400.0,
            'peso_base': 30.0,
            'lines': 2,
            'categoria': 'grandi',
            'rotatable': True  # Tutti ruotabili per massimizzare complessità
        })
    
    # Crea i 50 pezzi
    for i, config in enumerate(piece_configs, 1):
        # Variazione dimensioni per rotazione se necessario
        if config['rotatable'] and i % 4 == 0:
            # Alcuni pezzi con dimensioni che forzano rotazione
            width = max(config['width'], config['height'])
            height = min(config['width'], config['height'])
        else:
            width = config['width']
            height = config['height']
        
        # Catalogo
        part_number = f"PERF-{config['categoria'].upper()}-{i:03d}"
        catalogo = Catalogo(
            part_number=part_number,
            descrizione=f"Performance Test Piece {i} - {config['categoria']} - v1.4.17-DEMO",
            categoria=f"Test-Performance-{config['categoria']}",
            sotto_categoria="v1.4.17-DEMO-ScenarioC",
            attivo=True,
            note=f"Pezzo #{i} per test performance - {width}×{height}mm"
        )
        db.add(catalogo)
        
        # Tool
        tool = Tool(
            id=8000 + i,
            part_number_tool=f"TOOL-PERF-{i:03d}",
            larghezza_piano=width,
            lunghezza_piano=height,
            peso=config['peso_base'] + (i * 0.5),  # Variazione peso graduale
            materiale="Alluminio" if i % 2 == 0 else "Acciaio",
            disponibile=True,
            descrizione=f"Tool performance test {i} - {width}×{height}mm - {config['categoria']}"
        )
        db.add(tool)
        
        # Parte
        parte = Parte(
            id=8000 + i,
            part_number=part_number,
            ciclo_cura_id=ciclo_cura.id,
            descrizione_breve=f"Performance Test {i} - {config['categoria']}",
            num_valvole_richieste=config['lines'],
            note_produzione=f"Test performance v1.4.17-DEMO piece {i} - {config['categoria']}"
        )
        db.add(parte)
        
        # ODL
        odl = ODL(
            id=8000 + i,
            parte_id=8000 + i,
            tool_id=8000 + i,
            status="Preparazione",
            priorita=i,  # Priorità crescente
            note=f"ODL performance test {i} - {config['categoria']} - v1.4.17-DEMO"
        )
        db.add(odl)
        
        if i % 10 == 0:  # Log ogni 10 pezzi
            logger.info(f"  ✅ Creati {i}/50 pezzi...")
    
    db.commit()
    logger.info("📦 50 pezzi test performance creati con successo")

def create_performance_test_scenario():
    """Crea lo scenario di test per la performance"""
    logger.info("🚀 AVVIO CREAZIONE SCENARIO TEST PERFORMANCE v1.4.17-DEMO")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Pulisci dati precedenti
        clear_existing_test_data(db)
        
        # Crea autoclave di test
        autoclave = create_test_autoclave(db)
        
        # Crea i 50 pezzi di test
        create_performance_test_data(db)
        
        logger.info("=" * 60)
        logger.info("🎉 SCENARIO TEST PERFORMANCE CREATO CON SUCCESSO!")
        logger.info("")
        logger.info("📋 RIASSUNTO SCENARIO:")
        logger.info(f"   🏭 Autoclave: {autoclave.nome} - {autoclave.larghezza_piano}×{autoclave.lunghezza}mm")
        logger.info(f"   📦 Pezzi: 50 misti (20 piccoli + 20 medi + 10 grandi)")
        logger.info(f"   🎯 ODL IDs: 8001-8050")
        logger.info(f"   ⏱️  Timeout: 90s")
        
        return autoclave.id
        
    except Exception as e:
        logger.error(f"❌ Errore durante la creazione dello scenario: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

def run_performance_test(autoclave_id: int) -> Dict[str, Any]:
    """Esegue il test di performance via API"""
    logger.info("🧪 AVVIO TEST PERFORMANCE...")
    
    # Prepara richiesta API
    odl_ids = list(range(8001, 8051))  # 8001-8050 = 50 ODL
    
    request_data = {
        "autoclave_id": autoclave_id,
        "odl_ids": odl_ids,
        "parameters": {
            "timeout_override": 90,  # Forza timeout 90s
            "allow_heuristic": True,  # Abilita RRGH
            "use_fallback": True     # Abilita BL-FFD fallback
        }
    }
    
    logger.info(f"📤 Richiesta nesting: {len(odl_ids)} ODL, timeout 90s")
    
    # Esegui richiesta con timing
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/batch_nesting/solve",
            json=request_data,
            timeout=API_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        api_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ API chiamata completata in {api_time:.2f}s")
            return {
                'success': True,
                'api_time': api_time,
                'response': result
            }
        else:
            logger.error(f"❌ API error {response.status_code}: {response.text}")
            return {
                'success': False,
                'api_time': api_time,
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        api_time = end_time - start_time
        logger.error(f"⏰ API timeout dopo {api_time:.2f}s")
        return {
            'success': False,
            'api_time': api_time,
            'error': "API timeout"
        }
    except Exception as e:
        end_time = time.time()
        api_time = end_time - start_time
        logger.error(f"💥 Errore API: {str(e)}")
        return {
            'success': False,
            'api_time': api_time,
            'error': str(e)
        }

def analyze_performance_results(test_result: Dict[str, Any]) -> Dict[str, Any]:
    """Analizza i risultati del test di performance"""
    logger.info("📊 ANALISI RISULTATI PERFORMANCE...")
    
    if not test_result['success']:
        return {
            'passed': False,
            'reason': f"Test fallito: {test_result['error']}",
            'metrics': {}
        }
    
    response = test_result['response']
    metrics = response.get('metrics', {})
    
    # Estrai metriche chiave
    api_time = test_result['api_time']
    solver_time_ms = metrics.get('time_solver_ms', 0)
    solver_time_s = solver_time_ms / 1000.0
    
    positioned_count = metrics.get('positioned_count', 0)
    total_pieces = 50
    excluded_count = metrics.get('excluded_count', total_pieces)
    
    efficiency_score = metrics.get('efficiency_score', 0.0)
    algorithm_status = metrics.get('algorithm_status', 'UNKNOWN')
    rotation_used = metrics.get('rotation_used', False)
    heuristic_iters = metrics.get('heuristic_iters', 0)
    
    # Verifica overlaps
    layouts = response.get('layouts', [])
    has_overlaps = len(response.get('overlaps', [])) > 0
    
    # Criteri di successo
    time_ok = solver_time_s < 90.0  # < 90s
    no_overlaps_ok = not has_overlaps
    efficiency_ok = efficiency_score >= 70.0  # ≥ 70%
    positioned_ok = positioned_count > 0  # Almeno qualche pezzo posizionato
    
    passed = time_ok and no_overlaps_ok and efficiency_ok and positioned_ok
    
    # Log risultati dettagliati
    logger.info(f"⏱️  Timing: API {api_time:.2f}s, Solver {solver_time_s:.2f}s")
    logger.info(f"📦 Posizionamento: {positioned_count}/{total_pieces} pezzi ({(positioned_count/total_pieces)*100:.1f}%)")
    logger.info(f"📊 Efficienza: {efficiency_score:.1f}%")
    logger.info(f"🔄 Rotazione: {rotation_used}")
    logger.info(f"🚀 RRGH iterazioni: {heuristic_iters}")
    logger.info(f"⚙️  Algoritmo: {algorithm_status}")
    logger.info(f"🎯 Overlap: {'❌ Presenti' if has_overlaps else '✅ Nessuno'}")
    
    # Criteri dettagliati
    logger.info("")
    logger.info("🧪 CRITERI VALIDAZIONE:")
    logger.info(f"   ⏱️  Tempo < 90s: {'✅' if time_ok else '❌'} ({solver_time_s:.1f}s)")
    logger.info(f"   🎯 Nessun overlap: {'✅' if no_overlaps_ok else '❌'}")
    logger.info(f"   📊 Efficienza ≥ 70%: {'✅' if efficiency_ok else '❌'} ({efficiency_score:.1f}%)")
    logger.info(f"   📦 Pezzi posizionati: {'✅' if positioned_ok else '❌'} ({positioned_count})")
    
    return {
        'passed': passed,
        'reason': 'Test superato' if passed else 'Uno o più criteri falliti',
        'metrics': {
            'api_time_s': api_time,
            'solver_time_s': solver_time_s,
            'positioned_count': positioned_count,
            'total_pieces': total_pieces,
            'efficiency_score': efficiency_score,
            'has_overlaps': has_overlaps,
            'rotation_used': rotation_used,
            'heuristic_iters': heuristic_iters,
            'algorithm_status': algorithm_status,
            'criteria': {
                'time_ok': time_ok,
                'no_overlaps_ok': no_overlaps_ok,
                'efficiency_ok': efficiency_ok,
                'positioned_ok': positioned_ok
            }
        }
    }

def main():
    """Main function"""
    try:
        # Fase 1: Crea scenario test
        logger.info("🎬 FASE 1: CREAZIONE SCENARIO")
        autoclave_id = create_performance_test_scenario()
        
        if not autoclave_id:
            print("❌ Creazione scenario fallita!")
            sys.exit(1)
        
        # Fase 2: Esegui test performance
        logger.info("")
        logger.info("🎬 FASE 2: ESECUZIONE TEST")
        test_result = run_performance_test(autoclave_id)
        
        # Fase 3: Analizza risultati
        logger.info("")
        logger.info("🎬 FASE 3: ANALISI RISULTATI")
        analysis = analyze_performance_results(test_result)
        
        # Report finale
        logger.info("")
        logger.info("=" * 60)
        if analysis['passed']:
            logger.info("🎉 TEST PERFORMANCE SUPERATO!")
            print("✅ Test performance v1.4.17-DEMO SUPERATO!")
            print(f"📊 Efficienza: {analysis['metrics']['efficiency_score']:.1f}%")
            print(f"⏱️  Tempo: {analysis['metrics']['solver_time_s']:.1f}s")
            print(f"📦 Posizionati: {analysis['metrics']['positioned_count']}")
            sys.exit(0)
        else:
            logger.error("❌ TEST PERFORMANCE FALLITO!")
            print("❌ Test performance v1.4.17-DEMO FALLITO!")
            print(f"🔍 Motivo: {analysis['reason']}")
            if 'metrics' in analysis:
                print(f"📊 Efficienza: {analysis['metrics'].get('efficiency_score', 0):.1f}%")
                print(f"⏱️  Tempo: {analysis['metrics'].get('solver_time_s', 0):.1f}s")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Test interrotto dall'utente")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Errore imprevisto: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 