# 🔧 Debug Report – CarbonPilot

## 🗂️ Migrazioni
- Rimosso op.drop_table e op.drop_column da init_schema.py
- Aggiunto `pass` nelle funzioni upgrade() e downgrade() per prevenire errori di indentazione
- **Problema**: Le tabelle non sono state create nel database
- **Soluzione**: Riscrivere il file di migrazione per includere la creazione delle tabelle

## 🐳 Docker
- docker compose down -v && docker compose up --build completato
- Backend avviato con FastAPI
- Frontend avviato con Next.js
- Postgres in esecuzione

## 🌱 Seed
- Tentativo di esecuzione tools/seed_test_data.py
- **Errori**:
  - relation "autoclavi" does not exist - Tabelle non create nel database
  - Endpoint parti: Not Found - Probabilmente l'API non è configurata correttamente

## ✅ Prossimi passi
1. Modificare il file di migrazione per creare le tabelle corrette
2. Verificare che gli endpoint API siano configurati correttamente
3. Rieseguire il seed dei dati

## ❌ Errori riscontrati
- Errore nei modelli SQLAlchemy (mancano tabelle)
- Errore negli endpoint FastAPI (not found su /parti/)
- Errore nelle migrazioni (tabelle non create) 