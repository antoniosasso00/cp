# 📐 Visualizzazione Nesting 2D - CarbonPilot

## 🎯 Panoramica

La pagina di visualizzazione del nesting permette di vedere i risultati dell'algoritmo OR-Tools in un canvas 2D interattivo, mostrando la disposizione ottimale dei tool nell'autoclave con proporzioni reali.

## 📍 Posizione

```
frontend/src/app/nesting/result/[batch_id]/page.tsx
```

## 🚀 Funzionalità Implementate

### 📊 Canvas 2D con React-Konva
- **Scala dinamica**: Calcolo automatico della scala per mantenere le proporzioni reali
- **Griglia di riferimento**: Tacche ogni 100mm per orientamento visivo
- **Bordi autoclave**: Visualizzazione chiara dei limiti del piano di carico

### 🔧 Visualizzazione Tool
- **Rettangoli colorati**: Ogni tool ha un colore univoco per distinguibilità
- **Informazioni integrate**: ODL ID, Part Number, dimensioni reali
- **Indicatore rotazione**: Simbolo visivo per tool ruotati di 90°
- **Tooltip interattivo**: Dettagli completi al passaggio del mouse

### 📈 Statistiche in Tempo Reale
- Numero di tool posizionati
- Peso totale del carico
- Area utilizzata (m²)
- Efficienza di utilizzo (%)

### ⚙️ Interazioni Utente
- **Rimozione ODL**: Click su un tool per rimuoverlo dalla configurazione
- **Conferma configurazione**: Pulsante per accettare il layout e cambiare stato
- **Navigazione**: Pulsante per tornare alla pagina precedente

### 📋 Informazioni Dettagliate
- **Dettagli batch**: ID, date di creazione/aggiornamento, note
- **Informazioni autoclave**: Nome, produttore, dimensioni piano
- **ODL esclusi**: Tabella con motivi di esclusione dal nesting

## 🔗 API Utilizzate

### Endpoint Principale
```
GET /api/v1/batch_nesting/{batch_id}/full
```

**Risposta include:**
- Configurazione JSON con posizioni tool
- Informazioni autoclave (nome, dimensioni)
- ODL esclusi con motivi
- Statistiche aggregate

### Endpoint Aggiornamento
```
PUT /api/v1/batch_nesting/{batch_id}
```

**Per confermare la configurazione:**
```json
{
  "stato": "confermato",
  "confermato_da_utente": "utente_frontend",
  "confermato_da_ruolo": "Curing"
}
```

## 📐 Calcolo Scala Dinamica

```typescript
const maxCanvasWidth = 800;
const maxCanvasHeight = 600;
const autoclaveWidth = configurazione_json.canvas_width;
const autoclaveHeight = configurazione_json.canvas_height;

const scaleX = maxCanvasWidth / autoclaveWidth;
const scaleY = maxCanvasHeight / autoclaveHeight;
const scale = Math.min(scaleX, scaleY, 1); // Non ingrandire oltre le dimensioni reali
```

## 🎨 Struttura Dati Tool

```typescript
interface ToolPosition {
  odl_id: number;
  x: number;           // Posizione X in mm
  y: number;           // Posizione Y in mm
  width: number;       // Larghezza in mm
  height: number;      // Altezza in mm
  peso: number;        // Peso in kg
  rotated?: boolean;   // Se ruotato di 90°
  part_number?: string;
  descrizione?: string;
  ciclo_cura?: string;
  tool_nome?: string;
}
```

## 🔄 Stati del Batch

| Stato | Descrizione | Azioni Disponibili |
|-------|-------------|-------------------|
| `sospeso` | In attesa di conferma | Rimozione ODL, Conferma |
| `confermato` | Confermato per produzione | Solo visualizzazione |
| `terminato` | Completato | Solo visualizzazione |

## 🎯 Utilizzo

### 1. Accesso alla Pagina
Navigare a: `/nesting/result/{batch_id}`

### 2. Visualizzazione
- Il canvas mostra automaticamente tutti i tool posizionati
- Le dimensioni sono in scala reale rispetto all'autoclave
- I colori sono generati automaticamente per distinguere i tool

### 3. Interazione
- **Hover**: Mostra tooltip con dettagli tool
- **Click**: Conferma rimozione ODL (solo se stato = "sospeso")
- **Conferma**: Cambia stato batch a "confermato"

### 4. Informazioni Aggiuntive
- Pannello destro con statistiche e dettagli
- Tabella ODL esclusi (se presenti)
- Informazioni autoclave utilizzata

## 🛠️ Dipendenze Tecniche

### Frontend
```json
{
  "konva": "^9.x",
  "react-konva": "^18.x"
}
```

### Componenti UI
- Card, Button, Badge (shadcn/ui)
- Alert, Separator (shadcn/ui)
- Lucide React icons

## 🔧 Configurazione Sviluppo

### 1. Installazione Dipendenze
```bash
cd frontend
npm install konva react-konva
```

### 2. Avvio Server Backend
```bash
cd backend
py main.py
```

### 3. Avvio Frontend
```bash
cd frontend
npm run dev
```

### 4. Test
Navigare a: `http://localhost:3001/nesting/result/{batch_id}`

## 📊 Esempio URL di Test

Con i dati di esempio nel database:
```
http://localhost:3001/nesting/result/45ea9210-071c-498f-97ba-409e344745fc
```

## 🚨 Gestione Errori

### Errori Comuni
- **Batch non trovato**: Messaggio di errore con redirect
- **Configurazione mancante**: Visualizzazione vuota con avviso
- **Server non raggiungibile**: Alert di connessione

### Debug
- Console browser per log dettagliati
- Network tab per verificare chiamate API
- Controllo stato server backend

## 🔮 Sviluppi Futuri

### Funzionalità Pianificate
- [ ] Drag & drop per riposizionamento tool
- [ ] Zoom e pan del canvas
- [ ] Esportazione immagine/PDF
- [ ] Confronto configurazioni multiple
- [ ] Animazioni di caricamento
- [ ] Modalità fullscreen

### Miglioramenti UX
- [ ] Temi colore personalizzabili
- [ ] Filtri per tipo tool
- [ ] Ricerca tool per Part Number
- [ ] Cronologia modifiche

## 📝 Note Tecniche

### Performance
- Canvas ottimizzato per max 50 tool simultanei
- Rendering on-demand per interazioni
- Debounce su operazioni costose

### Compatibilità
- Chrome/Edge: Supporto completo
- Firefox: Supporto completo
- Safari: Supporto base (test richiesti)
- Mobile: Responsive design

### Sicurezza
- Validazione input lato client e server
- Sanitizzazione dati configurazione
- Rate limiting su API calls

---

**Versione**: v1.1.4-DEMO  
**Ultimo aggiornamento**: 31 Maggio 2025  
**Autore**: CarbonPilot Development Team 