#!/bin/bash
set -e

# Attendi che il database sia pronto
echo "Attendo che il database sia pronto..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database disponibile!"

# Applica le migrazioni Alembic
echo "Applicazione delle migrazioni Alembic..."
python -m alembic upgrade head

# Esegui lo script di inizializzazione del database
echo "Inizializzazione del database..."
python db_init.py

# Verifica che la tabella nesting_results esista
echo "Verifica della tabella nesting_results..."
python verify_nesting_table.py

# Avvia l'applicazione
echo "Avvio dell'applicazione..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 