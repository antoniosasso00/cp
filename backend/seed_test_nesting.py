"""
Script per generare dati di test per il nesting.
Questo script crea una connessione diretta al database locale per testare 
la tabella nesting_results.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from models.nesting_result import NestingResult
from models.autoclave import Autoclave
from models.odl import ODL
from models.base import Base

# Configura l'URL del database per il testing locale
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/carbonpilot"

def setup_test_db():
    """Configura e inizializza il database di test."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Crea le tabelle se non esistono già
    Base.metadata.create_all(bind=engine)
    
    # Crea una sessione
    db = SessionLocal()
    
    try:
        # Verifica che ci siano autoclavi nel DB
        autoclavi = db.query(Autoclave).all()
        if not autoclavi:
            print("ERRORE: Non ci sono autoclavi nel database. Aggiungi prima almeno un'autoclave.")
            return False
            
        # Verifica che ci siano ODL nel DB
        odl_list = db.query(ODL).all()
        if not odl_list:
            print("ERRORE: Non ci sono ODL nel database. Aggiungi prima almeno un ODL.")
            return False
            
        # Crea un nesting di test
        autoclave = autoclavi[0]
        odl_samples = odl_list[:3] if len(odl_list) >= 3 else odl_list
        
        nesting = NestingResult(
            autoclave_id=autoclave.id,
            odl_ids=[odl.id for odl in odl_samples],
            area_utilizzata=5.5,
            area_totale=10.0,
            valvole_utilizzate=3,
            valvole_totali=autoclave.num_linee_vuoto,
            created_at=datetime.now()
        )
        
        # Aggiungi gli ODL alla relazione
        for odl in odl_samples:
            nesting.odl_list.append(odl)
            
        # Salva nel database
        db.add(nesting)
        db.commit()
        
        print(f"Creato nesting di test con ID {nesting.id}")
        print(f"Autoclave: {autoclave.nome} (ID: {autoclave.id})")
        print(f"ODL inclusi: {[odl.id for odl in odl_samples]}")
        
        return True
    except Exception as e:
        db.rollback()
        print(f"ERRORE durante la creazione dei dati di test: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_db() 