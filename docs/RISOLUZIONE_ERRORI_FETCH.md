# 🔧 Risoluzione Errori di Fetch - CarbonPilot

## 📋 Problemi Identificati

### 1. **Configurazione Hostname Errata**
- **Problema**: Il file `next.config.js` era configurato per l'ambiente Docker (`carbonpilot-backend:8000`) invece che per lo sviluppo locale
- **Sintomo**: Errori "Failed to fetch" con status 0
- **Soluzione**: Modificato `next.config.js` per usare `localhost:8000`

```javascript
// PRIMA (Docker)
destination: 'http://carbonpilot-backend:8000/api/:path*'

// DOPO (Sviluppo locale)
destination: 'http://localhost:8000/api/:path*'
```

### 2. **Backend Non Inizializzato**
- **Problema**: Database vuoto (0 tabelle) causava errori nelle API
- **Sintomo**: Errori 500 nelle chiamate API
- **Soluzione**: Eseguito `python create_tables.py` per inizializzare il database

### 3. **Gestione Errori API Insufficiente**
- **Problema**: Logging limitato e gestione errori poco dettagliata
- **Sintomo**: Difficoltà nel debug degli errori di connessione
- **Soluzione**: Aggiunto interceptors Axios con logging dettagliato

### 4. **Configurazione API Mista**
- **Problema**: Uso misto di `axios` e `fetch` con configurazioni duplicate
- **Sintomo**: Errori del linter e comportamenti inconsistenti
- **Soluzione**: Unificata la configurazione Axios con interceptors

## 🛠️ Modifiche Applicate

### File Modificati:

1. **`frontend/next.config.js`**
   - Cambiato hostname da Docker a localhost

2. **`frontend/src/lib/api.ts`**
   - Aggiunto timeout di 10 secondi
   - Implementato interceptors per logging dettagliato
   - Migliorata gestione errori con messaggi specifici
   - Rimossa dichiarazione duplicata di `api`

3. **`start_dev_fixed.bat`** (nuovo)
   - Script intelligente che controlla se i servizi sono già attivi
   - Avvio sequenziale con verifiche di stato
   - Apertura automatica del browser

### Database:
- Inizializzate tutte le tabelle SQLAlchemy
- Verificata connessione al database SQLite

## 🚀 Come Avviare l'Applicazione

### Metodo Raccomandato:
```bash
.\start_dev_fixed.bat
```

### Metodo Manuale:
```bash
# Terminal 1 - Backend
cd backend
..\\.venv\\Scripts\\activate.bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

## 🔍 Verifica Funzionamento

### Test Backend:
```bash
curl http://localhost:8000/health
# Dovrebbe restituire: {"status":"healthy",...}
```

### Test Frontend:
```bash
curl http://localhost:3000/api/v1/catalogo
# Dovrebbe fare proxy al backend
```

### Test Completo:
1. Aprire http://localhost:3000
2. Navigare alla sezione "Tools"
3. Verificare che non ci siano errori nella console del browser
4. Controllare che i dati vengano caricati correttamente

## 📊 Logging e Debug

### Console Browser:
- `🔗 API Base URL configurata:` - Conferma URL corretto
- `🌐 API Request:` - Log delle richieste in uscita
- `✅ API Response:` - Log delle risposte ricevute
- `❌ Errore nella risposta API:` - Dettagli errori

### Console Backend:
- `INFO:main:✅ Database inizializzato e server pronto!`
- `INFO:     127.0.0.1:XXXXX - "GET /api/v1/..." 200 OK`

## 🔄 Aggiornamenti Automatici

L'applicazione ora include:
- **Auto-refresh** ogni 5 secondi per i dati dei tools
- **Refresh on focus** quando si torna alla finestra
- **Indicatori visivi** dello stato di aggiornamento
- **Gestione errori** con toast notifications

## 🐛 Troubleshooting

### Se persistono errori di fetch:
1. Verificare che il backend sia attivo: `curl http://localhost:8000/health`
2. Controllare la console del browser per errori specifici
3. Verificare che non ci siano firewall che bloccano le porte 3000/8000
4. Riavviare entrambi i servizi con `.\start_dev_fixed.bat`

### Se il database è vuoto:
```bash
cd backend
python create_tables.py
```

### Se ci sono errori di dipendenze:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## 📝 Note per lo Sviluppo

- **Ambiente Docker**: Per usare Docker, ripristinare `carbonpilot-backend:8000` in `next.config.js`
- **Produzione**: Configurare variabili d'ambiente appropriate
- **CORS**: Attualmente permette tutte le origini (`allow_origins=["*"]`) - restringere in produzione

---

*Documento creato il: $(Get-Date)*
*Ultima modifica: $(Get-Date)* 