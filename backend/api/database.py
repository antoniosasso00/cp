import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Importiamo Base da models
from models.base import Base

# Carica variabili d'ambiente
load_dotenv()

# Configurazione della connessione al database
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "carbonpilot")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dipendenza per ottenere una sessione del database"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inizializza il database creando tutte le tabelle definite"""
    # Importa qui i modelli per assicurarsi che siano registrati con Base
    # Il modello User è già importato tramite Base
    
    # Non crea le tabelle in produzione - usare Alembic per le migrazioni
    if os.getenv("ENVIRONMENT") == "development":
        Base.metadata.create_all(bind=engine) 