#!/bin/bash

echo "🌍 Avvio ambiente di sviluppo CarbonPilot..."

# Avvia i container Docker
docker compose up -d

# Apri VS Code con le cartelle principali
code ./backend/app
code ./frontend/app

echo "✅ Ambiente di sviluppo pronto!"
echo "📝 Frontend: http://localhost:3000"
echo "📝 Backend: http://localhost:8000/docs" 