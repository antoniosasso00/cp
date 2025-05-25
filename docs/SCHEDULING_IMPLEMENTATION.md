# 📅 Sistema di Scheduling Completo - CarbonPilot

## 🎯 Panoramica

Il sistema di scheduling di CarbonPilot è stato completamente implementato con tutte le funzionalità richieste. Supporta la pianificazione avanzata di autoclavate con gestione automatica, priorità, azioni operatore e integrazione completa con ODL e nesting.

## ✅ Funzionalità Implementate

### 🧩 1. FORM SEMPLIFICATO
- **✅ Completato**: Componente `ScheduleForm.tsx`
- **Funzionalità**:
  - Selezione data/ora inizio
  - Selezione autoclave
  - Selezione categoria/sotto-categoria
  - Calcolo automatico data fine da dati storici (`tempi_produzione`)
  - Placeholder "Non disponibile" quando mancano dati storici
  - Validazione completa del form
  - Supporto modalità dark

### 📅 2. VISUALIZZAZIONE NEL CALENDARIO
- **✅ Completato**: Componente `CalendarSchedule.tsx` aggiornato
- **Funzionalità**:
  - Eventi schedulati in calendario (giorno/settimana/mese)
  - Visualizzazione Part Number o Sotto-categoria
  - Autoclave associata
  - Stati: In attesa, Schedulato, Completato, Previsionale, In corso, Posticipato
  - Tooltip dettagliato con data fine stimata
  - Supporto modalità dark completo
  - Colori differenziati per tipo e stato
  - Badge priorità visivi

### 🔄 3. SCHEDULAZIONE AUTOMATICA PER FREQUENZA
- **✅ Completato**: Componente `RecurringScheduleForm.tsx`
- **Funzionalità**:
  - Configurazione PN o sotto-categoria
  - Numero pezzi/mese da produrre
  - Generazione automatica eventi distribuiti sul mese
  - Eventi con stato "Previsionale"
  - Anteprima distribuzione con statistiche

### 🤖 4. ASSOCIAZIONE AUTOMATICA ODL
- **✅ Completato**: Backend service `schedule_service.py`
- **Funzionalità**:
  - Ricerca ODL compatibili per data
  - Priorità per stesso PN o categoria
  - Aggiunta automatica a schedulazione/autoclave
  - Integrazione con algoritmo nesting
  - Warning per eventi senza ODL compatibili

### 🧠 5. GESTIONE PRIORITÀ
- **✅ Completato**: Sistema completo di priorità
- **Funzionalità**:
  - ODL con priorità alta (≥8) assegnati per primi
  - Colori diversi per eventi ad alta priorità (rosso)
  - Badge numerico priorità nella preview evento
  - Bordo dorato per eventi prioritari
  - Ordinamento automatico per priorità

### 🧪 6. CONFERMA OPERATORE & FLUSSO
- **✅ Completato**: Sistema azioni operatore
- **Funzionalità**:
  - Azioni "Avvia", "Posticipa", "Completa"
  - Cambio stato ODL a "In Autoclave" all'avvio
  - Spostamento eventi con posticipo
  - Toast/feedback per ogni interazione
  - Tooltip interattivo con azioni disponibili
  - Gestione stati avanzati

## 🛠️ Architettura Tecnica

### Backend (FastAPI + SQLAlchemy)

#### Modelli Database
- **`ScheduleEntry`**: Modello principale con nuovi campi
  - `schedule_type`: Tipo di schedulazione (ODL, categoria, ricorrente)
  - `categoria`, `sotto_categoria`: Per schedulazioni per categoria
  - `is_recurring`: Flag per schedulazioni ricorrenti
  - `estimated_duration_minutes`: Durata stimata
  - `note`: Note aggiuntive

- **`TempoProduzione`**: Nuova tabella per tempi storici
  - Tempi medi per part_number, categoria, sotto_categoria
  - Statistiche (min, max, numero osservazioni)
  - Metodo `get_tempo_stimato()` con priorità

#### API Endpoints
- `GET /api/v1/schedules`: Lista schedulazioni con filtri
- `POST /api/v1/schedules`: Crea schedulazione
- `POST /api/v1/schedules/recurring`: Crea schedulazioni ricorrenti
- `POST /api/v1/schedules/{id}/action`: Azioni operatore
- `GET /api/v1/schedules/production-times`: Gestione tempi
- `GET /api/v1/schedules/auto-generate`: Generazione automatica

#### Servizi
- **`schedule_service.py`**: Logica business principale
  - `calculate_estimated_end_time()`: Calcolo automatico fine
  - `create_recurring_schedules()`: Distribuzione ricorrente
  - `handle_operator_action()`: Gestione azioni
  - `assign_compatible_odl()`: Assegnazione automatica ODL

### Frontend (Next.js + TypeScript + Tailwind)

#### Componenti
- **`CalendarSchedule.tsx`**: Calendario principale con react-big-calendar
- **`ScheduleForm.tsx`**: Form semplificato per nuove schedulazioni
- **`RecurringScheduleForm.tsx`**: Form per schedulazioni ricorrenti
- **`EventTooltip`**: Tooltip interattivo con azioni operatore

#### Tipi TypeScript
- **`ScheduleEntryType`**: Enum per tipi di schedulazione
- **`ScheduleEntryStatus`**: Enum per stati avanzati
- **`ScheduleOperatorActionData`**: Tipo per azioni operatore
- **`CalendarEvent`**: Tipo per eventi calendario

#### API Client
- **`scheduleApi`**: Client completo con tutti gli endpoint
- Gestione errori e loading states
- Supporto filtri e parametri

## 🎨 UI/UX Features

### Modalità Dark
- Supporto completo per tema scuro
- Stili personalizzati per react-big-calendar
- Colori ottimizzati per leggibilità

### Colori e Indicatori
- **Blu**: Schedulazioni ODL specifiche
- **Viola**: Schedulazioni per categoria
- **Ciano**: Schedulazioni per sotto-categoria
- **Verde**: Schedulazioni ricorrenti
- **Rosso**: Priorità alta (≥8)
- **Giallo**: In attesa
- **Grigio**: Previsionale
- **Arancione**: Posticipato

### Emoji e Badge
- 🔥 Priorità alta
- 📋 Previsionale
- ⏳ In attesa
- 🔄 In corso
- ⏸️ Posticipato
- ✅ Completato

## 📊 Database Schema Updates

### Nuove Colonne `schedule_entries`
```sql
ALTER TABLE schedule_entries ADD COLUMN schedule_type VARCHAR(50) DEFAULT 'odl_specifico';
ALTER TABLE schedule_entries ADD COLUMN categoria VARCHAR(100);
ALTER TABLE schedule_entries ADD COLUMN sotto_categoria VARCHAR(100);
ALTER TABLE schedule_entries ADD COLUMN is_recurring BOOLEAN DEFAULT 0;
ALTER TABLE schedule_entries ADD COLUMN pieces_per_month INTEGER;
ALTER TABLE schedule_entries ADD COLUMN note TEXT;
ALTER TABLE schedule_entries ADD COLUMN estimated_duration_minutes INTEGER;
```

### Nuova Tabella `tempi_produzione`
```sql
CREATE TABLE tempi_produzione (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number VARCHAR(100),
    categoria VARCHAR(100),
    sotto_categoria VARCHAR(100),
    tempo_medio_minuti REAL NOT NULL,
    tempo_minimo_minuti REAL,
    tempo_massimo_minuti REAL,
    numero_osservazioni INTEGER DEFAULT 1 NOT NULL,
    ultima_osservazione TIMESTAMP NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Come Utilizzare

### 1. Avvio Sistema
```bash
# Backend
cd backend
python main.py

# Frontend
cd frontend
npm run dev
```

### 2. Accesso Interfaccia
- Naviga su `http://localhost:3000/dashboard/schedule`
- Il calendario mostra tutte le schedulazioni esistenti

### 3. Creazione Schedulazioni
- **Nuova**: Clicca "➕ Nuova" o su uno slot vuoto del calendario
- **Ricorrente**: Clicca "🔄 Ricorrente" per schedulazioni per frequenza
- **Auto-genera**: Clicca "🤖 Auto-genera" per generazione automatica

### 4. Gestione Eventi
- Clicca su un evento per vedere dettagli e azioni
- Usa "▶️ Avvia", "⏸️ Posticipa", "✅ Completa" per gestire il flusso
- Elimina eventi non necessari con "🗑️ Elimina"

## 🔧 Configurazione

### Tempi di Produzione
I tempi storici sono gestiti automaticamente. Per aggiungere nuovi tempi:
```python
# Backend script
python insert_sample_data.py
```

### Dati di Test
Il sistema include dati di esempio per:
- Aerospace: Wing Components (240 min), Fuselage (360 min)
- Automotive: Engine Parts (180 min)
- Medical: Implants (120 min)
- Industrial: Machinery (480 min)

## 🐛 Troubleshooting

### Problemi Comuni
1. **Calendario vuoto**: Verifica che ci siano schedulazioni nel database
2. **Errori API**: Controlla che il backend sia avviato su porta 8000
3. **Tempi non calcolati**: Verifica che esistano dati in `tempi_produzione`

### Log e Debug
- Backend: Log dettagliati in console
- Frontend: Errori in DevTools console
- Database: Usa script di verifica schema

## 📈 Metriche e Performance

### Ottimizzazioni Implementate
- Indici database per query veloci
- Lazy loading componenti
- Memoizzazione callback React
- Gestione efficiente stati

### Scalabilità
- Supporto filtri data range per grandi dataset
- Paginazione API pronta per implementazione
- Cache client per dati statici (autoclavi, categorie)

## 🔮 Sviluppi Futuri

### Funzionalità Pianificate
- [ ] Notifiche push per scadenze
- [ ] Export calendario in formati standard (iCal, PDF)
- [ ] Dashboard analytics con KPI
- [ ] Integrazione con sistemi ERP esterni
- [ ] Mobile app companion

### Miglioramenti Tecnici
- [ ] WebSocket per aggiornamenti real-time
- [ ] Caching avanzato con Redis
- [ ] Test automatizzati completi
- [ ] Deployment containerizzato

---

## 🎉 Conclusione

Il sistema di scheduling di CarbonPilot è ora completamente funzionale e pronto per l'uso in produzione. Tutte le funzionalità richieste sono state implementate con un'architettura solida, UI intuitiva e performance ottimizzate.

**Stato**: ✅ **COMPLETATO**  
**Versione**: 1.0.0  
**Data**: Dicembre 2024 