# Test End-to-End - Batch Monitoring Page

## Obiettivo
Verificare il funzionamento del refactor della pagina Batch-Monitoring con MetricCard e filtering.

## Prerequisiti
- Frontend avviato su http://localhost:3000
- Backend mock data attivo nella pagina

## Test Cases

### Test 1: Visualizzazione MetricCard
**Obiettivo**: Verificare che tutte le MetricCard sono visibili e con valori corretti

**Passi**:
1. Naviga a `/dashboard/curing/batch-monitoring`
2. Attendi caricamento pagina (spinner deve scomparire)
3. Verifica presenza delle 6 MetricCard:
   - Totale Batch (valore: 3)
   - In Sospeso (valore: 1)
   - Confermati (valore: 1)
   - Caricati (valore: 0)
   - In Cura (valore: 1)
   - Completati (valore: 0)

**Risultato atteso**: ✅ Tutte le card sono visibili con valori mock corretti

---

### Test 2: Filtering con Click su MetricCard
**Obiettivo**: Verificare che cliccando su una MetricCard si applica il filtro status

**Passi**:
1. Click su MetricCard "In Sospeso"
2. Verifica URL: deve contenere `?status=sospeso`
3. Verifica visual feedback: MetricCard deve avere border blue (ring-2)
4. Verifica accordion: sezione "In Sospeso" deve essere visibile e evidenziata
5. Click su MetricCard "Totale Batch"
6. Verifica URL: deve essere `?status=all` o senza parametro status
7. Verifica reset: nessuna card evidenziata

**Risultato atteso**: ✅ Filtering funziona correttamente con URL e visual feedback

---

### Test 3: Accordion per Workflow Sections
**Obiettivo**: Verificare che le sezioni accordion funzionano correttamente

**Passi**:
1. Verifica sezioni visibili:
   - "In Sospeso" (1 batch)
   - "Confermati" (1 batch)
   - "Caricati" (0 batch)
   - "In Cura" (1 batch)
   - "Completati" (0 batch)
2. Click header sezione "In Sospeso" per chiudere
3. Verifica che contenuto scompare
4. Click di nuovo per riaprire
5. Verifica che contenuto riappare

**Risultato atteso**: ✅ Tutte le sezioni si aprono/chiudono correttamente

---

### Test 4: Contenuto Tabelle Accordion
**Obiettivo**: Verificare che i dati dei batch sono mostrati correttamente nelle tabelle

**Passi**:
1. Espandi sezione "In Sospeso"
2. Verifica presenza batch "Batch Test 1" con:
   - Stato: badge "In Sospeso" giallo
   - Autoclave: "Autoclave PANINI"
   - ODL/Nesting: "5 ODL • 2 Nesting"
3. Espandi sezione "In Cura"
4. Verifica colonne aggiuntive per batch in cura:
   - Progresso (barra progressione)
   - Temperatura (attuale/target)
   - Pressione (attuale/target)
   - Tempo Rimanente

**Risultato atteso**: ✅ Dati mostrati correttamente con colonne specifiche per stato

---

### Test 5: Empty State
**Obiettivo**: Verificare che sezioni vuote mostrano empty state corretto

**Passi**:
1. Espandi sezione "Caricati" (0 batch)
2. Verifica presenza messaggio: "Nessun batch in questa fase"
3. Verifica presenza icona Package opaca
4. Espandi sezione "Completati" (0 batch)
5. Verifica stesso comportamento

**Risultato atteso**: ✅ Empty state mostrato correttamente per sezioni vuote

---

### Test 6: Filtri Globali
**Obiettivo**: Verificare che i filtri aggiuntivi funzionano

**Passi**:
1. Inserisci "Test 1" nel campo Ricerca
2. Verifica che vengono mostrati solo batch che contengono "Test 1"
3. Seleziona "Autoclave 2" nel dropdown Autoclave
4. Verifica filtering per autoclave
5. Reset filtri

**Risultato atteso**: ✅ Tutti i filtri funzionano correttamente

---

### Test 7: Responsive Design
**Obiettivo**: Verificare che il layout si adatta a diversi viewport

**Passi**:
1. Ridimensiona browser a 375px larghezza (mobile)
2. Verifica che MetricCard si adattano in griglia 2 colonne
3. Verifica che descrizioni sezioni sono nascoste (`hidden md:block`)
4. Torna a desktop (>768px)
5. Verifica layout normale

**Risultato atteso**: ✅ Layout responsive funziona correttamente

---

## Note di Implementazione

### Modifiche Principali
- ✅ Sostituito `StatusCard` con `MetricCard`
- ✅ Aggiunto `data-testid` per testing automatizzato
- ✅ Implementato filtering con router.query.status
- ✅ Mantenutre accordion workflow sections
- ✅ Rimossi template alternativi (BatchEmptyState, etc.)

### Differenze MetricCard vs StatusCard
- `MetricCard` usa `variant` invece di `color`
- `MetricCard` ha `selected` prop per evidenziare stato attivo
- `MetricCard` supporta `data-testid` per testing
- Trend format migliorato con label "da ieri"

### Data TestIds Implementati
- `batch-monitoring-page`: Container principale
- `metric-card-{type}`: Ogni MetricCard (total, sospeso, confermato, etc.)
- `workflow-section-{id}`: Ogni sezione accordion
- `workflow-header-{id}`: Header cliccabile sezioni
- `workflow-content-{id}`: Contenuto collapsible sezioni
- `section-badge`: Badge contatore batch in sezioni
- `empty-state`: Messaggio quando sezione è vuota

## Comandi per Testing

```bash
# Build frontend (deve completare senza errori)
cd frontend && npm run build

# Avvia dev server
cd frontend && npm run dev

# Se disponibile Playwright in futuro:
# npx playwright test batch-monitoring.spec.ts
``` 