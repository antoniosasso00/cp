#!/usr/bin/env python3
"""
CarbonPilot - Script di Seed Test Data v1.4.12-DEMO
Genera scenario di test per algoritmo nesting potenziato

Scenario: 20 pezzi, capacità linee vuoto = 8, atteso:
- area ≥ 75%
- efficiency_score ≥ 70%
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base
from backend.models.autoclave import Autoclave, StatoAutoclaveEnum
from backend.models.catalogo import Catalogo
from backend.models.ciclo_cura import CicloCura
from backend.models.parte import Parte
from backend.models.tool import Tool
from backend.models.odl import ODL
import random
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione database
DATABASE_URL = "sqlite:///../backend/carbonpilot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_scenario():
    """
    Crea scenario di test v1.4.12-DEMO con 20 pezzi ottimizzato per autoclavi aeronautiche
    """
    
    db = SessionLocal()
    
    try:
        logger.info("🚀 Inizializzo scenario test v1.4.12-DEMO")
        
        # 1. Crea autoclave di test aeronautica
        autoclave = db.query(Autoclave).filter(Autoclave.nome == "AeroTest-v1.4.12").first()
        if not autoclave:
            autoclave = Autoclave(
                nome="AeroTest-v1.4.12",
                codice="AERO-TEST-DEMO",
                produttore="TestCorp Aerospace",
                anno_produzione=2023,
                larghezza_piano=1200.0,  # 1.2m larghezza
                lunghezza=2000.0,        # 2m lunghezza  
                temperatura_max=200.0,   # 200°C max
                pressione_max=8.0,       # 8 bar max
                max_load_kg=500.0,       # 500kg carico max
                num_linee_vuoto=8,       # IMPORTANTE: 8 linee per test
                stato=StatoAutoclaveEnum.DISPONIBILE,
                note="Autoclave test per algoritmo v1.4.12-DEMO"
            )
            db.add(autoclave)
            db.flush()
            logger.info(f"✅ Autoclave creata: {autoclave.nome} ({autoclave.larghezza_piano}x{autoclave.lunghezza}mm)")
        
        # 2. Crea ciclo di cura standard aeronautico
        ciclo = db.query(CicloCura).filter(CicloCura.nome == "Aeronautico-Standard-DEMO").first()
        if not ciclo:
            ciclo = CicloCura(
                nome="Aeronautico-Standard-DEMO",
                descrizione="Ciclo standard per componenti aeronautici - test DEMO",
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,  # 2 ore
                attiva_stasi2=False
            )
            db.add(ciclo)
            db.flush()
            logger.info(f"✅ Ciclo cura creato: {ciclo.nome}")
        
        # 3. Crea catalogo part numbers aeronautici
        part_numbers = [
            ("WING-BRACKET-L", "Supporto ala sinistra", "Strutturale", "Brackets"),
            ("WING-BRACKET-R", "Supporto ala destra", "Strutturale", "Brackets"), 
            ("ENGINE-MOUNT-F", "Attacco motore frontale", "Propulsione", "Mounts"),
            ("ENGINE-MOUNT-R", "Attacco motore posteriore", "Propulsione", "Mounts"),
            ("LANDING-GEAR-M", "Carrello principale", "Train Atterraggio", "Main Gear"),
            ("LANDING-GEAR-N", "Carrello di prua", "Train Atterraggio", "Nose Gear"),
            ("CONTROL-SURF-A", "Superficie controllo A", "Controlli", "Surfaces"),
            ("CONTROL-SURF-B", "Superficie controllo B", "Controlli", "Surfaces"),
            ("FUEL-TANK-P", "Serbatoio carburante primario", "Combustibile", "Tanks"),
            ("FUEL-TANK-S", "Serbatoio carburante secondario", "Combustibile", "Tanks"),
            ("CABIN-PANEL-F", "Pannello cabina frontale", "Interni", "Panels"),
            ("CABIN-PANEL-R", "Pannello cabina posteriore", "Interni", "Panels"),
            ("AVIONICS-BOX-1", "Scatola avionica primaria", "Elettronica", "Boxes"),
            ("AVIONICS-BOX-2", "Scatola avionica secondaria", "Elettronica", "Boxes"),
            ("THERMAL-SHIELD", "Schermo termico", "Protezione", "Shields")
        ]
        
        for part_num, desc, cat, subcat in part_numbers:
            if not db.query(Catalogo).filter(Catalogo.part_number == part_num).first():
                catalogo = Catalogo(
                    part_number=part_num,
                    descrizione=desc,
                    categoria=cat,
                    sotto_categoria=subcat,
                    attivo=True
                )
                db.add(catalogo)
        
        db.flush()
        logger.info(f"✅ Catalogo aggiornato con {len(part_numbers)} part numbers aeronautici")
        
        # 4. Crea parti con ciclo cura associato
        parti_configs = [
            ("WING-BRACKET-L", "Supporto ala sinistra - produzione", 2),
            ("WING-BRACKET-R", "Supporto ala destra - produzione", 2),
            ("ENGINE-MOUNT-F", "Attacco motore frontale - produzione", 3),
            ("ENGINE-MOUNT-R", "Attacco motore posteriore - produzione", 3),
            ("LANDING-GEAR-M", "Carrello principale - produzione", 4),
            ("LANDING-GEAR-N", "Carrello di prua - produzione", 4),
            ("CONTROL-SURF-A", "Superficie controllo A - produzione", 1),
            ("CONTROL-SURF-B", "Superficie controllo B - produzione", 1),
            ("FUEL-TANK-P", "Serbatoio primario - produzione", 3),
            ("FUEL-TANK-S", "Serbatoio secondario - produzione", 2),
            ("CABIN-PANEL-F", "Pannello cabina frontale - produzione", 1),
            ("CABIN-PANEL-R", "Pannello cabina posteriore - produzione", 1),
            ("AVIONICS-BOX-1", "Scatola avionica 1 - produzione", 2),
            ("AVIONICS-BOX-2", "Scatola avionica 2 - produzione", 2),
            ("THERMAL-SHIELD", "Schermo termico - produzione", 1)
        ]
        
        parti_create = []
        for part_num, desc_breve, valvole in parti_configs:
            parte = db.query(Parte).filter(Parte.part_number == part_num).first()
            if not parte:
                parte = Parte(
                    part_number=part_num,
                    descrizione_breve=desc_breve,
                    ciclo_cura_id=ciclo.id,
                    num_valvole_richieste=valvole,
                    note_produzione=f"Configurazione test DEMO - {valvole} linee vuoto"
                )
                db.add(parte)
                parti_create.append(parte)
        
        db.flush()
        logger.info(f"✅ Parti create: {len(parti_create)}")
        
        # 5. Crea tools con dimensioni ottimizzate per scenario test
        tool_configs = [
            ("WING-BRACKET-L", 350, 280, 15.0),      # Tool grandi strutturali
            ("WING-BRACKET-R", 350, 280, 15.0), 
            ("ENGINE-MOUNT-F", 400, 300, 25.0),      # Tool motore (pesanti)
            ("ENGINE-MOUNT-R", 400, 300, 25.0),
            ("LANDING-GEAR-M", 450, 350, 35.0),      # Tool carrello (molto pesanti)
            ("LANDING-GEAR-N", 300, 250, 20.0),
            ("CONTROL-SURF-A", 600, 200, 12.0),      # Tool superfici (lunghi)
            ("CONTROL-SURF-B", 600, 200, 12.0),
            ("FUEL-TANK-P", 500, 400, 30.0),         # Tool serbatoi (grandi)
            ("FUEL-TANK-S", 400, 350, 25.0),
            ("CABIN-PANEL-F", 300, 300, 8.0),        # Tool pannelli (leggeri)
            ("CABIN-PANEL-R", 300, 300, 8.0),
            ("AVIONICS-BOX-1", 200, 150, 5.0),       # Tool elettronica (piccoli)
            ("AVIONICS-BOX-2", 200, 150, 5.0),
            ("THERMAL-SHIELD", 800, 150, 10.0)       # Tool schermo (lungo sottile)
        ]
        
        tools_create = []
        for part_num, width, height, weight in tool_configs:
            tool_part_num = f"TOOL-{part_num}"
            tool = db.query(Tool).filter(Tool.part_number_tool == tool_part_num).first()
            if not tool:
                tool = Tool(
                    part_number_tool=tool_part_num,
                    descrizione=f"Tool per {part_num} - test DEMO",
                    larghezza_piano=float(width),
                    lunghezza_piano=float(height),
                    peso=float(weight),
                    materiale="Alluminio 7075" if weight < 20 else "Acciaio Inox",
                    disponibile=True,
                    note=f"Tool test scenario DEMO - {width}x{height}mm, {weight}kg"
                )
                db.add(tool)
                tools_create.append(tool)
        
        db.flush()
        logger.info(f"✅ Tools creati: {len(tools_create)}")
        
        # 6. Associa tools alle parti
        for parte in db.query(Parte).filter(Parte.part_number.in_([p[0] for p in parti_configs])):
            tool_part_num = f"TOOL-{parte.part_number}"
            tool = db.query(Tool).filter(Tool.part_number_tool == tool_part_num).first()
            if tool and parte.part_number not in [t.part_number for t in tool.parti]:
                tool.parti.append(parte)
        
        # 7. Crea 20 ODL per il test (alcuni duplicati per raggiungere 20)
        odl_configs = [
            ("WING-BRACKET-L", 1), ("WING-BRACKET-R", 1),
            ("ENGINE-MOUNT-F", 2), ("ENGINE-MOUNT-R", 2),
            ("LANDING-GEAR-M", 1), ("LANDING-GEAR-N", 1),
            ("CONTROL-SURF-A", 1), ("CONTROL-SURF-B", 1),
            ("FUEL-TANK-P", 1), ("FUEL-TANK-S", 1),
            ("CABIN-PANEL-F", 2), ("CABIN-PANEL-R", 2),
            ("AVIONICS-BOX-1", 2), ("AVIONICS-BOX-2", 2),
            ("THERMAL-SHIELD", 1), ("WING-BRACKET-L", 1)  # Duplicati per raggiungere 20
        ]
        
        # Aggiungi qualche ODL extra per raggiungere esattamente 20
        extra_parts = ["ENGINE-MOUNT-F", "CABIN-PANEL-F", "AVIONICS-BOX-1", "LANDING-GEAR-M"]
        for part_num in extra_parts:
            odl_configs.append((part_num, 1))
        
        odls_create = []
        for i, (part_num, priority) in enumerate(odl_configs[:20]):  # Limita a 20 ODL
            parte = db.query(Parte).filter(Parte.part_number == part_num).first()
            tool_part_num = f"TOOL-{part_num}"
            tool = db.query(Tool).filter(Tool.part_number_tool == tool_part_num).first()
            
            if parte and tool:
                odl = ODL(
                    parte_id=parte.id,
                    tool_id=tool.id,
                    status="Preparazione",
                    priorita=priority,
                    note=f"ODL test scenario DEMO #{i+1} - {part_num}"
                )
                db.add(odl)
                odls_create.append(odl)
        
        db.commit()
        logger.info(f"✅ ODL creati: {len(odls_create)}")
        
        # 8. Riepilogo scenario - CALCOLO DIRETTO DELLE PROPRIETÀ
        # Calcolo le proprietà direttamente senza refresh
        total_area_autoclave = 1200.0 * 2000.0  # larghezza_piano * lunghezza 
        autoclave_max_load = 500.0  # max_load_kg
        autoclave_num_linee = 8  # num_linee_vuoto
        autoclave_id = autoclave.id
        autoclave_width = 1200.0  # larghezza_piano
        autoclave_length = 2000.0  # lunghezza
        
        total_area_tools = sum(tool.larghezza_piano * tool.lunghezza_piano for tool in tools_create)
        total_weight_tools = sum(tool.peso for tool in tools_create)
        total_valvole = sum(parte.num_valvole_richieste for parte in parti_create)
        
        logger.info(f"""
🎯 SCENARIO TEST v1.4.12-DEMO COMPLETATO
========================================
📐 Autoclave: {autoclave_width}x{autoclave_length}mm = {total_area_autoclave/10000:.1f}m²
🔧 Tools: {len(tools_create)} pezzi, area totale {total_area_tools/10000:.1f}m²
⚖️ Peso totale tools: {total_weight_tools:.1f}kg (limite {autoclave_max_load}kg)
🔌 Linee vuoto totali richieste: {total_valvole} (capacità {autoclave_num_linee})
📋 ODL generati: {len(odls_create)}

🎯 TARGET ATTESI:
- Area utilizzata ≥ 75%
- Efficiency score ≥ 70%
- Peso entro limite {autoclave_max_load}kg
- Linee vuoto entro {autoclave_num_linee} linee

🚀 COMANDI TEST:
uvicorn backend.main:app --reload
POST /nesting/solve con autoclave_id={autoclave_id}
        """)
        
        return {
            "autoclave_id": autoclave_id,
            "odl_ids": [odl.id for odl in odls_create],
            "total_tools": len(tools_create),
            "total_weight": total_weight_tools,
            "autoclave_area": total_area_autoclave,
            "tools_area": total_area_tools,
            "coverage_potential": min(100, (total_area_tools / total_area_autoclave) * 100)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Errore durante setup scenario: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    scenario_info = setup_test_scenario()
    print(f"\n✅ Scenario pronto! Autoclave ID: {scenario_info['autoclave_id']}")
    print(f"📋 ODL IDs: {scenario_info['odl_ids']}")
    print(f"🎯 Copertura teorica massima: {scenario_info['coverage_potential']:.1f}%") 