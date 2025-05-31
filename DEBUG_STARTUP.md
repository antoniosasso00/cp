# 🔧 CarbonPilot - Guida Debug Startup

## ⚠️ **Errori Comuni e Soluzioni**

### **1. Errore "Could not find platform independent libraries"**
```
Could not find platform independent libraries <prefix>
```

**Cause:**
- Ambiente virtuale Python corrotto
- Path Python non corretto
- Dipendenze mancanti

**Soluzioni:**
```bash
# Opzione 1: Usa Python di sistema
cd backend
python -m uvicorn main:app --reload --port 8000

# Opzione 2: Ricrea ambiente virtuale
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt

# Opzione 3: Usa script smart
.\start_dev_smart.bat
```

### **2. Errore "WinError 10013 - Porta già occupata"**
```
ERROR: [WinError 10013] Tentativo di accesso al socket con modalità non consentite
```

**Diagnosi:**
```bash
# Controlla chi occupa le porte
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Termina processo specifico
taskkill /PID [PID_NUMBER] /F
```

**Soluzioni:**
- Usa `start_dev_smart.bat` che gestisce automaticamente
- Termina manualmente i processi e riavvia
- Cambia porta nel file `main.py` (es. 8001)

### **3. Verifica Sistema Attivo**

**Check rapido:**
```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000

# Enhanced Nesting
curl -X POST http://localhost:8000/api/v1/nesting/enhanced-preview ^
     -H "Content-Type: application/json" ^
     -d "{\"odl_ids\": [6, 7], \"autoclave_id\": 1}"
```

### **4. URL Diretti per Test**

| Componente | URL | Descrizione |
|------------|-----|-------------|
| Backend Health | `http://localhost:8000/health` | Stato backend |
| API Docs | `http://localhost:8000/docs` | Documentazione API |
| Frontend | `http://localhost:3000` | Interfaccia principale |
| **Nesting Enhanced** | `http://localhost:3000/dashboard/curing/nesting/auto-multi` | **Nuova visualizzazione** |
| Nesting Preview | Da pagina auto-multi → "Genera Nesting" | Test enhanced canvas |

## 🎯 **Test Enhanced Nesting Implementato**

### **Novità Implementate:**
1. **Visualizzazione reale proporzioni tool** invece di stime area
2. **Posizionamento geometrico preciso** con coordinate mm
3. **Enhanced Nesting Canvas** con:
   - Dimensioni reali autoclave e tool
   - Scala proporzionale millimetrica
   - Griglia di riferimento (cm e mm)
   - Indicatori rotazione tool
   - Statistiche avanzate (efficienza geometrica/totale)
   - Gestione ODL esclusi con motivi
   - Margini di sicurezza visualizzati

### **Backend Enhanced:**
- Endpoint `/api/v1/nesting/enhanced-preview` 
- Algoritmo OR-Tools con posizionamento geometrico
- Constraints configurabili (distanze, padding, efficienza)
- Rotazioni automatiche tool
- Separazione cicli di cura

### **Come Testare:**
1. Vai su: `http://localhost:3000/dashboard/curing/nesting/auto-multi`
2. Clicca "Genera Nesting Automatico"
3. Seleziona alcuni ODL e autoclave
4. Vai al preview → Vedrai la **nuova visualizzazione enhanced**
5. I layout mostrano ora dimensioni reali, non stime!

## 🚀 **Avvio Raccomandato**

```bash
# Usa sempre lo script smart
.\start_dev_smart.bat
```

Lo script:
- ✅ Controlla se servizi già attivi
- ✅ Gestisce errori porta occupata  
- ✅ Prova diversi environment Python
- ✅ Apre automaticamente la pagina nesting
- ✅ Fornisce diagnostici completi

## 📞 **Se Tutti i Test Falliscono**

1. **Riavvia completamente il sistema**
2. **Elimina cache Next.js**: `rmdir /s frontend\.next`
3. **Reinstalla dipendenze frontend**: `cd frontend && npm install`
4. **Usa ambiente Python di sistema invece di .venv**
5. **Controlla firewall/antivirus che blocchi porte** 