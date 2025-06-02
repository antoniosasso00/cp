#!/usr/bin/env python3
"""
🧪 SANITY SEED v1.4.14-DEMO
===========================

Script per creare dati di test controllati per verificare il funzionamento
del nesting solver. Crea un scenario semplice e prevedibile:

- Autoclave: 1000mm × 2000mm (area ragionevole)
- 3 pezzi: 200×500mm ciascuno (dovrebbero entrare facilmente)
- 2 linee vuoto per pezzo (totale 6, sotto il limite di 10)

Risultato atteso:
- Tutti e 3 i pezzi posizionati
- Efficienza > 50%
- Nessun pezzo escluso per motivi di dimensioni
"""

import sys
import os
import logging
from datetime import datetime

# Aggiungi il path del backend per importare i moduli
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from api.database import get_db
from models.autoclave import Autoclave, StatoAutoclaveEnum
from models.odl import ODL
from models.parte import Parte
from models.tool import Tool
from models.ciclo_cura import CicloCura
from models.catalogo import Catalogo

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sanity_test_data():
    """
    Crea dati di test controllati per il nesting sanity check
    """
    logger.info("🧪 Creazione dati sanity test per nesting v1.4.14...")
    
    # Ottieni sessione database
    db = next(get_db())
    
    try:
        # 1. Crea autoclave di test (se non esiste)
        autoclave = db.query(Autoclave).filter(Autoclave.codice == "SANITY-TEST-v1.4.14").first()
        if not autoclave:
            autoclave = Autoclave(
                nome="Sanity Test Autoclave v1.4.14",
                codice="SANITY-TEST-v1.4.14",
                lunghezza=2000.0,  # 2000mm = 2m
                larghezza_piano=1000.0,  # 1000mm = 1m
                temperatura_max=200.0,
                pressione_max=8.0,
                max_load_kg=500.0,
                num_linee_vuoto=10,
                produttore="Test Manufacturer",
                anno_produzione=2024,
                stato=StatoAutoclaveEnum.DISPONIBILE,
                note="Autoclave creata per sanity test nesting v1.4.14"
            )
            db.add(autoclave)
            db.commit()
            db.refresh(autoclave)
            logger.info(f"✅ Creata autoclave: {autoclave.nome} (ID: {autoclave.id})")
        else:
            logger.info(f"📋 Autoclave esistente: {autoclave.nome} (ID: {autoclave.id})")
        
        # 2. Crea ciclo di cura di test (se non esiste)
        ciclo_cura = db.query(CicloCura).filter(CicloCura.nome == "Sanity Test Cycle").first()
        if not ciclo_cura:
            ciclo_cura = CicloCura(
                nome="Sanity Test Cycle",
                descrizione="Ciclo di cura per test sanity",
                durata_stasi1=60,
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                attiva_stasi2=False
            )
            db.add(ciclo_cura)
            db.commit()
            db.refresh(ciclo_cura)
            logger.info(f"✅ Creato ciclo cura: {ciclo_cura.nome} (ID: {ciclo_cura.id})")
        else:
            logger.info(f"📋 Ciclo cura esistente: {ciclo_cura.nome} (ID: {ciclo_cura.id})")
        
        # 3. Crea 3 pezzi di test
        test_pieces = []
        for i in range(1, 4):
            part_number = f"SANITY-PIECE-{i:02d}"
            
            # Crea catalogo entry (se non esiste)
            catalogo = db.query(Catalogo).filter(Catalogo.part_number == part_number).first()
            if not catalogo:
                catalogo = Catalogo(
                    part_number=part_number,
                    descrizione=f"Pezzo di test sanity #{i}",
                    categoria="Test",
                    sotto_categoria="Sanity",
                    attivo=True
                )
                db.add(catalogo)
                db.commit()
                db.refresh(catalogo)
            
            # Crea parte (se non esiste)
            parte = db.query(Parte).filter(Parte.part_number == part_number).first()
            if not parte:
                parte = Parte(
                    part_number=part_number,
                    descrizione_breve=f"Test piece {i} per sanity check",
                    ciclo_cura_id=ciclo_cura.id,
                    num_valvole_richieste=2,  # 2 linee vuoto per pezzo
                    note_produzione=f"Pezzo di test #{i} - dimensioni 200x500mm"
                )
                db.add(parte)
                db.commit()
                db.refresh(parte)
            
            # Crea tool (se non esiste)
            tool_part_number = f"TOOL-SANITY-{i:02d}"
            tool = db.query(Tool).filter(Tool.part_number_tool == tool_part_number).first()
            if not tool:
                tool = Tool(
                    part_number_tool=tool_part_number,
                    descrizione=f"Tool per test sanity piece {i}",
                    lunghezza_piano=500.0,  # 500mm lunghezza
                    larghezza_piano=200.0,  # 200mm larghezza
                    peso=25.0,  # 25kg (ragionevole)
                    materiale="Alluminio",
                    disponibile=True,
                    note=f"Tool di test per sanity check #{i}"
                )
                db.add(tool)
                db.commit()
                db.refresh(tool)
            
            # Crea ODL (se non esiste)
            odl = db.query(ODL).filter(
                ODL.parte_id == parte.id,
                ODL.tool_id == tool.id
            ).first()
            if not odl:
                odl = ODL(
                    parte_id=parte.id,
                    tool_id=tool.id,
                    status="Attesa Cura",  # Stato corretto per nesting
                    priorita=i,  # Priorità crescente
                    note=f"ODL di test sanity #{i}"
                )
                db.add(odl)
                db.commit()
                db.refresh(odl)
                logger.info(f"✅ Creato ODL #{i}: ID {odl.id}, tool {tool.lunghezza_piano}x{tool.larghezza_piano}mm")
            else:
                # Aggiorna stato se necessario
                if odl.status != "Attesa Cura":
                    odl.status = "Attesa Cura"
                    db.commit()
                logger.info(f"📋 ODL esistente #{i}: ID {odl.id}, tool {tool.lunghezza_piano}x{tool.larghezza_piano}mm")
            
            test_pieces.append({
                'odl_id': odl.id,
                'part_number': part_number,
                'tool_dimensions': f"{tool.lunghezza_piano}x{tool.larghezza_piano}mm",
                'weight': tool.peso,
                'lines_needed': parte.num_valvole_richieste
            })
        
        # 4. Riepilogo dati creati
        logger.info("🎯 SANITY TEST DATA SUMMARY:")
        logger.info(f"   Autoclave: {autoclave.nome} ({autoclave.lunghezza}x{autoclave.larghezza_piano}mm)")
        logger.info(f"   Area autoclave: {autoclave.lunghezza * autoclave.larghezza_piano / 10000:.1f} cm²")
        logger.info(f"   Capacità linee vuoto: {autoclave.num_linee_vuoto}")
        logger.info(f"   Peso massimo: {autoclave.max_load_kg}kg")
        logger.info("")
        logger.info("   Pezzi di test:")
        total_area = 0
        total_weight = 0
        total_lines = 0
        for piece in test_pieces:
            area = 500 * 200 / 10000  # cm²
            total_area += area
            total_weight += piece['weight']
            total_lines += piece['lines_needed']
            logger.info(f"     ODL {piece['odl_id']}: {piece['tool_dimensions']}, {piece['weight']}kg, {piece['lines_needed']} linee")
        
        logger.info("")
        logger.info(f"   TOTALI: {total_area:.1f} cm² ({total_area/(autoclave.lunghezza * autoclave.larghezza_piano / 10000)*100:.1f}% area)")
        logger.info(f"           {total_weight}kg ({total_weight/autoclave.max_load_kg*100:.1f}% peso)")
        logger.info(f"           {total_lines} linee ({total_lines/autoclave.num_linee_vuoto*100:.1f}% linee vuoto)")
        
        # 5. Informazioni per il test
        logger.info("")
        logger.info("🚀 READY FOR SANITY TEST:")
        logger.info(f"   Autoclave ID: {autoclave.id}")
        logger.info(f"   ODL IDs: {[p['odl_id'] for p in test_pieces]}")
        logger.info("")
        logger.info("📋 Test con comando:")
        logger.info(f'   curl -X POST "http://localhost:8000/batch_nesting/solve" \\')
        logger.info(f'        -H "Content-Type: application/json" \\')
        logger.info(f'        -d \'{{"autoclave_id": {autoclave.id}, "odl_ids": {[p["odl_id"] for p in test_pieces]}}}\'')
        logger.info("")
        logger.info("🎯 RISULTATO ATTESO:")
        logger.info("   - pieces_positioned: 3")
        logger.info("   - pieces_excluded: 0")
        logger.info("   - efficiency_score: > 50%")
        logger.info("   - algorithm_status: CP-SAT_OPTIMAL o FALLBACK_GREEDY")
        
        return {
            'autoclave_id': autoclave.id,
            'odl_ids': [p['odl_id'] for p in test_pieces],
            'expected_positioned': 3,
            'expected_excluded': 0,
            'min_efficiency': 50.0
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante creazione dati sanity: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        result = create_sanity_test_data()
        print("\n✅ Sanity test data creati con successo!")
        print(f"Autoclave ID: {result['autoclave_id']}")
        print(f"ODL IDs: {result['odl_ids']}")
        print("\n🧪 Ora puoi testare il nesting con questi dati controllati.")
        
    except Exception as e:
        print(f"\n❌ Errore: {str(e)}")
        sys.exit(1) 