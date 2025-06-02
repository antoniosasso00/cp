"""
Configurazione del database e gestione delle sessioni.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FLAG DI CONFIGURAZIONE ==========
# Questo flag permette di passare facilmente da SQLite a PostgreSQL
USE_SQLITE = True  # Cambia a False per usare PostgreSQL

# Configurazione del database
if USE_SQLITE:
    # SQLite per sviluppo locale - usa path assoluto
    backend_dir = Path(__file__).parent.parent
    db_path = backend_dir / "carbonpilot.db"
    DATABASE_URL = f"sqlite:///{db_path}"
    logger.info("🗃️ Configurazione database: SQLite (locale)")
else:
    # PostgreSQL per produzione
    DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/carbonpilot"
    logger.info("🐘 Configurazione database: PostgreSQL")

# Log del DATABASE_URL per debug (nascondendo la password per sicurezza)
def log_database_config():
    """Log della configurazione del database per debug."""
    if "postgresql" in DATABASE_URL:
        url_for_log = DATABASE_URL.replace(":postgres@", ":***@") if DATABASE_URL else "None"
    else:
        url_for_log = DATABASE_URL
    logger.info(f"Connessione database configurata: {url_for_log}")

def get_database_url():
    """Restituisce l'URL del database."""
    return DATABASE_URL

def test_database_connection():
    """Testa la connessione al database."""
    try:
        engine_test = create_engine(DATABASE_URL)
        with engine_test.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if USE_SQLITE:
                logger.info("✅ Connessione al database SQLite riuscita!")
            else:
                logger.info("✅ Connessione al database PostgreSQL riuscita!")
            return True
    except Exception as e:
        logger.error(f"❌ Errore connessione database: {str(e)}")
        if not USE_SQLITE:
            logger.error("Verifica che PostgreSQL sia attivo su localhost:5432 e che il database 'carbonpilot' esista")
            logger.info("💡 Suggerimento: Imposta USE_SQLITE = True per usare SQLite in sviluppo")
        return False

# Log della configurazione all'importazione
logger.info(f"Database URL configurato: {DATABASE_URL}")

# Testa la connessione
test_database_connection()

# Crea l'engine SQLAlchemy
if USE_SQLITE:
    # Per SQLite, aggiungi check_same_thread=False per permettere l'uso in thread multipli
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, echo=False)

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