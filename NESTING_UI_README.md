# 🧠 Interfaccia Nesting Automatico - v1.1.2-DEMO

## 📋 Panoramica

È stata implementata l'interfaccia frontend iniziale per avviare un nesting automatico. L'utente con ruolo **Curing** o **ADMIN** può ora:

- ✅ Visualizzare tutti gli ODL nello stato `"Attesa Cura"`
- ✅ Visualizzare tutte le autoclavi `"DISPONIBILI"`
- ✅ Selezionare ODL e autoclavi con supporto "Select all / Deselect all"
- ✅ Impostare parametri di nesting (padding, priorità, ecc.)
- ✅ Cliccare su "Genera Nesting" per inviare la richiesta al backend
- ✅ Visualizzare i risultati del nesting generato

## 🚀 Come Testare

### 1. Avvio Applicazione

```bash
# Terminal 1 - Backend
cd backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

### 2. Accesso Interfaccia

1. **Apri browser**: `http://localhost:3000`
2. **Seleziona ruolo**: Scegli "Curing" o "ADMIN"
3. **Naviga al nesting**: Sidebar → CURING → Nesting
4. **URL diretto**: `http://localhost:3000/dashboard/curing/nesting`

### 3. Test Funzionalità

#### 📄 Pagina Principale Nesting
- **Selezione ODL**: Checkbox per ogni ODL in "Attesa Cura"
- **Selezione Autoclavi**: Checkbox per ogni autoclave "DISPONIBILE"
- **Pulsanti Bulk**: "Seleziona Tutti" / "Deseleziona Tutti"
- **Parametri**: Configura padding, distanza, priorità area, accorpamento
- **Generazione**: Clicca "Genera Nesting" per avviare

#### 📄 Pagina Risultati
- **Informazioni Generali**: Nome batch, data, ODL inclusi
- **Parametri Utilizzati**: Configurazione algoritmo
- **Statistiche**: Area, peso, valvole (se disponibili)
- **Azioni**: Download report, nuovo nesting

## 🎨 Dati Visualizzati

### 📦 Per ogni ODL:
- **Part Number** e descrizione breve
- **Tool associato** e dimensioni (lunghezza × larghezza)
- **Ciclo di cura** (se presente)
- **Numero valvole** richieste
- **Priorità** ODL

### 🔥 Per ogni Autoclave:
- **Nome** e codice identificativo
- **Dimensioni** (lunghezza × larghezza)
- **Temperatura** e pressione massime
- **Carico massimo** e linee vuoto
- **Piano secondario** (se supportato)

## 🔧 Parametri Nesting

### 📏 Parametri Geometrici
- **Padding (mm)**: Spazio minimo attorno a ogni tool (default: 20mm)
- **Distanza Minima (mm)**: Distanza minima tra i tool (default: 15mm)

### ⚙️ Parametri Algoritmo
- **Priorità Area**: Ottimizza per utilizzo massimo dell'area (default: true)
- **Accorpamento ODL**: Raggruppa ODL con caratteristiche simili (default: false)

## 🔄 Flusso Operativo

### 1. **Selezione Dati**
```
Caricamento ODL "Attesa Cura" → Caricamento Autoclavi "DISPONIBILI"
```

### 2. **Configurazione**
```
Selezione ODL → Selezione Autoclavi → Impostazione Parametri
```

### 3. **Generazione**
```
Validazione Input → Invio Richiesta → Creazione BatchNesting → Navigazione Risultati
```

### 4. **Visualizzazione**
```
Caricamento Batch → Visualizzazione Dati → Azioni Disponibili
```

## 🛠️ Implementazione Tecnica

### 📄 Nuove Pagine
- `frontend/src/app/dashboard/curing/nesting/page.tsx`
- `frontend/src/app/dashboard/curing/nesting/result/[batch_id]/page.tsx`

### 📄 Endpoint API
- **POST** `/api/v1/nesting/genera` - Genera nuovo nesting
- **GET** `/api/v1/batch_nesting/{batch_id}` - Recupera risultati

### 📄 Componenti UI
- **shadcn/ui**: Card, Button, Checkbox, Input, Switch, Badge
- **Icone**: Package, Flame, LayoutGrid, Loader2, CheckCircle2

## 🔍 Validazioni Implementate

### ✅ Lato Client
- Almeno un ODL deve essere selezionato
- Almeno un'autoclave deve essere selezionata
- Parametri numerici con range validi (0-100)

### ✅ Lato Server
- Validazione esistenza ODL e autoclavi
- Conversione tipi dati (string → int)
- Gestione errori con messaggi dettagliati

## 📊 Gestione Stati

### 🔄 Loading States
- **Caricamento iniziale**: Spinner durante fetch dati
- **Generazione nesting**: Button disabilitato + spinner
- **Caricamento risultati**: Spinner durante fetch batch

### ⚠️ Error States
- **Errori di rete**: Toast con messaggio di errore
- **Dati mancanti**: Messaggi informativi
- **Batch non trovato**: Pagina errore con azioni recovery

## 🚀 Prossimi Sviluppi

### 📄 Canvas Grafico 2D
- Visualizzazione layout nesting interattivo
- Drag & drop per riposizionamento tool
- Zoom e pan per navigazione
- Export immagine layout

### 📄 Algoritmo Nesting Reale
- Sostituzione endpoint temporaneo
- Implementazione algoritmi ottimizzazione
- Calcolo statistiche reali (area, peso, valvole)
- Gestione vincoli complessi

### 📄 Funzionalità Avanzate
- Salvataggio configurazioni preferite
- Template parametri per tipologie prodotto
- Confronto risultati nesting multipli
- Integrazione con sistema scheduling

## 🐛 Note Tecniche

### 📄 Endpoint Temporaneo
L'endpoint `/api/v1/nesting/genera` è **temporaneo** e:
- Usa solo la prima autoclave selezionata
- Crea un BatchNesting senza calcoli reali
- Genera nome batch automatico
- Non calcola statistiche effettive

### 📄 Proxy API
Il frontend usa proxy Next.js per reindirizzare `/api/*` al backend FastAPI su `localhost:8000`.

### 📄 Ruoli Accesso
Solo utenti con ruolo **"Curing"** o **"ADMIN"** possono accedere alla funzionalità nesting.

## ✅ Test Completati

- ✅ Caricamento dati ODL e autoclavi
- ✅ Selezione multipla con checkbox
- ✅ Validazione input parametri
- ✅ Invio richiesta nesting
- ✅ Navigazione ai risultati
- ✅ Visualizzazione dati batch
- ✅ Gestione errori e loading states
- ✅ Responsive design

---

**Versione**: v1.1.2-DEMO  
**Data**: 27 Gennaio 2025  
**Autore**: Sistema CarbonPilot 