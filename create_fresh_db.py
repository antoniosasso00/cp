#!/usr/bin/env python3
"""
Crea un database fresco con lo schema completo
"""

import sys
import os
from pathlib import Path

# Aggiungi il path del backend per gli import
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Imposta variabili d'ambiente per SQLite
os.environ["DATABASE_URL"] = "sqlite:///./carbonpilot.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./carbonpilot.db"

from sqlalchemy import create_engine
from models.base import Base

def create_fresh_database():
    """Crea un database fresco con lo schema completo"""
    
    # Rimuovi database esistente
    db_path = backend_path / "carbonpilot.db"
    if db_path.exists():
        db_path.unlink()
        print(f"✅ Database esistente rimosso: {db_path}")
    
    # Crea engine SQLite
    engine = create_engine("sqlite:///./backend/carbonpilot.db", echo=False)
    
    # Crea tutte le tabelle
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database creato con schema completo!")
    print(f"📁 Percorso: {db_path}")
    print(f"📊 Tabelle create: {len(Base.metadata.tables)}")
    
    # Lista tabelle create
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")

if __name__ == "__main__":
    create_fresh_database() 