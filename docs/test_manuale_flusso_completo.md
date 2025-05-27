# 🧪 Test Manuale Flusso Completo CarbonPilot

## 📋 Prerequisiti

1. **Backend attivo**: `uvicorn main:app --reload --host 0.0.0.0 --port 8000` (dalla directory `backend`)
2. **Frontend attivo**: `npm run dev` (dalla directory `frontend`)
3. **Database popolato**: Eseguire `python tools/seed_test.py --clear` per dati minimali

## 🎯 Obiettivo del Test

Verificare il flusso completo:
**Preparazione** → **Laminazione** → **Attesa Cura** → **Nesting** → **Cura** → **Report**

---

## 📊 Dati di Test Disponibili

Dopo aver eseguito `seed_test.py`, il database contiene:

### 📦 Catalogo Parts
- **TEST-001**: Pannello test leggero (800x600x30mm)
- **TEST-002**: Supporto test pesante (1200x800x60mm)

### 🔧 Tools
- **TOOL-LIGHT**: Stampo leggero (50kg, 1000x700mm)
- **TOOL-HEAVY**: Stampo pesante (300kg, 1500x900mm)

### 🏭 Autoclave
- **TEST-AUTO**: Autoclave test (max 500kg, 2000x1200mm)

### 📝 ODL Iniziali
- **ODL #1**: TEST-001 + TOOL-LIGHT (Stato: Preparazione)
- **ODL #2**: TEST-002 + TOOL-HEAVY (Stato: Preparazione)

---

## 🚀 Procedura di Test

### 1️⃣ **FASE LAMINAZIONE** (Ruolo: Laminatore)

1. **Accedi all'applicazione**: http://localhost:3000
2. **Login come Laminatore** (se implementato il sistema di autenticazione)
3. **Vai alla sezione ODL**
4. **Verifica ODL disponibili**:
   - Dovresti vedere 2 ODL in stato "Preparazione"
   - ODL #1: TEST-001 con TOOL-LIGHT
   - ODL #2: TEST-002 con TOOL-HEAVY

5. **Avanza ODL #1**:
   - Seleziona ODL #1 (TEST-001)
   - Cambia stato da "Preparazione" → "Laminazione"
   - Aggiungi note: "Laminazione iniziata"
   - Salva modifiche

6. **Simula completamento laminazione**:
   - Cambia stato da "Laminazione" → "In Coda"
   - Poi da "In Coda" → "Attesa Cura"
   - Aggiungi note: "Pronto per autoclave"

7. **Ripeti per ODL #2**:
   - Avanza anche il secondo ODL fino ad "Attesa Cura"

### 2️⃣ **FASE NESTING** (Ruolo: Autoclavista)

1. **Vai alla sezione Nesting/Autoclave**
2. **Verifica ODL in attesa**:
   - Dovresti vedere 2 ODL in stato "Attesa Cura"
   - Entrambi pronti per essere inclusi nel nesting

3. **Crea nuovo nesting**:
   - Seleziona autoclave "TEST-AUTO"
   - Aggiungi entrambi gli ODL al nesting
   - Verifica calcoli automatici:
     - Peso totale: 350kg (50kg + 300kg) ✅ < 500kg limite
     - Area utilizzata sui due piani
     - Valvole richieste vs disponibili

4. **Configura nesting**:
   - Imposta superficie piano 2 (se configurabile)
   - Verifica posizionamento automatico dei tool
   - Controlla efficienza di utilizzo

5. **Conferma nesting**:
   - Clicca "Conferma Nesting"
   - Verifica che gli ODL passino a stato "Cura"
   - Controlla che il nesting sia salvato

### 3️⃣ **FASE CURA** (Ruolo: Autoclavista)

1. **Avvia ciclo di cura**:
   - Seleziona il nesting confermato
   - Verifica parametri del ciclo "Ciclo Test":
     - Temperatura: 120°C
     - Pressione: 4.0 bar
     - Durata: 30 minuti
   - Clicca "Avvia Cura"

2. **Monitora progresso**:
   - Verifica barra di progresso (se implementata)
   - Controlla stato autoclave
   - Monitora parametri in tempo reale (se disponibili)

3. **Completa cura**:
   - Attendi completamento o simula fine ciclo
   - Clicca "Termina Cura"
   - Verifica che ODL passino a stato "Finito"

### 4️⃣ **FASE REPORT** (Ruolo: Admin/Responsabile)

1. **Vai alla sezione Report**
2. **Genera report di produzione**:
   - Seleziona periodo: oggi
   - Includi sezioni: produzione, nesting, tempi
   - Clicca "Genera Report"

3. **Verifica report generato**:
   - Controlla che il PDF sia creato
   - Scarica e apri il report
   - Verifica contenuti:
     - Dettagli ODL completati
     - Statistiche nesting
     - Tempi di produzione
     - Efficienza autoclave

4. **Visualizza storico**:
   - Controlla lista report generati
   - Verifica metadati (dimensione file, data, tipo)

---

## ✅ Criteri di Successo

### 🎯 Flusso ODL
- [ ] ODL avanzano correttamente tra gli stati
- [ ] Transizioni di stato sono logiche e controllate
- [ ] Note e timestamp vengono salvati

### 🎯 Nesting
- [ ] Algoritmo calcola correttamente peso e area
- [ ] Vincoli di peso e spazio sono rispettati
- [ ] Posizionamento 2D funziona su entrambi i piani
- [ ] Efficienza di utilizzo è calcolata

### 🎯 Cura
- [ ] Parametri ciclo sono applicati correttamente
- [ ] Stato autoclave è aggiornato
- [ ] Progresso è monitorabile
- [ ] Completamento aggiorna stati ODL

### 🎯 Report
- [ ] PDF è generato correttamente
- [ ] Dati sono accurati e completi
- [ ] Download funziona
- [ ] Storico è mantenuto

---

## 🐛 Problemi Comuni e Soluzioni

### Backend non raggiungibile
```bash
# Verifica che il backend sia attivo
curl http://localhost:8000/health

# Se non risponde, riavvia:
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend non si carica
```bash
# Verifica che il frontend sia attivo
cd frontend
npm run dev
```

### Database vuoto
```bash
# Ripopola con dati di test
cd tools
python seed_test.py --clear
```

### Errori di nesting
- Verifica che i tool abbiano peso configurato
- Controlla che l'autoclave abbia max_load_kg impostato
- Assicurati che gli ODL siano in stato "Attesa Cura"

---

## 📝 Note per lo Sviluppatore

### Aree da Testare Approfonditamente
1. **Validazione dati**: Controlli sui limiti di peso e spazio
2. **Gestione errori**: Comportamento con dati inconsistenti
3. **Performance**: Tempi di risposta con molti ODL
4. **UI/UX**: Usabilità delle interfacce di nesting

### Possibili Miglioramenti
1. **Notifiche real-time**: Aggiornamenti automatici stato
2. **Validazione avanzata**: Controlli più sofisticati
3. **Visualizzazione 3D**: Rappresentazione tridimensionale
4. **Ottimizzazione automatica**: Suggerimenti di miglioramento

---

## 🎉 Completamento Test

Una volta completato il test, documenta:
- [ ] Tutti i passaggi sono stati eseguiti con successo
- [ ] Eventuali bug o problemi riscontrati
- [ ] Suggerimenti per miglioramenti
- [ ] Screenshot delle schermate principali

**Data test**: ___________  
**Testato da**: ___________  
**Versione**: ___________  
**Esito**: ⭐⭐⭐⭐⭐ 