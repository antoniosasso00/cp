# 🔄 BatchNesting - Ciclo Completo Stati

## ✅ Stati Implementati

**Flusso completo:** `DRAFT` → `SOSPESO` → `CONFERMATO` → `LOADED` → `CURED` → `TERMINATO`

### 📊 Stati Disponibili

| Stato | Descrizione | Transizioni Consentite |
|-------|-------------|------------------------|
| `DRAFT` | Bozza in preparazione | → SOSPESO |
| `SOSPESO` | In attesa di conferma | → CONFERMATO |
| `CONFERMATO` | Confermato e pronto | → LOADED |
| `LOADED` | Caricato in autoclave | → CURED |
| `CURED` | Cura completata | → TERMINATO |
| `TERMINATO` | Completato | *(finale)* |

## 🔧 Endpoint Implementati

### 1. **PATCH `/batch-nesting/{id}/confirm`**
- **Transizione:** `SOSPESO` → `CONFERMATO`
- **Protezione:** Solo `Responsabile`, `Autoclavista`, `ADMIN`
- **Aggiornamenti:**
  - `stato` → `CONFERMATO`
  - `data_conferma` → timestamp attuale
  - `confermato_da_utente` + `confermato_da_ruolo`

### 2. **PATCH `/batch-nesting/{id}/load`**
- **Transizione:** `CONFERMATO` → `LOADED`
- **Protezione:** Solo `Responsabile`, `Autoclavista`, `ADMIN`
- **Aggiornamenti:**
  - `stato` → `LOADED`
  - `updated_at` → timestamp attuale

### 3. **PATCH `/batch-nesting/{id}/cure`**
- **Transizione:** `LOADED` → `CURED`
- **Protezione:** Solo `Responsabile`, `Autoclavista`, `ADMIN`
- **Aggiornamenti:**
  - `stato` → `CURED`
  - `updated_at` → timestamp attuale

### 4. **PATCH `/batch-nesting/{id}/terminate`**
- **Transizione:** `CURED` → `TERMINATO`
- **Protezione:** Solo `Responsabile`, `Autoclavista`, `ADMIN`
- **Aggiornamenti:**
  - `stato` → `TERMINATO`
  - `data_completamento` → timestamp attuale
  - `durata_ciclo_minuti` → calcolata da `data_conferma`

### 5. **PATCH `/batch-nesting/{id}/conferma`** ⚠️ LEGACY
- **Alias deprecato** per `/confirm`
- Mantiene compatibilità con frontend esistente

## 🔒 Protezioni Implementate

### **Aggiornamenti Batch (PUT)**
- ✅ Solo batch in stato `SOSPESO` possono essere aggiornati
- ❌ Batch confermati/caricati/in corso sono read-only

### **Eliminazioni Batch (DELETE)**
- ✅ Solo batch in stato `SOSPESO` possono essere eliminati
- ❌ Batch in corso di lavorazione sono protetti

### **Transizioni di Stato**
- ✅ Ogni transizione valida solo dallo stato precedente
- ✅ Controllo ruoli utente per ogni operazione
- ✅ Logging completo di tutte le operazioni

## 📝 Campi Audit Trail

| Campo | Tipo | Aggiornato in |
|-------|------|---------------|
| `creato_da_utente` | string | Creazione |
| `creato_da_ruolo` | string | Creazione |
| `confermato_da_utente` | string | Conferma |
| `confermato_da_ruolo` | string | Conferma |
| `data_conferma` | datetime | Conferma |
| `data_completamento` | datetime | Terminazione |
| `durata_ciclo_minuti` | int | Terminazione |
| `created_at` | datetime | Automatico |
| `updated_at` | datetime | Ogni modifica |

## 🚀 Esempi di Utilizzo

### Conferma Batch
```bash
curl -X PATCH "http://localhost:8000/api/batch_nesting/{id}/confirm" \
  -d "confermato_da_utente=user123&confermato_da_ruolo=Responsabile"
```

### Carica in Autoclave
```bash
curl -X PATCH "http://localhost:8000/api/batch_nesting/{id}/load" \
  -d "caricato_da_utente=user123&caricato_da_ruolo=Autoclavista"
```

### Avvia Cura
```bash
curl -X PATCH "http://localhost:8000/api/batch_nesting/{id}/cure" \
  -d "avviato_da_utente=user123&avviato_da_ruolo=Responsabile"
```

### Termina Batch
```bash
curl -X PATCH "http://localhost:8000/api/batch_nesting/{id}/terminate" \
  -d "terminato_da_utente=user123&terminato_da_ruolo=Autoclavista"
```

## ⚡ Note Tecniche

- **Validazione ruoli**: Controllo in ogni endpoint
- **Transizioni atomiche**: Rollback automatico su errore
- **Logging completo**: Tracciamento di ogni operazione
- **Compatibilità**: Endpoint legacy mantenuto
- **Sicurezza**: Solo stati SOSPESO modificabili

---
*Generato automaticamente - CarbonPilot v1.4.19* 