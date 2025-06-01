#!/usr/bin/env python3
"""
Script per verificare e creare dati di test per i tempi standard.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.db import SessionLocal
from models.odl import ODL
from models.tempo_fase import TempoFase
from models.parte import Parte
from models.catalogo import Catalogo
from models.tool import Tool
from models.ciclo_cura import CicloCura
from datetime import datetime, timedelta

def check_database_status():
    """Controlla lo stato del database."""
    db = SessionLocal()
    
    print("=== STATO DATABASE ===")
    print(f"ODL totali: {db.query(ODL).count()}")
    print(f"ODL con include_in_std=True: {db.query(ODL).filter(ODL.include_in_std == True).count()}")
    print(f"ODL con status 'Finito': {db.query(ODL).filter(ODL.status == 'Finito').count()}")
    print(f"Tempi fasi totali: {db.query(TempoFase).count()}")
    print(f"Tempi fasi completati: {db.query(TempoFase).filter(TempoFase.durata_minuti.isnot(None)).count()}")
    
    # Controlla ODL che soddisfano tutti i criteri
    valid_odl = db.query(ODL).filter(
        ODL.include_in_std == True,
        ODL.status == "Finito"
    ).all()
    
    print(f"ODL validi per calcolo: {len(valid_odl)}")
    
    if valid_odl:
        print("\nODL validi:")
        for odl in valid_odl:
            print(f"  ODL #{odl.id} - Parte: {odl.parte_id} - Status: {odl.status}")
            
            # Controlla se ha tempi fasi completati
            tempi_completati = db.query(TempoFase).filter(
                TempoFase.odl_id == odl.id,
                TempoFase.durata_minuti.isnot(None)
            ).all()
            
            print(f"    Tempi fasi completati: {len(tempi_completati)}")
            for tempo in tempi_completati:
                print(f"      Fase: {tempo.fase} - Durata: {tempo.durata_minuti} min")
    
    db.close()

def create_test_data():
    """Crea dati di test per verificare il calcolo dei tempi standard."""
    db = SessionLocal()
    
    try:
        print("\n=== CREAZIONE DATI DI TEST ===")
        
        # Verifica se esiste già un catalogo di test
        catalogo = db.query(Catalogo).filter(Catalogo.part_number == "TEST-STD-001").first()
        if not catalogo:
            catalogo = Catalogo(
                part_number="TEST-STD-001",
                descrizione="Part number di test per tempi standard",
                categoria="Test",
                sotto_categoria="Standard Times"
            )
            db.add(catalogo)
            db.flush()
            print("✅ Catalogo di test creato")
        
        # Verifica se esiste una parte di test
        parte = db.query(Parte).filter(Parte.part_number == "TEST-STD-001").first()
        if not parte:
            parte = Parte(
                part_number="TEST-STD-001",
                descrizione_breve="Parte di test per tempi standard",
                num_valvole_richieste=2
            )
            db.add(parte)
            db.flush()
            print("✅ Parte di test creata")
        
        # Verifica se esiste un tool di test
        tool = db.query(Tool).filter(Tool.part_number_tool == "TOOL-TEST-001").first()
        if not tool:
            tool = Tool(
                part_number_tool="TOOL-TEST-001",
                descrizione="Tool di test per tempi standard",
                lunghezza_piano=100.0,
                larghezza_piano=50.0,
                peso=10.0
            )
            db.add(tool)
            db.flush()
            print("✅ Tool di test creato")
        
        # Crea alcuni ODL di test con tempi fasi completati
        for i in range(3):
            # Verifica se l'ODL esiste già
            existing_odl = db.query(ODL).filter(
                ODL.parte_id == parte.id,
                ODL.tool_id == tool.id
            ).first()
            
            if not existing_odl:
                odl = ODL(
                    parte_id=parte.id,
                    tool_id=tool.id,
                    status="Finito",
                    include_in_std=True,
                    priorita=1,
                    note=f"ODL di test #{i+1} per calcolo tempi standard"
                )
                db.add(odl)
                db.flush()
                
                # Crea tempi fasi per questo ODL
                # Fase Laminazione
                tempo_lam = TempoFase(
                    odl_id=odl.id,
                    fase="laminazione",
                    inizio_fase=datetime.now() - timedelta(hours=2),
                    fine_fase=datetime.now() - timedelta(hours=1, minutes=30),
                    durata_minuti=30 + (i * 5)  # Varia la durata per avere dati diversi
                )
                db.add(tempo_lam)
                
                # Fase Cura
                tempo_cura = TempoFase(
                    odl_id=odl.id,
                    fase="cura",
                    inizio_fase=datetime.now() - timedelta(hours=1, minutes=30),
                    fine_fase=datetime.now() - timedelta(minutes=30),
                    durata_minuti=60 + (i * 10)  # Varia la durata per avere dati diversi
                )
                db.add(tempo_cura)
                
                print(f"✅ ODL di test #{i+1} creato con tempi fasi")
        
        db.commit()
        print("✅ Dati di test creati con successo!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante la creazione dei dati di test: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Controllo stato database...")
    check_database_status()
    
    print("\n🛠️ Vuoi creare dati di test? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        create_test_data()
        print("\n🔍 Controllo stato database dopo creazione dati...")
        check_database_status()
    else:
        print("✅ Operazione annullata") 