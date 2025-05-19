#!/bin/bash
set -e

echo "Inizializzazione del backend CarbonPilot..."

# Verifica connessione al database
echo "Verifica della connessione al database..."
python -c "
import psycopg2
import os
import time
import sys

DB_HOST = os.getenv('POSTGRES_SERVER', 'db')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_NAME = os.getenv('POSTGRES_DB', 'carbonpilot')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

MAX_RETRIES = 10
RETRY_INTERVAL = 3

for i in range(MAX_RETRIES):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME,
            port=DB_PORT
        )
        conn.close()
        print('✅ Connessione al database riuscita')
        sys.exit(0)
    except Exception as e:
        print(f'Tentativo {i+1}/{MAX_RETRIES}: Connessione fallita - {e}')
        if i < MAX_RETRIES - 1:
            print(f'Nuovo tentativo tra {RETRY_INTERVAL} secondi...')
            time.sleep(RETRY_INTERVAL)
        else:
            print('❌ Impossibile connettersi al database dopo i tentativi massimi')
            sys.exit(1)
"

# Verifica stato database e schema
echo "Verifica dello schema del database..."
python -c "
import psycopg2
import os

DB_HOST = os.getenv('POSTGRES_SERVER', 'db')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
DB_NAME = os.getenv('POSTGRES_DB', 'carbonpilot')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    dbname=DB_NAME,
    port=DB_PORT
)
cursor = conn.cursor()

# Verifica se la tabella alembic_version esiste
cursor.execute(\"\"\"
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'alembic_version'
    );
\"\"\")
alembic_exists = cursor.fetchone()[0]

if alembic_exists:
    print('✅ Tabella alembic_version trovata')
    
    # Verifica qual è la versione corrente
    cursor.execute('SELECT version_num FROM alembic_version;')
    current_version = cursor.fetchone()
    
    if current_version:
        print(f'✅ Versione attuale: {current_version[0]}')
    else:
        print('❌ Nessuna versione trovata nella tabella alembic_version')
else:
    print('❓ Tabella alembic_version non trovata - lo schema potrebbe non essere inizializzato')

# Verifica se le tabelle principali esistono
tables_to_check = ['cataloghi', 'autoclavi', 'cicli_cura', 'tools', 'parti']
existing_tables = []
missing_tables = []

for table in tables_to_check:
    cursor.execute(f\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = '{table}'
        );
    \"\"\")
    if cursor.fetchone()[0]:
        existing_tables.append(table)
    else:
        missing_tables.append(table)

if existing_tables:
    print(f'✅ Tabelle esistenti: {existing_tables}')

if missing_tables:
    print(f'❓ Tabelle mancanti: {missing_tables}')

cursor.close()
conn.close()
"

# Applica le migrazioni
echo "Applicazione delle migrazioni Alembic..."
python -m alembic upgrade head || {
    echo "⚠️ Si sono verificati errori durante l'applicazione delle migrazioni."
    echo "⚠️ Si tenterà comunque di avviare l'API."
}

# Tenta di applicare direttamente la seconda migrazione se necessario
echo "Prova ad applicare direttamente la seconda migrazione..."
python -m alembic upgrade 2030_refactor_models || {
    echo "⚠️ Non è stato possibile applicare la seconda migrazione."
}

# Avvia l'API FastAPI
echo "Avvio dell'API FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload 