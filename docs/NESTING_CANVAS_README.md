# 🎨 Nesting Canvas - Visualizzazione Interattiva

## 📋 Panoramica

Il **NestingCanvas** è un componente React avanzato che fornisce una visualizzazione SVG interattiva dei layout di nesting. Permette agli utenti di visualizzare, esplorare e analizzare i layout di nesting con funzionalità avanzate di zoom, pan e informazioni dettagliate.

## ✨ Funzionalità Principali

### 🔍 Visualizzazione Interattiva
- **Canvas SVG scalabile** con rendering fedele alle dimensioni reali
- **Zoom e Pan** fluidi con controlli mouse e touch
- **Griglia di riferimento** configurabile per orientamento
- **Tooltip informativi** con dettagli completi per ogni ODL

### 🎯 Rappresentazione Accurata
- **Bounding box precisi** per ogni tool con quote dimensionali
- **Orientamento automatico** con indicatori di rotazione
- **Colori basati su priorità** con gradiente verde-rosso
- **Valvole richieste** visualizzate per ogni ODL

### 🎛️ Controlli Avanzati
- **Toggle visualizzazione**: griglia, quote, nomi, valvole, priorità
- **Selezione ODL** con evidenziazione e dettagli
- **Esportazione PNG** del layout completo
- **Fit-to-view** automatico per ottimizzare la visualizzazione

### 📊 Informazioni Dettagliate
- **Legenda priorità** con scala colori
- **Statistiche layout** (efficienza, valvole, area)
- **ODL esclusi** con motivi di esclusione
- **Informazioni autoclave** con dimensioni e capacità

## 🚀 Utilizzo

### Integrazione Base
```tsx
import { NestingCanvas } from '@/components/nesting/NestingCanvas'

function MyComponent() {
  const handleToolClick = (odl: ODLLayoutInfo) => {
    console.log('Tool selezionato:', odl)
  }

  return (
    <NestingCanvas
      nestingId={123}
      onToolClick={handleToolClick}
      showControls={true}
      height={600}
    />
  )
}
```

### Props Disponibili
- `nestingId: number` - ID del nesting da visualizzare
- `onToolClick?: (odl: ODLLayoutInfo) => void` - Callback per click su tool
- `showControls?: boolean` - Mostra/nasconde controlli (default: true)
- `className?: string` - Classi CSS aggiuntive
- `height?: number` - Altezza del canvas in pixel (default: 600)

## 🎨 Caratteristiche Visive

### Codifica Colori
- **Verde**: Priorità bassa (1-3)
- **Giallo**: Priorità media (4-6)
- **Arancione**: Priorità alta (7-8)
- **Rosso**: Priorità critica (9-10)
- **Rosso scuro**: ODL esclusi

### Indicatori Visivi
- **Pattern diagonale**: Tool ruotati di 90°
- **Icona rotazione**: Cerchio bianco con freccia
- **Badge priorità**: Numero in cerchio bianco
- **Contatore valvole**: Numero seguito da "V"

### Elementi Interattivi
- **Hover**: Ombreggiatura e cambio opacità
- **Selezione**: Bordo blu e quote dimensionali
- **Tooltip**: Informazioni complete al passaggio del mouse

## 🔧 Controlli Utente

### Navigazione
- **Mouse Wheel**: Zoom in/out
- **Click + Drag**: Pan del viewport
- **Pulsanti Zoom**: +/- per controllo preciso
- **Reset**: Ripristina vista originale
- **Fit View**: Adatta alla finestra

### Visualizzazione
- **Griglia**: Toggle griglia di riferimento
- **Quote**: Mostra/nasconde dimensioni
- **Nomi**: Visualizza part number dei tool
- **Valvole**: Mostra numero valvole richieste
- **Priorità**: Badge con livello priorità
- **Esclusi**: Evidenzia ODL non posizionati

## 📈 Statistiche e Informazioni

### Pannello Statistiche
- **ODL totali**: Numero complessivo di ODL
- **ODL posizionati**: Quanti sono nel layout
- **ODL esclusi**: Quanti non hanno trovato posto
- **Valvole utilizzate/totali**: Rapporto utilizzo
- **Area utilizzata**: Superficie occupata in cm²
- **Efficienza**: Percentuale di utilizzo dell'autoclave

### Legenda Priorità
- **Scala visiva**: Colori per ogni livello di priorità
- **Riferimento rapido**: Identificazione immediata
- **Consistenza**: Stessi colori in tutta l'applicazione

## 🔄 Integrazione con Altri Componenti

### NestingSelector
Il canvas si integra con `NestingSelector` per permettere la selezione di nesting esistenti:

```tsx
const [selectedNestingId, setSelectedNestingId] = useState<number | null>(null)

return (
  <>
    {!selectedNestingId ? (
      <NestingSelector onNestingSelected={setSelectedNestingId} />
    ) : (
      <NestingCanvas nestingId={selectedNestingId} />
    )}
  </>
)
```

### Tab Preview
Integrato nel tab "Preview & Ottimizzazione" con toggle tra vista tabellare e canvas:
- **Modalità Tabella**: Vista tradizionale con liste e statistiche
- **Modalità Canvas**: Visualizzazione grafica interattiva

## 🎯 Casi d'Uso

### 1. Verifica Layout
- Controllo visivo della disposizione dei tool
- Verifica dell'utilizzo ottimale dello spazio
- Identificazione di problemi di posizionamento

### 2. Presentazioni
- Esportazione di immagini per report
- Visualizzazione chiara per stakeholder
- Documentazione dei layout approvati

### 3. Analisi Efficienza
- Confronto visivo tra diverse configurazioni
- Identificazione di aree di miglioramento
- Ottimizzazione dell'utilizzo dell'autoclave

### 4. Troubleshooting
- Identificazione rapida di ODL esclusi
- Analisi dei motivi di esclusione
- Verifica dei vincoli di spazio

## 🔮 Sviluppi Futuri

### Funzionalità Pianificate
- **Editing drag-and-drop**: Riposizionamento manuale dei tool
- **Simulazione multi-piano**: Visualizzazione 3D per autoclavi multi-livello
- **Animazioni**: Transizioni fluide tra stati
- **Confronto layout**: Vista side-by-side di diverse configurazioni
- **Esportazione avanzata**: PDF, SVG, formati CAD

### Miglioramenti UX
- **Minimap**: Navigazione rapida in layout grandi
- **Ricerca visiva**: Evidenziazione di tool specifici
- **Filtri avanzati**: Visualizzazione selettiva per criteri
- **Modalità presentazione**: Vista fullscreen ottimizzata

## 🛠️ Considerazioni Tecniche

### Performance
- **Rendering ottimizzato**: SVG con elementi riutilizzabili
- **Lazy loading**: Caricamento dati on-demand
- **Memoizzazione**: Cache dei calcoli pesanti
- **Viewport culling**: Rendering solo elementi visibili

### Accessibilità
- **Keyboard navigation**: Controlli da tastiera
- **Screen reader**: Descrizioni alternative
- **Contrasto**: Colori accessibili
- **Focus management**: Navigazione logica

### Responsive Design
- **Adattamento mobile**: Touch gestures
- **Breakpoint**: Layout ottimizzati per diverse dimensioni
- **Scalabilità**: Mantenimento proporzioni su tutti i dispositivi

---

*Documentazione aggiornata: Gennaio 2025*
*Versione componente: 1.0.0* 