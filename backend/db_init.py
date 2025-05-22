"""
Script di inizializzazione del database
Crea tutte le tabelle necessarie se non esistono già.
"""

import os
import sys
import time
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, NestingResult
from models.db import get_database_url

def init_db():
    """Inizializza il database creando tutte le tabelle se non esistono già."""
    # Ottiene l'URL del database dalla configurazione
    database_url = get_database_url()
    
    # Attendi che il database sia disponibile
    engine = None
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Crea l'engine SQLAlchemy
            engine = create_engine(database_url)
            # Testa la connessione
            with engine.connect() as conn:
                print("Connessione al database stabilita con successo!")
                break
        except Exception as e:
            retry_count += 1
            print(f"Tentativo {retry_count}/{max_retries}: impossibile connettersi al database. Errore: {str(e)}")
            if retry_count < max_retries:
                print(f"Attendo 5 secondi prima di riprovare...")
                time.sleep(5)
            else:
                print("Impossibile connettersi al database dopo i tentativi massimi.")
                sys.exit(1)
    
    # Verifica l'esistenza delle tabelle
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Verifica se la tabella nesting_results esiste
    if "nesting_results" not in existing_tables:
        print("La tabella 'nesting_results' non esiste. Creazione in corso...")
        
        # Crea le tabelle
        Base.metadata.create_all(bind=engine)
        print("Tutte le tabelle sono state create con successo!")
    else:
        print("Tutte le tabelle necessarie esistono già.")
    
    return True

if __name__ == "__main__":
    init_db() 