"""
Script per creare tutte le tabelle nel database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from models.db import get_database_url

def create_all_tables():
    """Crea tutte le tabelle nel database."""
    # Ottiene l'URL del database dalla configurazione
    database_url = get_database_url()
    
    # Crea l'engine e la sessione
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Crea tutte le tabelle
    Base.metadata.create_all(bind=engine)
    
    print("Tutte le tabelle sono state create con successo!")

if __name__ == "__main__":
    create_all_tables() 