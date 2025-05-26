# 📊 Componenti di Visualizzazione Progresso ODL

## 🎯 Panoramica

Questo modulo fornisce una visualizzazione avanzata dello stato degli ODL con barra di progresso temporale segmentata e storico dettagliato. I componenti sono progettati per essere riutilizzabili e integrabili in diverse viste dell'applicazione.

## 🧩 Componenti Principali

### 1. `OdlProgressBar`

**Scopo**: Visualizza una barra di progresso temporale segmentata per gli stati degli ODL.

**Caratteristiche**:
- ✅ **Segmentazione Temporale**: Ogni segmento rappresenta un intervallo temporale tra stati
- 🎨 **Colori Configurabili**: Ogni stato ha colori e icone specifiche
- 📊 **Proporzioni Reali**: La larghezza dei segmenti è proporzionale alla durata effettiva
- 🔍 **Tooltip Informativi**: Hover per dettagli su durata, timestamp inizio/fine
- ⚠️ **Indicatori di Ritardo**: Badge per ODL che superano le 24h nello stesso stato
- 🎯 **Indicatore Stato Corrente**: Linea animata per lo stato attivo

**Configurazione Stati**:
```typescript
const STATI_CONFIG = {
  'Preparazione': { color: 'bg-gray-400', icon: '📋', order: 1 },
  'Laminazione': { color: 'bg-blue-500', icon: '🔧', order: 2 },
  'In Coda': { color: 'bg-orange-400', icon: '⏳', order: 2.5 },
  'Attesa Cura': { color: 'bg-yellow-500', icon: '⏱️', order: 3 },
  'Cura': { color: 'bg-red-500', icon: '🔥', order: 4 },
  'Finito': { color: 'bg-green-500', icon: '✅', order: 5 }
};
```

**Utilizzo**:
```tsx
import { OdlProgressBar } from '@/components/ui/OdlProgressBar';

<OdlProgressBar
  odl={progressData}
  showDetails={true}
  className="my-4"
  onTimelineClick={() => setTimelineOpen(true)}
/>
```

### 2. `OdlTimelineModal`

**Scopo**: Modal per visualizzare lo storico completo degli ODL con timeline dettagliata.

**Caratteristiche**:
- 📈 **Statistiche Riassuntive**: Durata totale, numero transizioni, efficienza stimata
- 📋 **Timeline Eventi**: Cronologia completa con icone, durate e dettagli
- 📊 **Durate per Stato**: Breakdown del tempo trascorso in ogni fase
- 💾 **Esportazione CSV**: Download dei dati per analisi esterne
- 🔗 **Informazioni Correlate**: Collegamenti a nesting, autoclavi, responsabili

**Utilizzo**:
```tsx
import { OdlTimelineModal } from '@/components/ui/OdlTimelineModal';

<OdlTimelineModal
  odlId={123}
  isOpen={timelineOpen}
  onOpenChange={setTimelineOpen}
/>
```

### 3. `OdlProgressWrapper`

**Scopo**: Componente wrapper che gestisce il caricamento dei dati e integra barra + modal.

**Caratteristiche**:
- 🔄 **Auto-refresh**: Aggiornamento automatico dei dati (configurabile)
- ⚡ **Gestione Stati**: Loading, errore, dati vuoti
- 🎛️ **Configurabile**: Dettagli visibili/nascosti, intervalli di refresh
- 🔗 **Integrazione Completa**: Barra di progresso + modal timeline

**Utilizzo**:
```tsx
import { OdlProgressWrapper } from '@/components/ui/OdlProgressWrapper';

<OdlProgressWrapper
  odlId={odl.id}
  showDetails={false}
  autoRefresh={true}
  refreshInterval={30}
  className="min-h-[40px]"
/>
```

## 🔌 API Backend

### Endpoint `/api/v1/odl-monitoring/monitoring/{odl_id}/progress`

**Scopo**: Dati ottimizzati per la barra di progresso.

**Risposta**:
```json
{
  "id": 123,
  "status": "Attesa Cura",
  "created_at": "2025-01-25T10:00:00Z",
  "updated_at": "2025-01-25T14:30:00Z",
  "timestamps": [
    {
      "stato": "Preparazione",
      "inizio": "2025-01-25T10:00:00Z",
      "fine": "2025-01-25T11:30:00Z",
      "durata_minuti": 90
    },
    {
      "stato": "Laminazione",
      "inizio": "2025-01-25T11:30:00Z",
      "fine": "2025-01-25T14:30:00Z",
      "durata_minuti": 180
    }
  ],
  "tempo_totale_stimato": 270
}
```

### Endpoint `/api/v1/odl-monitoring/monitoring/{odl_id}/timeline`

**Scopo**: Dati completi per il modal timeline.

**Risposta**:
```json
{
  "odl_id": 123,
  "parte_nome": "Componente A",
  "tool_nome": "Tool-001",
  "status_corrente": "Attesa Cura",
  "logs": [...],
  "statistiche": {
    "durata_totale_minuti": 270,
    "durata_per_stato": {...},
    "numero_transizioni": 2,
    "efficienza_stimata": 85
  }
}
```

## 🎨 Integrazione nelle Viste

### Vista ODL Principale (`/dashboard/shared/odl`)

```tsx
// Sostituisce la vecchia BarraAvanzamentoODL
<TableCell className="w-64">
  <OdlProgressWrapper 
    odlId={item.id}
    showDetails={false}
    className="min-h-[40px]"
  />
</TableCell>
```

### Dashboard Monitoraggio (`/dashboard/responsabile/odl-monitoring`)

```tsx
// Integrata nella lista di monitoraggio
<OdlProgressWrapper 
  odlId={odl.id}
  showDetails={false}
  className="mb-2"
/>
```

### Dashboard Responsabile

```tsx
// Negli ODL in attesa di nesting
<OdlProgressWrapper 
  odlId={odl.id}
  showDetails={false}
  className="text-xs"
/>
```

## 🧪 Test e Validazione

### Test Locali Suggeriti

1. **Creazione ODL con Stati Diversi**:
   ```bash
   # Crea ODL in vari stati per verificare proporzioni
   curl -X POST /api/v1/odl -d '{"parte_id": 1, "tool_id": 1, "priorita": 3}'
   ```

2. **Simulazione Ritardi**:
   ```sql
   -- Modifica timestamp nel DB per simulare ritardi
   UPDATE odl_logs SET timestamp = timestamp - INTERVAL '2 days' WHERE odl_id = 123;
   ```

3. **Test Timeline**:
   - Apri modal timeline per ODL con molti eventi
   - Verifica calcolo durate e statistiche
   - Test esportazione CSV

4. **Test Auto-refresh**:
   - Abilita auto-refresh su ODL attivi
   - Verifica aggiornamenti in tempo reale

## 🔧 Personalizzazione

### Aggiungere Nuovi Stati

1. **Aggiorna `STATI_CONFIG`** in `OdlProgressBar.tsx`:
```typescript
'Nuovo Stato': { 
  color: 'bg-purple-500', 
  textColor: 'text-purple-700',
  order: 6,
  icon: '🆕'
}
```

2. **Aggiorna Backend**: Modifica enum degli stati nel modello ODL

### Personalizzare Colori

Modifica le classi CSS in `STATI_CONFIG` per adattare i colori al brand aziendale.

### Aggiungere Metriche

Estendi `ODLTimelineStats` per includere nuove metriche di performance.

## 📝 Note Tecniche

- **Performance**: I componenti utilizzano lazy loading e memoization per ottimizzare le prestazioni
- **Accessibilità**: Tooltip e indicatori sono compatibili con screen reader
- **Responsive**: Layout adattivo per mobile e desktop
- **Internazionalizzazione**: Formattazione date e numeri in italiano

## 🚀 Roadmap Future

- [ ] **Grafici Avanzati**: Integrazione con Recharts per visualizzazioni più complesse
- [ ] **Notifiche Real-time**: WebSocket per aggiornamenti istantanei
- [ ] **Filtri Avanzati**: Filtro per range temporali, responsabili, etc.
- [ ] **Export Avanzato**: PDF, Excel con grafici
- [ ] **Confronto ODL**: Visualizzazione comparativa di più ODL
- [ ] **Predizioni AI**: Stima tempi di completamento basata su ML 