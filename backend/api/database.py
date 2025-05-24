# Importa la configurazione del database da models/db.py
from models.db import get_db, engine, Base

# Re-esporta get_db per compatibilità con i router esistenti
__all__ = ["get_db", "engine", "Base"]

def init_db():
    """Inizializza il database creando tutte le tabelle definite"""
    import os
    # Non crea le tabelle in produzione - usare Alembic per le migrazioni
    if os.getenv("ENVIRONMENT") == "development":
        Base.metadata.create_all(bind=engine) 