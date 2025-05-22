"""
Configurazione del database e gestione delle sessioni.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configurazione del database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/carbonpilot")

def get_database_url():
    """Restituisce l'URL del database."""
    return DATABASE_URL

# Crea l'engine SQLAlchemy
engine = create_engine(DATABASE_URL)

# Crea una factory per le sessioni
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base per i modelli
Base = declarative_base()

def get_db():
    """
    Dependency per ottenere una sessione del database.
    Da utilizzare con FastAPI Depends.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 