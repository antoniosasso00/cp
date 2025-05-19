#!/bin/bash
set -e

# Carica variabili d'ambiente dal file .env
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Funzioni di supporto
check_database() {
  echo "🔍 Verifico la connessione al database..."
  python -c "
import sys
from sqlalchemy import create_engine
import time

# Maximum number of retries
max_retries = 5
retry_count = 0
retry_delay = 2  # seconds

# Get database URL, defaulting to a value if not found
db_url = '${DATABASE_URL:-postgresql://postgres:postgres@db:5432/carbonpilot}'

while retry_count < max_retries:
    try:
        engine = create_engine(db_url)
        conn = engine.connect()
        conn.close()
        print('✅ Connessione al database riuscita!')
        sys.exit(0)
    except Exception as e:
        retry_count += 1
        if retry_count < max_retries:
            print(f'⚠️ Tentativo {retry_count}/{max_retries} fallito. Riprovo in {retry_delay} secondi...')
            print(f'Errore: {str(e)}')
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        else:
            print('❌ Impossibile connettersi al database dopo ripetuti tentativi!')
            print(f'Errore: {str(e)}')
            sys.exit(1)
  "
}

init_alembic() {
  if [ ! -d "migrations" ]; then
    echo "🚀 Inizializzazione Alembic per la gestione delle migrazioni..."
    alembic init migrations

    # Modifica il file env.py di Alembic per utilizzare le nostre configurazioni
    sed -i 's/from sqlalchemy import pool/from sqlalchemy import pool\nimport os\nfrom dotenv import load_dotenv\nfrom api.database import SQLALCHEMY_DATABASE_URL\n\nload_dotenv()/' migrations/env.py
    sed -i 's/config.set_main_option("sqlalchemy.url", url)/url = os.environ.get("DATABASE_URL", SQLALCHEMY_DATABASE_URL)\nconfig.set_main_option("sqlalchemy.url", url)/' migrations/env.py
    sed -i 's/target_metadata = None/from models.base import Base\ntarget_metadata = Base.metadata/' migrations/env.py
  fi
}

run_migrations() {
  echo "🔄 Applicazione migrazioni del database..."
  alembic upgrade head
}

show_help() {
  echo "💼 CarbonPilot Backend - Comandi disponibili:"
  echo "  start       - Avvia il server in modalità normale"
  echo "  dev         - Avvia il server in modalità sviluppo con reload automatico"
  echo "  migrate     - Crea ed esegue migrazioni del database"
  echo "  init-db     - Inizializza il database con dati di base"
  echo "  test        - Esegue i test automatici"
  echo "  help        - Mostra questo messaggio di aiuto"
}

# Comando principale
case "$1" in
  start)
    check_database
    run_migrations
    echo "🚀 Avvio del server in modalità produzione..."
    uvicorn main:app --host 0.0.0.0 --port 8000
    ;;
    
  dev)
    check_database
    run_migrations
    echo "🚀 Avvio del server in modalità sviluppo con reload automatico..."
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ;;
    
  migrate)
    check_database
    init_alembic
    
    # Se specificato, crea una nuova migrazione
    if [ -n "$2" ]; then
      echo "📝 Creazione nuova migrazione: $2"
      alembic revision --autogenerate -m "$2"
    fi
    
    run_migrations
    ;;
    
  init-db)
    check_database
    run_migrations
    echo "🌱 Inizializzazione database con dati di base..."
    python -c "
from models.base import Base
from api.database import engine, get_db
from sqlalchemy.orm import Session

# Qui puoi aggiungere codice per inserire dati iniziali nel database
print('✅ Inizializzazione completata')
"
    ;;

  test)
    echo "🧪 Esecuzione dei test automatici..."
    pytest -xvs tests/
    ;;
    
  help|*)
    show_help
    ;;
esac 