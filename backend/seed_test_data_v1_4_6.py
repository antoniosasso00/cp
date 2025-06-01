#!/usr/bin/env python3
"""
Script per aggiungere dati di test per v1.4.6-DEMO
Inserisce 2 part number con scostamenti significativi del 20% e 8%
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models.db import get_database_url
from models.catalogo import Catalogo
from models.parte import Parte
from models.tool import Tool
from models.ciclo_cura import CicloCura
from models.odl import ODL
from models.tempo_fase import TempoFase
from models.standard_time import StandardTime

def create_test_data():
    """Crea dati di test per verificare il pannello Top Delta"""
    
    # Connessione al database
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🔧 Creazione dati di test per v1.4.6-DEMO...")
        
        # 1. Verifica/Crea Part Number TEST-HIGH-DELTA (scostamento 20%)
        part_high = db.query(Catalogo).filter(Catalogo.part_number == "TEST-HIGH-DELTA").first()
        if not part_high:
            part_high = Catalogo(
                part_number="TEST-HIGH-DELTA",
                descrizione="Test Part con scostamento alto (20%)",
                categoria="Test",
                sotto_categoria="DeltaTest",
                attivo=True,
                note="Creato per test v1.4.6-DEMO"
            )
            db.add(part_high)
            print("✅ Creato catalogo TEST-HIGH-DELTA")

        # 2. Verifica/Crea Part Number TEST-MED-DELTA (scostamento 8%)
        part_med = db.query(Catalogo).filter(Catalogo.part_number == "TEST-MED-DELTA").first()
        if not part_med:
            part_med = Catalogo(
                part_number="TEST-MED-DELTA",
                descrizione="Test Part con scostamento medio (8%)",
                categoria="Test",
                sotto_categoria="DeltaTest",
                attivo=True,
                note="Creato per test v1.4.6-DEMO"
            )
            db.add(part_med)
            print("✅ Creato catalogo TEST-MED-DELTA")

        db.commit()

        # 3. Verifica/Crea Tool di test
        test_tool = db.query(Tool).filter(Tool.part_number_tool == "TOOL-TEST-DELTA").first()
        if not test_tool:
            test_tool = Tool(
                part_number_tool="TOOL-TEST-DELTA",
                descrizione="Tool per test delta",
                lunghezza_piano=300.0,
                larghezza_piano=200.0,
                peso=10.0,
                disponibile=True
            )
            db.add(test_tool)
            print("✅ Creato tool TOOL-TEST-DELTA")

        # 4. Verifica/Crea Ciclo di cura
        test_ciclo = db.query(CicloCura).filter(CicloCura.nome == "CICLO-TEST-DELTA").first()
        if not test_ciclo:
            test_ciclo = CicloCura(
                nome="CICLO-TEST-DELTA",
                temperatura_stasi1=180.0,
                pressione_stasi1=6.0,
                durata_stasi1=120,
                attiva_stasi2=False
            )
            db.add(test_ciclo)
            print("✅ Creato ciclo CICLO-TEST-DELTA")

        db.commit()

        # 5. Crea Parti
        parte_high = db.query(Parte).filter(Parte.part_number == "TEST-HIGH-DELTA").first()
        if not parte_high:
            parte_high = Parte(
                part_number="TEST-HIGH-DELTA",
                descrizione_breve="Test High Delta",
                num_valvole_richieste=2,
                ciclo_cura_id=test_ciclo.id,
                note_produzione="Test per v1.4.6-DEMO"
            )
            db.add(parte_high)

        parte_med = db.query(Parte).filter(Parte.part_number == "TEST-MED-DELTA").first()
        if not parte_med:
            parte_med = Parte(
                part_number="TEST-MED-DELTA",
                descrizione_breve="Test Med Delta",
                num_valvole_richieste=1,
                ciclo_cura_id=test_ciclo.id,
                note_produzione="Test per v1.4.6-DEMO"
            )
            db.add(parte_med)

        db.commit()
        print("✅ Creato parti di test")

        # 6. Crea tempi standard di riferimento (100 min per laminazione, 60 min per cura)
        standard_times = [
            # High delta part
            {"part_number": "TEST-HIGH-DELTA", "phase": "laminazione", "minutes": 100.0},
            {"part_number": "TEST-HIGH-DELTA", "phase": "cura", "minutes": 60.0},
            # Med delta part
            {"part_number": "TEST-MED-DELTA", "phase": "laminazione", "minutes": 100.0},
            {"part_number": "TEST-MED-DELTA", "phase": "cura", "minutes": 60.0},
        ]

        for st_data in standard_times:
            existing_st = db.query(StandardTime).filter(
                StandardTime.part_number == st_data["part_number"],
                StandardTime.phase == st_data["phase"]
            ).first()
            
            if not existing_st:
                new_st = StandardTime(
                    part_number=st_data["part_number"],
                    phase=st_data["phase"],
                    minutes=st_data["minutes"],
                    note="Tempo standard di test per v1.4.6-DEMO"
                )
                db.add(new_st)

        db.commit()
        print("✅ Creati tempi standard di test")

        # 7. Crea ODL e tempi osservati con scostamenti
        data_base = datetime.now() - timedelta(days=15)  # 15 giorni fa

        # Per TEST-HIGH-DELTA: tempi osservati 20% più alti (120min vs 100min, 72min vs 60min)
        for i in range(5):
            odl = ODL(
                parte_id=parte_high.id,
                tool_id=test_tool.id,
                priorita=1,
                status="Finito",
                include_in_std=True,
                note=f"Test ODL {i+1} per HIGH DELTA"
            )
            db.add(odl)
            db.flush()  # Per ottenere l'ID

            # Tempo laminazione: 120 min (20% più alto di 100)
            tempo_lam = TempoFase(
                odl_id=odl.id,
                fase="laminazione",
                inizio_fase=data_base + timedelta(days=i, hours=8),
                fine_fase=data_base + timedelta(days=i, hours=10),
                durata_minuti=120,
                note="Test laminazione con scostamento +20%"
            )
            tempo_lam.created_at = data_base + timedelta(days=i)
            db.add(tempo_lam)

            # Tempo cura: 72 min (20% più alto di 60)
            tempo_cura = TempoFase(
                odl_id=odl.id,
                fase="cura",
                inizio_fase=data_base + timedelta(days=i, hours=10),
                fine_fase=data_base + timedelta(days=i, hours=11, minutes=12),
                durata_minuti=72,
                note="Test cura con scostamento +20%"
            )
            tempo_cura.created_at = data_base + timedelta(days=i)
            db.add(tempo_cura)

        # Per TEST-MED-DELTA: tempi osservati 8% più alti (108min vs 100min, 65min vs 60min)
        for i in range(5):
            odl = ODL(
                parte_id=parte_med.id,
                tool_id=test_tool.id,
                priorita=1,
                status="Finito",
                include_in_std=True,
                note=f"Test ODL {i+1} per MED DELTA"
            )
            db.add(odl)
            db.flush()

            # Tempo laminazione: 108 min (8% più alto di 100)
            tempo_lam = TempoFase(
                odl_id=odl.id,
                fase="laminazione",
                inizio_fase=data_base + timedelta(days=i, hours=14),
                fine_fase=data_base + timedelta(days=i, hours=15, minutes=48),
                durata_minuti=108,
                note="Test laminazione con scostamento +8%"
            )
            tempo_lam.created_at = data_base + timedelta(days=i)
            db.add(tempo_lam)

            # Tempo cura: 65 min (8% più alto di 60)
            tempo_cura = TempoFase(
                odl_id=odl.id,
                fase="cura",
                inizio_fase=data_base + timedelta(days=i, hours=16),
                fine_fase=data_base + timedelta(days=i, hours=17, minutes=5),
                durata_minuti=65,
                note="Test cura con scostamento +8%"
            )
            tempo_cura.created_at = data_base + timedelta(days=i)
            db.add(tempo_cura)

        db.commit()
        print("✅ Creati ODL e tempi osservati di test")

        print("🎉 Dati di test per v1.4.6-DEMO creati con successo!")
        print("📊 Scostamenti attesi:")
        print("   • TEST-HIGH-DELTA: +20% (laminazione: 120 vs 100, cura: 72 vs 60)")
        print("   • TEST-MED-DELTA: +8% (laminazione: 108 vs 100, cura: 65 vs 60)")

    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante la creazione dei dati di test: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 