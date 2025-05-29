# 🎨 Guida al Layout Visuale del Nesting

## 📋 Panoramica

Il sistema di visualizzazione del nesting di CarbonPilot è stato potenziato con funzionalità avanzate per l'orientamento automatico dei tool e la visualizzazione di quote dettagliate. Questa guida spiega come utilizzare e comprendere le nuove funzionalità.

## 🎯 Funzionalità Principali

### 1. 🔄 Orientamento Automatico

Il sistema calcola automaticamente l'orientamento ottimale per ogni tool basandosi sull'efficienza spaziale:

- **Algoritmo**: Confronta l'efficienza tra orientamento normale e ruotato (90°)
- **Calcolo**: `efficienza = min(tool_dim / autoclave_dim)` per entrambe le dimensioni
- **Decisione**: Sceglie l'orientamento con efficienza maggiore
- **Visualizzazione**: Icona di rotazione 🔄 per tool ruotati

#### Esempio di Calcolo:
```
Tool: 600x400mm in Autoclave: 1200x800mm

Normale:   min(600/1200, 400/800) = min(0.5, 0.5) = 0.5
Ruotato:   min(400/1200, 600/800) = min(0.33, 0.75) = 0.33

Risultato: Orientamento normale (efficienza 0.5 > 0.33)
```

### 2. 📏 Quote Dimensionali

Le quote vengono visualizzate in tempo reale quando si seleziona o si passa il mouse su un tool:

- **Larghezza**: Quota orizzontale sopra il tool
- **Altezza**: Quota verticale a sinistra del tool (ruotata 90°)
- **Unità**: Millimetri (mm)
- **Colore**: Blu per distinguerle dal contenuto

### 3. 🖼️ Multi-Canvas

Gestione di più nesting contemporaneamente con due modalità di visualizzazione:

#### Vista a Tab
- Un tab per ogni autoclave
- Informazioni dettagliate dell'autoclave
- Nesting raggruppati per autoclave

#### Vista Griglia
- Layout a griglia 2 colonne
- Panoramica compatta
- Ideale per confronti rapidi

### 4. 📊 Statistiche Avanzate

Dashboard con metriche aggregate:
- **Nesting Totali**: Numero di nesting attivi
- **ODL Totali**: Somma di tutti gli ODL
- **Valvole Utilizzate**: Totale valvole in uso
- **Utilizzo Medio Area**: Percentuale media di utilizzo

## 🛠️ Componenti Implementati

### EnhancedNestingCanvas

Componente principale per la visualizzazione singola:

```typescript
<EnhancedNestingCanvas
  nestingData={nesting}
  canvasWidth={800}
  canvasHeight={500}
  showQuotes={true}
  showOrientation={true}
  enableZoom={true}
  onToolClick={(odlId) => handleToolClick(odlId)}
/>
```

**Props:**
- `nestingData`: Dati del nesting
- `canvasWidth/Height`: Dimensioni del canvas
- `showQuotes`: Mostra/nascondi quote dimensionali
- `showOrientation`: Mostra/nascondi indicatori di rotazione
- `enableZoom`: Abilita controlli zoom
- `onToolClick`: Callback per click su tool

### MultiNestingCanvas

Componente per visualizzazione multipla:

```typescript
<MultiNestingCanvas
  nestingList={nestings}
  onNestingSelect={handleNestingSelect}
  onToolClick={handleToolClick}
  showStatistics={true}
  groupByAutoclave={true}
/>
```

**Props:**
- `nestingList`: Array di nesting
- `onNestingSelect`: Callback per selezione nesting
- `onToolClick`: Callback per click su tool
- `showStatistics`: Mostra/nascondi statistiche
- `groupByAutoclave`: Raggruppa per autoclave

## 🎨 Sistema di Colori

### Priorità ODL
- 🔴 **Rosso**: Priorità Alta (1-2)
- 🟡 **Giallo**: Priorità Media (3-4)
- 🔵 **Blu**: Priorità Bassa (5+)

### Stati Nesting
- 🟢 **Verde**: Completato
- 🔵 **Blu**: In corso
- 🟣 **Viola**: Schedulato
- 🟡 **Giallo**: Bozza/Altri stati

### Indicatori Speciali
- 🟠 **Arancione**: Tool ruotato (icona rotazione)
- 🟡 **Giallo**: Tool evidenziato dalla ricerca
- 🔵 **Blu**: Tool selezionato (bordo spesso)

## 🔍 Funzionalità Interattive

### Zoom e Navigazione
- **Zoom In/Out**: Pulsanti + e - o rotella mouse
- **Livelli**: Da 50% a 300%
- **Centro**: Zoom centrato sull'autoclave

### Ricerca e Filtro
- **Campi ricercabili**: ID ODL, Part Number, Tool, Descrizione
- **Evidenziazione**: Tool corrispondenti evidenziati in giallo
- **Attenuazione**: Tool non corrispondenti attenuati

### Selezione Tool
- **Click**: Seleziona/deseleziona tool
- **Hover**: Mostra tooltip con dettagli
- **Dettagli**: Pannello informativo per tool selezionato

## 📐 Calcolo della Scala

La scala viene calcolata automaticamente per adattare l'autoclave al canvas:

```typescript
const scaleX = (canvasWidth * 0.85) / autoclave.lunghezza
const scaleY = (canvasHeight * 0.85) / autoclave.larghezza_piano
const scale = Math.min(scaleX, scaleY)
```

- **Margine**: 15% del canvas riservato per UI
- **Proporzioni**: Mantiene le proporzioni reali
- **Indicazione**: Scala mostrata come "1:X" nell'interfaccia

## 🧪 Testing e Validazione

### Script di Validazione

Esegui `python tools/validate_nesting_canvas.py` per verificare:

1. **Dimensioni Reali**: Scala corretta e adattamento tool
2. **Orientamento**: Calcolo automatico funzionante
3. **Quote**: Visualizzazione corretta delle dimensioni
4. **Multi-Canvas**: Gestione multipli nesting

### Pagina di Test

Visita `/dashboard/nesting-preview` per:
- Testare componenti con dati di esempio
- Confrontare modalità vista singola vs multi-canvas
- Verificare funzionalità avanzate
- Sperimentare con controlli interattivi

## 🔧 Configurazione Database

### Colonne Aggiunte alla Tabella Tools

```sql
ALTER TABLE tools ADD COLUMN peso FLOAT;
ALTER TABLE tools ADD COLUMN materiale VARCHAR(100);
ALTER TABLE tools ADD COLUMN orientamento_preferito VARCHAR(20) DEFAULT 'auto';
```

### Migrazione

Esegui `python backend/migrations/add_tool_peso_materiale.py` per:
- Aggiungere colonne mancanti
- Popolare con dati di esempio
- Verificare integrità struttura

## 📊 Metriche e Performance

### Ottimizzazioni Implementate
- **Calcolo Lazy**: Posizioni calcolate solo quando necessario
- **Memoization**: Cache dei calcoli di orientamento
- **Rendering Condizionale**: Quote mostrate solo su hover/selezione
- **Debounce**: Ricerca con ritardo per performance

### Limiti Consigliati
- **ODL per Nesting**: Massimo 50 per performance ottimale
- **Canvas Size**: 800x500px per bilanciare dettaglio e performance
- **Zoom Level**: 50%-300% per usabilità

## 🚀 Prossimi Sviluppi

### Funzionalità Pianificate
- **Drag & Drop**: Riposizionamento manuale tool
- **Esportazione**: PDF/SVG ad alta risoluzione
- **Simulazione**: Anteprima modifiche in tempo reale
- **Ottimizzazione AI**: Suggerimenti automatici di miglioramento

### Miglioramenti UX
- **Gesture Touch**: Supporto dispositivi touch
- **Keyboard Shortcuts**: Scorciatoie da tastiera
- **Temi**: Modalità scura/chiara
- **Accessibilità**: Supporto screen reader

---

## 📞 Supporto

Per domande o problemi relativi al layout visuale del nesting:

1. Consulta questo documento
2. Esegui gli script di validazione
3. Controlla i log del browser per errori
4. Verifica la struttura del database

**Nota**: Questa funzionalità è in continua evoluzione. Consulta il changelog per gli aggiornamenti più recenti. 