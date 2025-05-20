#!/usr/bin/env python
"""
Script per eseguire migrazioni Alembic in modo semplificato.
Supporta l'uso locale (fuori da Docker) e gestisce automaticamente l'ambiente.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import psycopg2
from pathlib import Path

# 📂 Root del progetto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

# 🔧 Database PostgreSQL locale (non Docker)
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "carbonpilot"

LOCAL_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
os.environ["DATABASE_URL"] = LOCAL_DATABASE_URL
os.environ["POSTGRES_USER"] = POSTGRES_USER
os.environ["POSTGRES_PASSWORD"] = POSTGRES_PASSWORD
os.environ["POSTGRES_SERVER"] = POSTGRES_HOST
os.environ["POSTGRES_PORT"] = POSTGRES_PORT
os.environ["POSTGRES_DB"] = POSTGRES_DB

# 📍 Path al Python della virtualenv
if sys.platform == "win32":
    VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
else:
    VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

# 🔍 Test della connessione PostgreSQL
def test_db_connection():
    """Verifica che la connessione al database sia disponibile."""
    print(f"🔍 Test di connessione a PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connessione OK - PostgreSQL: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Errore di connessione a PostgreSQL: {str(e)}")
        print("\nSuggerimenti:")
        print("1. Verifica che PostgreSQL sia in esecuzione")
        print("2. Controlla le credenziali in questo script")
        print("3. Assicurati che il database 'carbonpilot' esista")
        print("4. Prova a connetterti manualmente con: psql -U postgres -h localhost -p 5432 carbonpilot")
        return False

# 🔧 Verifica l'ambiente
def check_environment():
    """Verifica che l'ambiente sia configurato correttamente."""
    if not VENV_PYTHON.exists():
        print(f"❌ Python non trovato in {VENV_PYTHON}.")
        print("   Devi attivare l'ambiente virtuale con: .venv\\Scripts\\activate (Windows)")
        print("   o source .venv/bin/activate (Linux/Mac)")
        return False
    
    if not ALEMBIC_INI.exists():
        print(f"❌ File alembic.ini non trovato in {ALEMBIC_INI}")
        return False
    
    return test_db_connection()

# 🔄 Modifica temporanea di alembic.ini se necessario
def prepare_alembic_config():
    """Verifica e prepara la configurazione di Alembic."""
    # Legge alembic.ini
    with open(ALEMBIC_INI, 'r') as f:
        config_content = f.read()
    
    # Se contiene riferimenti a variabili d'ambiente, crea una copia temporanea
    if '%(DATABASE_URL)s' in config_content:
        print("ℹ️ Creazione configurazione temporanea per Alembic...")
        tmp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.ini')
        with open(tmp_config.name, 'w') as f:
            # Sostituisce il riferimento alla variabile d'ambiente con l'URL esplicito
            updated_content = config_content.replace('%(DATABASE_URL)s', LOCAL_DATABASE_URL)
            f.write(updated_content)
        return tmp_config.name
    
    return None

# 🛠️ Esegue un comando Alembic
def run_alembic_command(command, message=None):
    """Esegue un comando Alembic con gestione degli errori."""
    cmd = [str(VENV_PYTHON), "-m", "alembic"]
    
    # Aggiungi parametri specifici del comando
    if command == "revision":
        cmd.extend(["revision", "--autogenerate"])
        if message:
            cmd.extend(["-m", message])
    elif command == "upgrade":
        cmd.extend(["upgrade", "head"])
    elif command == "history":
        cmd.extend(["history"])
    
    try:
        print(f"🚀 Esecuzione: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore nell'esecuzione di {command}:")
        print(f"🔴 Codice di errore: {e.returncode}")
        print(f"🔴 Output di errore:\n{e.stderr}")
        return False

# 📝 Funzione principale
def main():
    """Esegue la migrazione Alembic."""
    if not check_environment():
        sys.exit(1)
    
    print("\n🗣️ Verifica storico migrazioni:")
    run_alembic_command("history")
    
    # Se l'utente ha fornito un messaggio da riga di comando, lo usa
    if len(sys.argv) > 1:
        migration_message = " ".join(sys.argv[1:])
    else:
        # Altrimenti chiede un messaggio
        migration_message = input("🔧 Inserisci il messaggio per la migrazione Alembic: ").strip()
    
    if not migration_message:
        print("❌ È necessario specificare un messaggio per la migrazione.")
        sys.exit(1)
    
    # Prepara configurazione temporanea se necessario
    tmp_config = prepare_alembic_config()
    if tmp_config:
        os.environ["ALEMBIC_CONFIG"] = tmp_config
    
    try:
        # Genera la migrazione
        print(f"\n📝 Generazione migrazione: '{migration_message}'")
        if not run_alembic_command("revision", migration_message):
            sys.exit(1)
        
        # Applica la migrazione
        print("\n⬆️ Applicazione migrazione...")
        if not run_alembic_command("upgrade"):
            sys.exit(1)
        
        print("\n✅ Migrazione completata con successo!")
    finally:
        # Pulizia
        if tmp_config and os.path.exists(tmp_config):
            os.unlink(tmp_config)

if __name__ == "__main__":
    main()
