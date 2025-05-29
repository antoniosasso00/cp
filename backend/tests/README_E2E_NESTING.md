# 🧪 Test End-to-End Sistema Nesting

Questo documento descrive i test end-to-end completi per il sistema di nesting automatico di CarbonPilot.

## 📋 Panoramica

I test end-to-end verificano l'intero flusso del sistema nesting:

1. **Seed con ODL vari** - Creazione dati di test con diverse priorità, dimensioni e cicli
2. **Generazione nesting automatico** - Test dell'algoritmo di ottimizzazione con parametri personalizzati
3. **Preview + conferma** - Verifica dell'anteprima e conferma dei nesting generati
4. **Caricamento + cura** - Simulazione del caricamento in autoclave e processo di cura
5. **Verifica stato finale e report** - Controllo dello stato del sistema e generazione report

## 🚀 Esecuzione Rapida

### Dalla Root del Progetto

```bash
# Test completo end-to-end
python run_e2e_test.py

# Solo creazione seed di test
cd backend
python run_test_seed.py --clean
```

### Dal Backend

```bash
cd backend

# Test completo
python tests/test_end_to_end_nesting.py

# Solo seed
python run_test_seed.py --clean
```

## 📦 Prerequisiti

### 1. Backend in Esecuzione

Il backend FastAPI deve essere attivo su `localhost:8000`:

```bash
cd backend
python -m uvicorn main:app --reload
```

### 2. Dipendenze Installate

```bash
pip install -r requirements.txt
```

Pacchetti principali richiesti:
- `requests` - Per chiamate API
- `sqlalchemy` - Per accesso database
- `fastapi` - Framework backend
- `pytest` - Framework di test (opzionale)

### 3. Database Configurato

Il database deve essere accessibile e configurato correttamente in `models/db.py`.

## 🌱 Gestione Seed di Test

### Creazione Seed Pulito

```bash
cd backend
python run_test_seed.py --clean
```

### Opzioni Disponibili

```bash
# Aiuto
python run_test_seed.py --help

# Pulisce database prima del seed
python run_test_seed.py --clean

# Forza seed anche se esistono dati
python run_test_seed.py --force
```

### Dati Creati dal Seed

Il seed crea automaticamente:

- **3 Cicli di cura** diversi (Standard 180°C, Rapido 160°C, Intensivo 200°C)
- **3 Autoclavi** con caratteristiche diverse (Grande, Media, Piccola)
- **6 Parti nel catalogo** (2 piccole, 2 medie, 2 grandi)
- **6 Tool** corrispondenti con dimensioni realistiche
- **20 ODL** in "Attesa Cura" con priorità variegate:
  - 5 ODL priorità alta (5)
  - 5 ODL priorità medio-alta (4)
  - 5 ODL priorità media (3)
  - 5 ODL priorità bassa (1-2)

## 🧪 Dettaglio Test End-to-End

### Step 1: Preparazione Ambiente

- Pulizia database per test pulito
- Verifica prerequisiti

### Step 2: Creazione Seed

- Creazione dati di test completi
- Verifica integrità dati

### Step 3: Test Connessione API

- Verifica raggiungibilità backend
- Test endpoint base

### Step 4: Preview Nesting

- Test endpoint `GET /api/v1/nesting/preview`
- Verifica raggruppamento ODL per ciclo compatibile
- Controllo autoclavi disponibili

### Step 5: Generazione Automatica

- Test endpoint `POST /api/v1/nesting/automatic`
- Parametri personalizzati:
  - `padding_mm`: 25.0
  - `margine_mm`: 50.0
  - `rotazione_abilitata`: true
  - `priorita_minima`: 1
  - `max_autoclavi`: 3
  - `efficienza_minima`: 0.6

### Step 6: Conferma Nesting

- Test endpoint `POST /api/v1/nesting/{id}/confirm`
- Conferma dei primi 2 nesting generati
- Verifica cambio stato a "Confermato"

### Step 7: Caricamento Nesting

- Test endpoint `POST /api/v1/nesting/{id}/load`
- Caricamento dei nesting confermati
- Verifica cambio stato ODL a "Cura"
- Verifica cambio stato autoclave a "IN_USO"

### Step 8: Simulazione Cura

- Creazione schedule entry per simulare ciclo completato
- Verifica integrazione con sistema scheduling

### Step 9: Verifica Stato Finale

- Controllo stato ODL (in cura vs attesa)
- Controllo stato nesting (bozza, confermato, caricato)
- Controllo stato autoclavi (in uso vs disponibili)
- Controllo schedule completate

### Step 10: Generazione Report

- Test endpoint `POST /api/v1/nesting/{id}/generate-report`
- Verifica creazione file PDF
- Controllo metadati report

## 📊 Interpretazione Risultati

### Successo Completo (100%)

Tutti i 10 test passano con successo. Il sistema funziona correttamente end-to-end.

### Successo Parziale (80-99%)

La maggior parte dei test passa. Verificare i test falliti per problemi specifici.

### Fallimento (< 80%)

Problemi significativi nel sistema. Verificare:
- Configurazione database
- Stato del backend
- Dipendenze mancanti
- Errori nei log

### Messaggi di Errore Comuni

#### "Backend non raggiungibile"
```bash
# Soluzione: Avvia il backend
cd backend
python -m uvicorn main:app --reload
```

#### "Dipendenze mancanti"
```bash
# Soluzione: Installa dipendenze
pip install -r requirements.txt
```

#### "Errore database"
```bash
# Soluzione: Verifica configurazione database
# Controlla models/db.py
```

## 🔧 Debug e Troubleshooting

### Log Dettagliati

I test producono output dettagliato per ogni step:

```
🚀 AVVIO TEST END-TO-END COMPLETO DEL SISTEMA NESTING
================================================================================
🕒 Timestamp: 2024-01-15 14:30:00

📋 STEP 1: Preparazione ambiente di test
🧹 Pulizia database per test pulito...
✅ Database pulito con successo

📋 STEP 2: Creazione seed con ODL vari
🌱 Creazione seed di test...
✅ Seed creato con successo:
   - 3 cicli di cura
   - 3 autoclavi
   - 6 parti nel catalogo
   - 20 ODL in Attesa Cura
   - Priorità: 5 alta, 10 media, 5 bassa
```

### Verifica Manuale

Dopo il seed, puoi verificare manualmente:

```bash
# Preview nesting
curl "http://localhost:8000/api/v1/nesting/preview?include_excluded=true"

# Generazione automatica
curl -X POST "http://localhost:8000/api/v1/nesting/automatic" \
  -H "Content-Type: application/json" \
  -d '{"force_regenerate": true}'
```

### Reset Completo

Per ricominciare da zero:

```bash
cd backend
python run_test_seed.py --clean
python tests/test_end_to_end_nesting.py
```

## 📈 Metriche di Performance

Il test misura automaticamente:

- **Tempo di esecuzione** per ogni step
- **Numero di ODL processati** vs esclusi
- **Efficienza nesting** generati
- **Tasso di successo** complessivo

### Benchmark Tipici

Su un sistema standard:
- Seed creation: ~2-3 secondi
- Preview generation: ~1 secondo
- Automatic nesting: ~5-10 secondi
- Confirmation/Loading: ~1 secondo per nesting
- Report generation: ~2-3 secondi per report

## 🔗 Integrazione CI/CD

Per integrare nei pipeline automatici:

```bash
# Script di test per CI
#!/bin/bash
set -e

# Avvia backend in background
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Aspetta che il backend sia pronto
sleep 10

# Esegui test
python tests/test_end_to_end_nesting.py

# Cleanup
kill $BACKEND_PID
```

## 📝 Estensioni Future

Possibili miglioramenti ai test:

1. **Test di carico** - Molti ODL simultanei
2. **Test di stress** - Autoclavi limitate
3. **Test di regressione** - Confronto con risultati precedenti
4. **Test di performance** - Benchmark automatici
5. **Test di integrazione frontend** - Selenium/Playwright

## 🆘 Supporto

Per problemi con i test:

1. Verifica i prerequisiti
2. Controlla i log dettagliati
3. Esegui test step-by-step
4. Verifica configurazione database
5. Controlla versioni dipendenze

Il sistema di test è progettato per essere robusto e fornire feedback dettagliato per facilitare il debug. 