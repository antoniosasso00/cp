# Sezione ODL (Ordini di Lavoro) - Manta Group

## 📋 Panoramica

La sezione ODL gestisce gli ordini di lavoro in produzione, fornendo strumenti per il monitoraggio, la gestione e il tracciamento delle fasi di produzione dei componenti in composito.

## 🏗️ Struttura

```
frontend/src/app/dashboard/odl/
├── page.tsx                    # Pagina principale ODL (solo attivi)
├── monitoraggio/
│   └── page.tsx               # Pagina monitoraggio in tempo reale
├── components/
│   └── odl-modal.tsx          # Modal per creazione/modifica ODL
└── README.md                  # Questa documentazione
```

## 🚀 Funzionalità Principali

### 1. Pagina ODL Principale (`/dashboard/odl`)

**Scopo**: Visualizzazione e gestione degli ODL attivi in produzione.

**Caratteristiche**:
- ✅ **Solo ODL Attivi**: Mostra esclusivamente gli ordini non completati
- 📊 **Barra di Avanzamento**: Visualizzazione grafica del progresso per ogni ODL
- 🎯 **Sistema Priorità**: Indicatori visivi per la priorità degli ordini
- 🔍 **Ricerca Avanzata**: Filtro per ID, part number, tool e note
- ➕ **Gestione CRUD**: Creazione, modifica ed eliminazione ODL

**Componenti Chiave**:
- `BarraAvanzamento`: Componente per visualizzare il progresso delle fasi
- `getPriorityIcon`: Funzione per icone priorità (🔴🟠🟡🟢)
- `getPriorityBadgeVariant`: Gestione colori badge priorità

### 2. Pagina Monitoraggio (`/dashboard/odl/monitoraggio`)

**Scopo**: Monitoraggio in tempo reale e gestione avanzamento fasi.

**Caratteristiche**:
- ⏱️ **Tempo Reale**: Visualizzazione stato corrente e durata fasi attive
- 🔄 **Avanzamento Fasi**: Bottone per far progredire gli ODL tra le fasi
- 📚 **Storico Completo**: Accordion con tutti gli ODL completati
- 📈 **Timeline Fasi**: Cronologia dettagliata di ogni fase con durate
- 🔄 **Auto-refresh**: Pulsante per aggiornamento dati

**Integrazione Backend**:
- `tempoFasiApi`: Gestione automatica dei tempi di produzione
- Chiusura automatica fase corrente e apertura successiva
- Tracciamento completo delle durate

### 3. Modal Gestione ODL (`components/odl-modal.tsx`)

**Scopo**: Interfaccia per creazione e modifica ordini di lavoro.

**Caratteristiche**:
- 📝 **Titolo Descrittivo**: Mostra nome parte invece di ID
- 🔗 **Relazioni Intelligenti**: Filtro automatico tool per parte selezionata
- ✅ **Validazione Robusta**: Controlli di integrità dati
- 🚀 **Link Rapidi**: Creazione veloce parti/tool mancanti

## 🎨 Sistema di Fasi e Colori

### Fasi di Produzione

| Fase | Icona | Colore | Durata Media | Descrizione |
|------|-------|--------|--------------|-------------|
| Preparazione | ⚙️ | Grigio | 30 min | Setup iniziale e preparazione materiali |
| Laminazione | 🔨 | Blu | 120 min | Processo di laminazione del composito |
| Attesa Cura | ⏱️ | Giallo | 60 min | Attesa prima del processo di cura |
| Cura | 🔥 | Rosso | 180 min | Processo di cura in autoclave |
| Finito | ✅ | Verde | - | Ordine completato |

### Sistema Priorità

| Livello | Icona | Colore | Range | Descrizione |
|---------|-------|--------|-------|-------------|
| Critica | 🔴 | Rosso | ≥ 8 | Priorità massima, urgente |
| Alta | 🟠 | Arancione | 5-7 | Priorità alta, importante |
| Media | 🟡 | Giallo | 3-4 | Priorità normale |
| Bassa | 🟢 | Verde | 1-2 | Priorità bassa, non urgente |

## 🔧 Configurazione Tecnica

### Costanti Principali

```typescript
// Configurazione fasi con durate proporzionali
const FASI_ODL = [
  { nome: "Preparazione", durata: 30, icona: "⚙️", colore: "bg-gray-400" },
  { nome: "Laminazione", durata: 120, icona: "🔨", colore: "bg-blue-400" },
  { nome: "Attesa Cura", durata: 60, icona: "⏱️", colore: "bg-yellow-400" },
  { nome: "Cura", durata: 180, icona: "🔥", colore: "bg-red-400" },
  { nome: "Finito", durata: 0, icona: "✅", colore: "bg-green-400" }
]

// Mapping stati ODL a fasi tempi_produzione
const STATO_A_FASE = {
  "Laminazione": "laminazione",
  "Attesa Cura": "attesa_cura", 
  "Cura": "cura"
}
```

### API Integration

```typescript
// Caricamento ODL con filtri
const data = await odlApi.getAll(filter)

// Caricamento tempi fasi per monitoraggio
const fasi = await tempoFasiApi.getAll({ odl_id: odl.id })

// Avanzamento automatico con gestione fasi
await tempoFasiApi.update(faseAttiva.id, { fine_fase: new Date().toISOString() })
await odlApi.update(odl.id, { status: nextStatus })
await tempoFasiApi.create({ odl_id, fase: nuovaFase, inizio_fase: new Date().toISOString() })
```

## 📊 Flusso di Lavoro Tipico

### 1. Creazione Nuovo ODL
1. Click "Nuovo ODL" nella pagina principale
2. Selezione parte dal catalogo
3. Selezione tool compatibile (filtrato automaticamente)
4. Impostazione priorità e note
5. Salvataggio con stato iniziale "Preparazione"

### 2. Monitoraggio Produzione
1. Navigazione a "Monitoraggio ODL"
2. Visualizzazione ODL in corso con fase attuale
3. Click "Avanza" per passare alla fase successiva
4. Conferma avanzamento nel dialog
5. Aggiornamento automatico tempi e stato

### 3. Gestione Completamento
1. ODL raggiunge stato "Finito"
2. Scompare dalla lista attivi
3. Appare nello storico completati
4. Timeline completa visibile nell'accordion

## 🎯 Best Practices

### Performance
- **Lazy Loading**: Caricamento dati solo quando necessario
- **Debouncing**: Ricerca con ritardo per ridurre chiamate API
- **Caching**: Riutilizzo dati caricati quando possibile

### UX/UI
- **Feedback Visivo**: Loading states e animazioni fluide
- **Messaggi Chiari**: Toast informativi per ogni azione
- **Responsive**: Interfaccia ottimizzata per tutti i dispositivi

### Gestione Errori
- **Try-Catch**: Gestione robusta degli errori API
- **Fallback**: Messaggi di errore user-friendly
- **Recovery**: Possibilità di riprovare operazioni fallite

## 🧪 Testing

### Dati di Test
```bash
# Popola database con dati di esempio
cd tools && python seed_test_data.py --debug
```

### Scenari di Test
1. **Creazione ODL**: Nuovo ordine con parte e tool esistenti
2. **Modifica ODL**: Cambio priorità e note
3. **Avanzamento**: Progressione attraverso tutte le fasi
4. **Ricerca**: Filtro per vari criteri
5. **Responsive**: Test su dispositivi mobili

## 🔮 Sviluppi Futuri

### Funzionalità Pianificate
- **Dashboard Analytics**: Grafici tempi medi per fase
- **Notifiche**: Alert per ODL in ritardo o priorità alta
- **Batch Operations**: Operazioni multiple su ODL selezionati
- **Export**: Esportazione dati per reporting
- **Scheduling**: Integrazione con pianificazione autoclavi

### Miglioramenti Tecnici
- **Real-time Updates**: WebSocket per aggiornamenti live
- **Offline Support**: Funzionalità base offline
- **Advanced Filters**: Filtri più granulari e salvabili
- **Audit Trail**: Tracciamento completo modifiche

## 📞 Supporto

Per problemi o domande sulla sezione ODL:
1. Verificare i log del browser (F12 → Console)
2. Controllare connessione backend (http://localhost:8000/docs)
3. Consultare la documentazione API
4. Verificare dati di test con seed script 