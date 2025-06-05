# CarbonPilot - Nesting Seed Guide v2.0.0-EXPANDED

## Overview
Guida completa per l'utilizzo del seed script unificato per i test del nesting.

**NUOVI REQUISITI v2.0.0:**
- ✅ **30 ODL** (invece di 20)
- ✅ **3 cicli di cura** (Aeronautico, Automotive, Marine)
- ✅ **3 autoclavi** (Large, Medium, Compact) 
- ✅ **Tools diversificati** con dimensioni e materiali varie

## Script Disponibili

### `tools/complete_nesting_seed.py` 
**Script principale unificato v2.0.0** che sostituisce tutti i precedenti:
- ❌ ~~seed_test_data.py~~ (obsoleto)
- ❌ ~~seed_edge_data.py~~ (obsoleto) 
- ❌ ~~sanity_seed.py~~ (obsoleto)

## Scenario Creato v2.0.0

### 🏭 **3 Autoclavi Diverse**
1. **Large** (1500x2500mm, 12 linee vuoto, 800kg)
2. **Medium** (1200x2000mm, 8 linee vuoto, 500kg) 
3. **Compact** (800x1500mm, 6 linee vuoto, 300kg)

### 🔄 **3 Cicli di Cura**
1. **Aeronautico-Standard** (180°C, 6bar, 120min)
2. **Automotive-Heavy** (200°C, 8bar, 90min + stasi2)
3. **Marine-Precision** (160°C, 5bar, 150min)

### 📦 **30 Tools Diversificati**
Suddivisi in 5 categorie:

#### Strutturali (12 tools)
- Supporti ala, attacchi motore, carrelli
- Strutture fusoliera, timoni
- **Dimensioni**: 350-800mm, **Peso**: 18-65kg
- **Materiali**: Acciaio Inox, Acciaio Maraging, Alluminio 7075

#### Propulsione (5 tools)  
- Condotti, ugelli, pale, compressori, turbine
- **Dimensioni**: 150-320mm, **Peso**: 12-35kg
- **Materiali**: Titanio Ti-6Al-4V, Superleghe Inconel

#### Controlli (5 tools)
- Alettoni, timoni, alette compensatrici
- **Dimensioni**: 200-800mm (lunghi), **Peso**: 5-18kg
- **Materiali**: Alluminio 7075, Alluminio 6061

#### Elettronica (5 tools)
- Sistemi navigazione, comunicazioni, controllo
- **Dimensioni**: 180-300mm (piccoli), **Peso**: 3.5-8kg
- **Materiali**: Alluminio 6061

#### Meccanica (5 tools)
- Pompe, riduttori, attuatori
- **Dimensioni**: 200-500mm, **Peso**: 10-30kg
- **Materiali**: Acciaio Inox, Acciaio Bonificato

### 📋 **30 ODL con Priorità Distribuite**
- **Alta priorità (P1)**: 10 ordini
- **Media priorità (P2)**: 12 ordini  
- **Bassa priorità (P3)**: 8 ordini

**Distribuzione per ciclo:**
- **12 parti** → Aeronautico (valvole 1-3)
- **10 parti** → Automotive (valvole 2-4)
- **8 parti** → Marine (valvole 1-2)

## Usage

### Esecuzione Base
```bash
# Attiva ambiente virtuale
.venv\Scripts\activate

# Esegui seed completo
python tools/complete_nesting_seed.py
```

### Funzionalità
- ✅ **Pulizia automatica** dei dati test precedenti
- ✅ **Creazione database** con 3 autoclavi, 3 cicli, 30 parti/tools/ODL
- ✅ **Logging dettagliato** del processo
- ✅ **Statistiche complete** per ogni autoclave
- ✅ **Gestione errori** e rollback automatico

## Test API

### 1. Avvio Backend
```bash
uvicorn backend.main:app --reload
```

### 2. Test con PowerShell (Windows)
```powershell
# Test autoclave grande (ID: 1)
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/nesting/solve" -Method POST -ContentType "application/json" -Body '{"autoclave_id": 1}'

# Test autoclave media (ID: 2)  
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/nesting/solve" -Method POST -ContentType "application/json" -Body '{"autoclave_id": 2}'

# Test autoclave compatta (ID: 3)
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/nesting/solve" -Method POST -ContentType "application/json" -Body '{"autoclave_id": 3}'

# Visualizza risultato
$response | ConvertTo-Json -Depth 10
```

### 3. Test con curl (Alternative)
```bash
# Test autoclave grande
curl -X POST "http://localhost:8000/api/nesting/solve" \
     -H "Content-Type: application/json" \
     -d '{"autoclave_id": 1}'

# Test autoclave media  
curl -X POST "http://localhost:8000/api/nesting/solve" \
     -H "Content-Type: application/json" \
     -d '{"autoclave_id": 2}'

# Test autoclave compatta
curl -X POST "http://localhost:8000/api/nesting/solve" \
     -H "Content-Type: application/json" \
     -d '{"autoclave_id": 3}'
```

## Aggiornamento Status ODL

### PowerShell
```powershell
# Aggiorna tutti gli ODL a "Attesa Cura" per il nesting
for ($i=1; $i -le 30; $i++) {
    $body = '{"status": "Attesa Cura"}'
    Invoke-RestMethod -Uri "http://localhost:8000/api/odl/$i/status" -Method PATCH -ContentType "application/json" -Body $body
    Write-Host "ODL $i aggiornato"
}
```

### Bash
```bash
# Aggiorna tutti gli ODL a "Attesa Cura"
for i in {1..30}; do
    curl -X PATCH "http://localhost:8000/api/odl/$i/status" \
         -H "Content-Type: application/json" \
         -d '{"status": "Attesa Cura"}'
    echo "ODL $i aggiornato"
done
```

## Target di Performance Attesi

### 🏭 Autoclave Large (1500x2500mm)
- **Efficiency**: ≥ 80%
- **Coverage**: ≥ 75% 
- **Pezzi posizionati**: 25-30 (tutti o quasi)
- **Utilizzo valvole**: ~267% (32/12 linee)

### 🏭 Autoclave Medium (1200x2000mm)  
- **Efficiency**: ≥ 70%
- **Coverage**: ≥ 65%
- **Pezzi posizionati**: 20-25 (maggior parte)
- **Utilizzo valvole**: ~400% (32/8 linee)

### 🏭 Autoclave Compact (800x1500mm)
- **Efficiency**: ≥ 60% 
- **Coverage**: ≥ 55%
- **Pezzi posizionati**: 15-20 (selezionati per priorità)
- **Utilizzo valvole**: ~533% (32/6 linee)

## Struttura Database

### Tabelle Principali
- **autoclavi**: 3 record (Large, Medium, Compact)
- **cicli_cura**: 3 record (Aeronautico, Automotive, Marine)
- **catalogo**: 30 record (5 categorie diverse)
- **parti**: 30 record (distribuiti tra i 3 cicli)
- **tools**: 30 record (dimensioni e materiali vari)
- **odl**: 30 record (priorità P1:10, P2:12, P3:8)

### Relazioni Chiave
- Ogni **parte** → 1 **ciclo di cura**
- Ogni **tool** → 1 **parte** (associazione N:M)
- Ogni **ODL** → 1 **parte** + 1 **tool**

## Debug & Troubleshooting

### Controllo Database
```python
# Verifica dati creati
python tools/print_schema_summary.py

# Controlla connessione
from backend.models.db import test_database_connection
test_database_connection()
```

### Log Analysis
Il seed script produce log dettagliati:
- 🧹 **Pulizia**: record eliminati per categoria
- 🏭 **Autoclavi**: dimensioni e capacità
- 🔄 **Cicli**: temperature e durate  
- 📦 **Tools**: materiali e dimensioni
- 📋 **ODL**: distribuzione priorità
- 📊 **Statistiche**: copertura e utilizzo per autoclave

### Problemi Comuni

#### "Nessun ODL disponibile"
- **Causa**: ODL in stato "Preparazione" invece di "Attesa Cura"
- **Soluzione**: Aggiornare status con script PowerShell/Bash sopra

#### "Database path not found"  
- **Causa**: Path database non corretto
- **Soluzione**: Il seed v2.0.0 usa `backend/models/db.py` (corretto)

#### "Import errors"
- **Causa**: Ambiente virtuale non attivato
- **Soluzione**: `.venv\Scripts\activate` su Windows

## Files Correlati

### Mantenuti
- ✅ `tools/complete_nesting_seed.py` - **Script principale v2.0.0**
- ✅ `tools/print_schema_summary.py` - Schema database  
- ✅ `tools/snapshot_structure.py` - Utility progetto
- ✅ `CursorNotes/NESTING_SEED_GUIDE.md` - **Questa guida**

### Opzionali (Advanced)
- ⚠️ `tools/edge_tests.py` - Test casi limite
- ⚠️ `tools/edge_single.py` - Test singolo pezzo

### Eliminati (Obsoleti)
- ❌ `tools/seed_test_data.py` 
- ❌ `tools/seed_edge_data.py`
- ❌ `tools/sanity_seed.py`

---

## Riassunto Miglioramenti v2.0.0

✅ **30 ODL** invece di 20  
✅ **3 autoclavi** diverse (Large/Medium/Compact)  
✅ **3 cicli di cura** (Aeronautico/Automotive/Marine)  
✅ **Tools diversificati** con 5 categorie e materiali vari  
✅ **Priorità distribuite** (P1:10, P2:12, P3:8)  
✅ **Statistiche per autoclave** (copertura, utilizzo valvole)  
✅ **Cleanup migliorato** dei dati test  
✅ **Logging dettagliato** del processo  
✅ **Documentazione aggiornata** con test per 3 autoclavi  

Il database è ora pronto per test completi e realistici dell'algoritmo di nesting con scenari diversificati!