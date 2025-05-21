#!/bin/bash
# Script per la risoluzione dei problemi di avvio nesting in Docker

echo "🚀 Avvio riparazione Docker per CarbonPilot Nesting v0.7.0"

# Arresta e rimuovi i container e i volumi
echo "📦 Arresto container e rimozione volumi..."
docker compose down -v

# Ricostruisci le immagini senza cache
echo "🏗️ Ricostruzione immagini Docker senza cache..."
docker compose build --no-cache

# Avvia i container in background
echo "🚀 Avvio container in background..."
docker compose up -d

# Attendi che il database sia pronto
echo "⏳ Attendi avvio del database..."
sleep 15

# Esegui lo script SQL di fix direttamente nel container PostgreSQL
echo "🔧 Esecuzione script SQL per creare tabelle nesting..."
docker compose exec -T db psql -U postgres -d carbonpilot < fix_nesting_tables.sql

# Riavvia il backend per assicurarsi che le tabelle siano visibili all'app
echo "🔄 Riavvio backend..."
docker compose restart backend

# Attendi un po' per il riavvio
sleep 5

# Verifica se l'API è attiva
echo "🔍 Verifica API backend..."
curl -s http://localhost:8000/docs > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API backend raggiungibile!"
else
    echo "❌ API backend non raggiungibile. Controlla i log con: docker compose logs -f backend"
fi

echo "✅ Fix Nesting completato! Verifica che tutto funzioni correttamente."
echo "📋 Accedi all'applicazione su http://localhost:3000" 