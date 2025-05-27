# 🧪 Test Rapido Correzioni ODL

## 🚀 Avvio Sistema

```bash
# Metodo rapido
start_dev_fixed.bat

# Oppure manuale
cd backend && .venv\Scripts\activate && uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

## ✅ Verifica Funzionamento

### 1. Health Check
```bash
curl http://localhost:8000/health
# Dovrebbe restituire: {"status": "healthy", "database": {"status": "connected"}}
```

### 2. Test Automatico Completo
```bash
python test_odl_status_fix.py
```

### 3. Test Manuale API
```bash
# Test conversione stato (maiuscolo → formato corretto)
curl -X PATCH "http://localhost:8000/api/odl/1/status" \
  -H "Content-Type: application/json" \
  -d '{"new_status": "LAMINAZIONE"}'

# Dovrebbe restituire ODL con status: "Laminazione"
```

### 4. Test Frontend (Console Browser)
```javascript
// Apri http://localhost:3000 e nella console:
import { updateOdlStatus } from './lib/api';

updateOdlStatus(1, "ATTESA_CURA")
  .then(result => console.log("✅ Successo:", result))
  .catch(error => console.error("❌ Errore:", error));
```

## 🔍 Cosa Verificare

- ✅ **Conversione automatica**: `"LAMINAZIONE"` → `"Laminazione"`
- ✅ **Gestione errori**: Messaggi chiari per stati non validi
- ✅ **Logging**: Output dettagliato in console backend/frontend
- ✅ **Compatibilità**: Hook `useODLByRole` funziona per tutti i ruoli

## 📚 Documentazione Completa

- **Dettagli tecnici**: `docs/correzioni_odl_implementate.md`
- **Changelog**: `docs/changelog.md`
- **API Docs**: http://localhost:8000/docs

## 🆘 Risoluzione Problemi

1. **Backend non si avvia**: Verifica `.venv` attivo
2. **Errore CORS**: Già risolto, metodo PATCH incluso
3. **Stati non aggiornati**: Controlla formato input (ora supporta tutti i formati)
4. **Frontend non funziona**: Verifica `npm install` completato 