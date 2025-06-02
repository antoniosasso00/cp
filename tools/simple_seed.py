#!/usr/bin/env python3
"""
CarbonPilot - Script di Seed Test Data v1.4.12-DEMO Semplificato
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

# Configurazione database
DATABASE_URL = "sqlite:///../backend/carbonpilot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_test_data():
    """Crea i dati di test minimi per il nesting"""
    
    db = SessionLocal()
    
    try:
        print("🚀 Creo scenario test semplificato...")
        
        # 1. Crea autoclave di test
        autoclave = Autoclave(
            nome="AeroTest-v1.4.12",
            codice="AERO-TEST-DEMO", 
            produttore="TestCorp",
            anno_produzione=2023,
            larghezza_piano=1200.0,
            lunghezza=2000.0,
            temperatura_max=200.0,
            pressione_max=8.0,
            max_load_kg=500.0,
            num_linee_vuoto=8,
            stato=StatoAutoclaveEnum.DISPONIBILE
        )
        db.add(autoclave)
        db.flush()
        autoclave_id = autoclave.id
        print(f"✅ Autoclave creata: ID {autoclave_id}")
        
        # 2. Crea ciclo di cura
        ciclo = CicloCura(
            nome="Aeronautico-Standard",
            descrizione="Ciclo standard",
            temperatura_stasi1=180.0,
            pressione_stasi1=6.0,
            durata_stasi1=120
        )
        db.add(ciclo)
        db.flush()
        print(f"✅ Ciclo cura creato: ID {ciclo.id}")
        
        # 3. Crea part numbers nel catalogo
        part_numbers = [
            "WING-BRACKET-L", "WING-BRACKET-R", "ENGINE-MOUNT-F", "ENGINE-MOUNT-R",
            "LANDING-GEAR-M", "CONTROL-SURF-A", "FUEL-TANK-P", "CABIN-PANEL-F",
            "AVIONICS-BOX-1", "THERMAL-SHIELD"
        ]
        
        for pn in part_numbers:
            catalogo = Catalogo(
                part_number=pn,
                descrizione=f"Componente {pn}",
                categoria="Aeronautico",
                attivo=True
            )
            db.add(catalogo)
        
        db.flush()
        print(f"✅ Catalogo creato con {len(part_numbers)} part numbers")
        
        # 4. Crea parti
        parti_data = [
            ("WING-BRACKET-L", 2), ("WING-BRACKET-R", 2), ("ENGINE-MOUNT-F", 3),
            ("ENGINE-MOUNT-R", 3), ("LANDING-GEAR-M", 4), ("CONTROL-SURF-A", 1),
            ("FUEL-TANK-P", 3), ("CABIN-PANEL-F", 1), ("AVIONICS-BOX-1", 2),
            ("THERMAL-SHIELD", 1)
        ]
        
        parte_ids = {}
        for pn, valvole in parti_data:
            parte = Parte(
                part_number=pn,
                descrizione_breve=f"Parte {pn}",
                ciclo_cura_id=ciclo.id,
                num_valvole_richieste=valvole
            )
            db.add(parte)
            db.flush()
            parte_ids[pn] = parte.id
        
        print(f"✅ Parti create: {len(parte_ids)}")
        
        # 5. Crea tools
        tool_configs = [
            ("WING-BRACKET-L", 350, 280, 15.0),
            ("WING-BRACKET-R", 350, 280, 15.0),
            ("ENGINE-MOUNT-F", 400, 300, 25.0),
            ("ENGINE-MOUNT-R", 400, 300, 25.0),
            ("LANDING-GEAR-M", 450, 350, 35.0),
            ("CONTROL-SURF-A", 600, 200, 12.0),
            ("FUEL-TANK-P", 500, 400, 30.0),
            ("CABIN-PANEL-F", 300, 300, 8.0),
            ("AVIONICS-BOX-1", 200, 150, 5.0),
            ("THERMAL-SHIELD", 800, 150, 10.0)
        ]
        
        tool_ids = {}
        for pn, width, height, weight in tool_configs:
            tool = Tool(
                part_number_tool=f"TOOL-{pn}",
                descrizione=f"Tool per {pn}",
                larghezza_piano=float(width),
                lunghezza_piano=float(height),
                peso=float(weight),
                disponibile=True
            )
            db.add(tool)
            db.flush()
            tool_ids[pn] = tool.id
        
        print(f"✅ Tools creati: {len(tool_ids)}")
        
        # 6. Crea ODL per test (20 pezzi)
        odl_configs = [
            "WING-BRACKET-L", "WING-BRACKET-R", "ENGINE-MOUNT-F", "ENGINE-MOUNT-R",
            "LANDING-GEAR-M", "CONTROL-SURF-A", "FUEL-TANK-P", "CABIN-PANEL-F",
            "AVIONICS-BOX-1", "THERMAL-SHIELD",
            # Duplicati per raggiungere 20
            "WING-BRACKET-L", "ENGINE-MOUNT-F", "CABIN-PANEL-F", "AVIONICS-BOX-1", 
            "CONTROL-SURF-A", "FUEL-TANK-P", "WING-BRACKET-R", "ENGINE-MOUNT-R",
            "LANDING-GEAR-M", "THERMAL-SHIELD"
        ]
        
        odl_ids = []
        for i, pn in enumerate(odl_configs[:20]):
            if pn in parte_ids and pn in tool_ids:
                odl = ODL(
                    parte_id=parte_ids[pn],
                    tool_id=tool_ids[pn],
                    status="Preparazione",
                    priorita=1,
                    note=f"ODL test #{i+1}"
                )
                db.add(odl)
                db.flush()
                odl_ids.append(odl.id)
        
        db.commit()
        print(f"✅ ODL creati: {len(odl_ids)}")
        
        # Riepilogo
        print(f"""
🎯 SCENARIO PRONTO!
==================
📐 Autoclave ID: {autoclave_id}
📋 ODL IDs: {odl_ids}
🔧 Tools: {len(tool_ids)} tipi
⚖️ Range peso: 5-35kg
🔌 Linee vuoto: 1-4 per pezzo

🚀 TEST:
uvicorn backend.main:app --reload
POST /batch_nesting/solve con autoclave_id={autoclave_id}
        """)
        
        return {
            "autoclave_id": autoclave_id,
            "odl_ids": odl_ids
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    result = create_test_data()
    print(f"✅ Scenario creato! Autoclave: {result['autoclave_id']}, ODL: {len(result['odl_ids'])}") 