#!/usr/bin/env python
"""
Script definitivo per eseguire migrazioni Alembic in modo robusto e affidabile.
Gestisce asyncpg per l'app e psycopg2 per Alembic senza conflitti.
"""
import os
import sys
import subprocess
import tempfile
import psycopg2
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 📂 Root del progetto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
MIGRATIONS_DIR = BACKEND_DIR / "alembic"
SEED_SCRIPT = BACKEND_DIR / "seed" / "seed_test_data.py"

# 🔧 Configurazione database
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "carbonpilot"

DATABASE_URL_ASYNC = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
DATABASE_URL_SYNC = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Imposta le variabili per Alembic
os.environ["DATABASE_URL"] = DATABASE_URL_ASYNC
os.environ["DATABASE_URL_SYNC"] = DATABASE_URL_SYNC

# 📍 Python della virtualenv
if sys.platform == "win32":
    VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

def check_prerequisites():
    """Verifica che tutti i prerequisiti siano soddisfatti."""
    if not ALEMBIC_INI.exists():
        logger.error(f"❌ File alembic.ini non trovato in {ALEMBIC_INI}")
        return False
    
    if not MIGRATIONS_DIR.exists():
        logger.error(f"❌ Directory migrations non trovata in {MIGRATIONS_DIR}")
        return False
    
    if not VENV_PYTHON.exists():
        logger.error(f"❌ Python virtualenv non trovato in {VENV_PYTHON}")
        return False
    
    return True

def test_db_connection():
    """Verifica connessione a PostgreSQL (psycopg2)."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            logger.info(f"✅ Connessione OK - {cur.fetchone()[0]}")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Errore connessione: {e}")
        return False

def run_alembic(command: str, message: str = ""):
    """Esegue un comando Alembic con gestione errori robusta."""
    cmd = [str(VENV_PYTHON), "-m", "alembic"]

    if command == "revision":
        cmd += ["revision", "--autogenerate", "-m", message]
    elif command == "upgrade":
        cmd += ["upgrade", "head"]
    elif command == "history":
        cmd += ["history"]

    try:
        result = subprocess.run(
            cmd, 
            cwd=BACKEND_DIR, 
            text=True, 
            capture_output=True, 
            check=True,
            env=dict(os.environ, PYTHONPATH=str(BACKEND_DIR))
        )
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Errore '{command}':\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Errore imprevisto durante '{command}': {e}")
        return False

def run_seed():
    """Esegue lo script di seed dei dati di test."""
    try:
        logger.info("🌱 Eseguo seed_test_data.py...")
        result = subprocess.run(
            [str(VENV_PYTHON), str(SEED_SCRIPT)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=True,
            env=dict(os.environ, PYTHONPATH=str(BACKEND_DIR))
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Errore durante il seed:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Errore imprevisto durante il seed: {e}")
        return False

def main():
    """Funzione principale con gestione errori robusta."""
    logger.info("🚀 Inizio processo di migrazione...")
    
    # 1. Verifica prerequisiti
    if not check_prerequisites():
        sys.exit(1)
    
    # 2. Test connessione database
    if not test_db_connection():
        sys.exit(1)
    
    # 3. Mostra storico migrazioni
    logger.info("📜 Storico migrazioni Alembic:")
    if not run_alembic("history"):
        sys.exit(1)
    
    # 4. Crea nuova revisione
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:]).strip()
    else:
        msg = input("✏️ Inserisci messaggio migrazione: ").strip()
    
    if not msg:
        logger.error("⚠️ Messaggio obbligatorio.")
        sys.exit(1)
    
    logger.info(f"📝 Creo nuova revisione: {msg}")
    if not run_alembic("revision", msg):
        sys.exit(1)
    
    # 5. Applica migrazione
    logger.info("⬆️ Upgrade a head...")
    if not run_alembic("upgrade"):
        sys.exit(1)
    
    # 6. Esegui seed dati
    if not run_seed():
        sys.exit(1)
    
    logger.info("✅ Tutto completato con successo!")

if __name__ == "__main__":
    main()
