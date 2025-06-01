# 🔧 Risoluzione Errori di Connessione CarbonPilot

## ❌ **PROBLEMA RISOLTO: Errori Dashboard e Widget**

### 🚨 **Sintomi Osservati**
- Widget dashboard mostravano "Errore nel caricamento dati"
- Log frontend: `Failed to proxy http://localhost:8000/api/v1/v1/dashboard/odl-count`
- Errore: `socket hang up` e `ECONNRESET`
- Backend non si avviava: `Python non è stato trovato`

---

## ✅ **SOLUZIONE IMPLEMENTATA**

### 🐍 **STEP 1: Risoluzione Problema Python**

**Problema**: Python non riconosciuto dal sistema Windows
**Soluzione**: Attivare l'ambiente virtuale presente

```powershell
# Navigare alla directory backend
cd backend

# Attivare l'ambiente virtuale
.\.venv\Scripts\Activate.ps1

# Verificare che Python sia ora disponibile
python --version

# Avviare il backend
python main.py
```

### 🔄 **STEP 2: Correzione Doppio Prefisso API**

**Problema**: Proxy Next.js aggiungeva doppio `/v1/` negli URL
- Chiamata: `/api/v1/dashboard/odl-count`
- Proxy trasformava in: `http://localhost:8000/api/v1/v1/dashboard/odl-count`

**Soluzione**: Correzione `frontend/next.config.js`

```javascript
// ❌ PRIMA (errato)
{
  source: '/api/:path*',
  destination: 'http://localhost:8000/api/v1/:path*',
}

// ✅ DOPO (corretto)
{
  source: '/api/:path*',
  destination: 'http://localhost:8000/api/:path*',
}
```

### 📡 **STEP 3: Creazione Endpoint Dashboard**

**Problema**: Mancavano gli endpoint per i widget dashboard

**Soluzione**: Creato `backend/api/routers/dashboard.py` con:
- ✅ `GET /api/v1/dashboard/odl-count`
- ✅ `GET /api/v1/dashboard/autoclave-load`  
- ✅ `GET /api/v1/dashboard/nesting-active`
- ✅ `GET /api/v1/dashboard/kpi-summary`

---

## 🚀 **PROCEDURA AVVIO CORRETTA**

### 1️⃣ **Avvio Backend**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python main.py
```
**Verifica**: Dovrebbe essere disponibile su `http://localhost:8000`

### 2️⃣ **Avvio Frontend**
```powershell
cd frontend
npm run dev
```
**Verifica**: Dovrebbe essere disponibile su `http://localhost:3000` o `http://localhost:3001`

### 3️⃣ **Test Connessione**
- **Health Check**: `http://localhost:8000/health`
- **Endpoint Dashboard**: `http://localhost:8000/api/v1/dashboard/odl-count`
- **Frontend Proxy**: `http://localhost:3000/api/v1/dashboard/odl-count`

---

## 🔍 **DIAGNOSTICA PROBLEMI FUTURI**

### ⚠️ **Errori Comuni e Soluzioni**

#### **1. "Python non è stato trovato"**
```powershell
# Soluzione: Attivare ambiente virtuale
cd backend
.\.venv\Scripts\Activate.ps1
```

#### **2. "Failed to proxy" o "socket hang up"**
- ✅ Verificare che backend sia avviato
- ✅ Verificare che non ci siano doppie proxy rules
- ✅ Controllare che le porte siano corrette (8000 backend, 3000 frontend)

#### **3. "Errore nel caricamento dati" nei widget**
- ✅ Verificare che gli endpoint dashboard esistano
- ✅ Controllare i log del backend per errori
- ✅ Verificare che il database sia accessibile

#### **4. "v1/v1" negli URL**
- ✅ Controllare configurazione proxy in `next.config.js`
- ✅ Verificare che frontend chiami `/api/v1/...`
- ✅ Assicurarsi che proxy non aggiunga prefissi extra

---

## 📊 **Status Endpoint Dashboard**

| Endpoint | Descrizione | Status |
|----------|-------------|--------|
| `/api/v1/dashboard/odl-count` | Statistiche ODL totali/completati | ✅ |
| `/api/v1/dashboard/autoclave-load` | Carico percentuale autoclavi | ✅ |
| `/api/v1/dashboard/nesting-active` | Nesting attivi tempo reale | ✅ |
| `/api/v1/dashboard/kpi-summary` | Riassunto KPI completo | ✅ |

---

## 🎯 **Benefici della Risoluzione**

- ✅ **Widget Dashboard**: Funzionanti con dati real-time
- ✅ **Sistema Drag-and-Drop**: Operativo completamente
- ✅ **API Robuste**: Endpoint dashboard dedicati
- ✅ **Proxy Corretto**: Eliminato doppio prefisso
- ✅ **Documentazione**: Guida per risoluzione futura

---

## 🔮 **Prevenzione Futura**

### 📝 **Checklist Pre-Deploy**
- [ ] Backend ambiente virtuale attivo
- [ ] Tutti gli endpoint API testati
- [ ] Proxy frontend configurato correttamente
- [ ] Widget dashboard caricano dati
- [ ] Log puliti da errori di connessione

### 🧪 **Script di Test Rapido**
```bash
# Test backend health
curl http://localhost:8000/health

# Test endpoint dashboard
curl http://localhost:8000/api/v1/dashboard/odl-count

# Test proxy frontend  
curl http://localhost:3000/api/v1/dashboard/odl-count
```

---

*Documento creato: 2024-01-XX*  
*Ultima modifica: 2024-01-XX*  
*Versione: 1.0* 