# 🚀 NESTING PREVIEW SEMPLIFICATO - CarbonPilot v1.4.10

**Documentazione completa del nuovo flusso di nesting con preview interattiva**

---

## 📋 Panoramica

Il nuovo flusso di **Nesting Preview Semplificato** sostituisce l'interfaccia complessa precedente con un workflow lineare e user-friendly che massimizza l'usabilità e riduce gli errori operativi.

### 🎯 **Obiettivi Raggiunti**
- ✅ **Flusso lineare**: 6 step chiari e sequenziali
- ✅ **Preview in tempo reale**: Visualizzazione istantanea del layout
- ✅ **Parametri configurabili**: Slider intuitivi per ottimizzazione
- ✅ **KPI visibili**: Metriche chiare per valutazione efficienza
- ✅ **Error handling robusto**: Gestione errori user-friendly
- ✅ **No drag-and-drop**: Semplificazione basata su click/rigenerazione

---

## 🗺️ Flusso Utente

### **STEP 1: Accesso alla Preview**
```
Dashboard → Curing → Nesting → "Preview Semplificata"
URL: /dashboard/curing/nesting/preview
```

### **STEP 2: Configurazione Parametri**
- **Selezione Autoclave**: Dropdown con autoclavi disponibili + info dimensioni
- **Selezione ODL**: Lista interattiva ODL in stato "ATTESA CURA"
- **Parametri Algoritmo**: 3 slider per personalizzazione

### **STEP 3: Generazione Anteprima**
- **Trigger**: Bottone "Genera Anteprima" 
- **API Call**: `POST /api/v1/batch_nesting/solve`
- **Feedback**: Loading spinner + progress indicator

### **STEP 4: Visualizzazione Layout**
- **Canvas Interattivo**: NestingCanvas con tool posizionati
- **KPI Dashboard**: 4 metriche chiave in cards
- **ODL Esclusi**: Lista dettagliata con motivi esclusione

### **STEP 5: Valutazione e Decisione**
- **Opzioni**: Rigenera (↻) | Annulla (✖) | Conferma (✓)
- **Scorciatoie**: `+`/`-` per zoom, `R` per rigenerare

### **STEP 6: Conferma Batch**
- **Creazione**: Batch definitivo via `POST /api/v1/batch_nesting/genera`
- **Redirect**: Pagina risultato batch `/result/{batch_id}`

---

## 🏗️ Architettura Tecnica

### **Frontend Structure**
```
frontend/src/app/dashboard/curing/nesting/
├── page.tsx                    # Pagina principale con link "Preview Semplificata"
├── preview/
│   └── page.tsx               # ✅ NUOVO: Preview semplificato
└── result/[batch_id]/
    ├── NestingCanvas.tsx      # 🔧 AGGIORNATO: Compatibilità nuova API
    └── page.tsx               # Pagina risultati batch
```

### **API Endpoints**
| Endpoint | Metodo | Scopo | Payload |
|----------|--------|-------|---------|
| `/api/v1/batch_nesting/solve` | POST | Preview nesting | `{odl_ids, autoclave_id, parametri}` |
| `/api/v1/batch_nesting/genera` | POST | Crea batch definitivo | `{odl_ids, autoclave_ids, parametri, nome}` |
| `/api/v1/odl?status=ATTESA%20CURA` | GET | ODL disponibili | Query params |
| `/api/v1/autoclavi?stato=DISPONIBILE` | GET | Autoclavi attive | Query params |

### **Data Flow**
```mermaid
graph TD
    A[User accede a /preview] --> B[Carica ODL + Autoclavi]
    B --> C[Configura parametri]
    C --> D[Seleziona ODL + Autoclave]
    D --> E[Clicca "Genera Anteprima"]
    E --> F[API /solve con parametri]
    F --> G[Visualizza layout + KPI]
    G --> H{Soddisfatto?}
    H -->|No| I[Modifica parametri] --> E
    H -->|Sì| J[Clicca "Conferma Batch"]
    J --> K[API /genera batch]
    K --> L[Redirect a /result/batch_id]
```

---

## ⚙️ Parametri Configurabili

### **Padding tra Tool**
- **Range**: 5-50mm
- **Default**: 20mm  
- **Impatto**: Spazio sicurezza attorno ai tool. Valori bassi = più ODL, rischio maggiore

### **Distanza dai Bordi**
- **Range**: 5-30mm
- **Default**: 15mm
- **Impatto**: Margine dal bordo autoclave. Valori bassi = maggiore utilizzo area

### **Capacità Linee Vuoto**
- **Range**: 1-50 linee
- **Default**: 10 linee
- **Impatto**: Limite valvole disponibili. Determina esclusione ODL ad alto consumo

---

## 📊 KPI Dashboard

### **Area Occupata %**
```typescript
area_pct = (area_utilizzata / area_totale_autoclave) × 100
```
- **Target**: >70% per efficienza ottimale
- **Colore**: Blu, icona Gauge

### **Linee Vuoto Utilizzate**
```typescript
format: "lines_used / vacuum_lines_capacity"
```
- **Target**: Utilizzo bilanciato senza saturazione
- **Colore**: Verde, icona Info

### **ODL Inclusi**
```typescript
positioned_count = tools_posizionati.length
```
- **Target**: Massimizzare numero ODL inclusi
- **Colore**: Viola, icona Users  

### **Peso Totale**
```typescript
total_weight = sum(tool.weight for tool in positioned_tools)
```
- **Target**: <90% del limite autoclave
- **Colore**: Arancione, icona Package

---

## 🔧 Algoritmi di Nesting

### **CP-SAT Principale (OR-Tools)**
- **Timeout Adaptivo**: `min(60s, 2s × numero_pezzi)`
- **Vincoli**: Non sovrapposizione 2D, limiti peso, valvole
- **Obiettivo**: Massimizza area utilizzata + numero ODL
- **Status**: `CP-SAT_OPTIMAL` | `CP-SAT_FEASIBLE`

### **Fallback Greedy**
- **Trigger**: Se CP-SAT fallisce o timeout
- **Algoritmo**: First-fit decreasing sull'asse lungo
- **Performance**: O(n²) deterministico
- **Status**: `FALLBACK_GREEDY`

### **Pre-filtraggio Intelligente**
- **Esclusioni automatiche**:
  - Tool troppo grandi per autoclave
  - Peso singolo > limite autoclave  
  - Linee vuoto richieste > capacità
- **Status**: `NO_VALID_TOOLS` se tutti esclusi

---

## 🎨 Design System

### **Layout Responsive**
```css
.main-grid {
  display: grid;
  grid-template-columns: 1fr 3fr;  /* Parametri : Canvas */
  gap: 1.5rem;
}

@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;     /* Stack verticale mobile */
  }
}
```

### **Color Palette**
- **Primario**: Blue (#3B82F6) - Pulsanti principali, canvas
- **Successo**: Green (#10B981) - Metriche positive, conferma
- **Warning**: Yellow (#F59E0B) - ODL esclusi, avvisi
- **Errore**: Red (#EF4444) - Errori critici, fallimenti
- **Neutro**: Gray (#6B7280) - Testo secondario, bordi

### **Typography Scale**
- **H1**: 30px/36px - Titolo pagina
- **H2**: 24px/32px - Titoli sezioni  
- **H3**: 20px/28px - Titoli card
- **Body**: 16px/24px - Testo principale
- **Small**: 14px/20px - Etichette, metadati
- **XSmall**: 12px/16px - Tooltips, info aggiuntive

---

## 🧪 Testing e Validazione

### **Scenari di Test**

#### **T1: Happy Path**
1. ✅ Caricamento dati iniziali
2. ✅ Selezione autoclave + 5 ODL
3. ✅ Configurazione parametri default
4. ✅ Generazione preview successo
5. ✅ Visualizzazione layout corretto
6. ✅ KPI accurati
7. ✅ Conferma batch e redirect

#### **T2: Edge Cases**
1. ✅ Nessun ODL disponibile
2. ✅ Nessuna autoclave disponibile  
3. ✅ Tutti ODL troppo grandi
4. ✅ Timeout algoritmo CP-SAT
5. ✅ Fallback greedy attivato
6. ✅ Errore API durante conferma

#### **T3: Error Handling**
1. ✅ Rete disconnessa
2. ✅ Server backend down
3. ✅ Autoclave passa a GUASTA durante selezione
4. ✅ ODL cambia stato durante processo
5. ✅ Parametri fuori range
6. ✅ Session expired

#### **T4: Performance**
1. ✅ 50+ ODL disponibili (scroll performance)
2. ✅ Layout con 20+ tool posizionati
3. ✅ Rigenerazione rapida (<3s)
4. ✅ Memory usage su dispositivi low-end
5. ✅ Network throttling (3G simulato)

### **Metriche Performance Target**
- **Time to Interactive**: <2s
- **First Contentful Paint**: <1s  
- **Preview Generation**: <10s (95th percentile)
- **Memory Usage**: <100MB
- **Bundle Size**: <500KB gzipped

---

## 🔐 Sicurezza e Validazioni

### **Input Validation**
```typescript
// Parametri range validation
padding_mm: [5, 50]
min_distance_mm: [5, 30]  
vacuum_lines_capacity: [1, 50]

// IDs validation
odl_ids: number[] (min: 1, max: 100)
autoclave_id: number (positive integer)
```

### **Authorization Checks**
- **Ruolo minimo**: `Curing` per accesso preview
- **Operazioni**: Solo utenti `Curing`+ possono confermare batch
- **Audit Trail**: Tutte le azioni loggate con user_id

### **Data Sanitization**
- **XSS Protection**: Tutti i testi user-input escapati
- **SQL Injection**: Parametrized queries obbligatorie
- **CSRF**: Token validation su POST requests

---

## 📈 Monitoring e Analytics

### **Metriche Operative**
- **Preview Success Rate**: % generazioni andate a buon fine
- **Algorithm Distribution**: CP-SAT vs Fallback usage
- **User Completion Rate**: % utenti che completano il flusso
- **Average Session Time**: Tempo medio sulla pagina
- **Error Frequency**: Tipologie errori più comuni

### **Performance Metrics**
- **API Response Times**: p50, p95, p99 per endpoint `/solve`
- **Memory Usage**: Peak memory durante operazioni pesanti
- **CPU Usage**: Utilizzo durante algoritmi intensivi
- **Network Transfer**: Dimensione payload request/response

### **Business Metrics**
- **Batch Confirmation Rate**: % preview confermate vs annullate
- **Parameter Usage**: Distribuzione valori parametri scelti
- **Efficiency Achieved**: Media % area utilizzata nei batch
- **User Adoption**: Utilizzo nuovo flusso vs vecchio

---

## 🔮 Roadmap Future

### **v1.4.11 - Interattività Avanzata**
- [ ] **Drag & Drop Canvas**: Modifica manuale posizioni tool
- [ ] **Undo/Redo Stack**: Cronologia delle modifiche
- [ ] **Snap-to-Grid**: Allineamento automatico preciso
- [ ] **Collision Detection**: Preview real-time sovrapposizioni

### **v1.4.12 - Ottimizzazioni**
- [ ] **Configurazioni Salvate**: Template parametri personalizzati
- [ ] **Batch Templates**: Pattern ricorrenti ottimizzati
- [ ] **Multi-Plane Support**: Utilizzo piano secondario
- [ ] **Weight Distribution**: Bilanciamento carico ottimale

### **v1.4.13 - Collaboration**
- [ ] **Real-time Sync**: Multi-utente simultaneo
- [ ] **Comments System**: Note collaborative su layout
- [ ] **Approval Workflow**: Processo approvazione multi-step
- [ ] **Version Control**: Versioning layout e rollback

### **v1.5.0 - AI Enhancement**
- [ ] **ML Recommendations**: Suggerimenti parametri basati su storia
- [ ] **Predictive Analytics**: Forecast efficiency pre-generazione
- [ ] **Auto-Optimization**: Tuning automatico parametri
- [ ] **Anomaly Detection**: Identificazione layout problematici

---

## 📚 Riferimenti

- **Documentazione API**: `/docs/api/v1/batch_nesting.md`
- **Design System**: `/docs/design-system.md` 
- **Testing Guide**: `/docs/testing/nesting-flow.md`
- **Deployment**: `/docs/deployment/frontend-build.md`
- **Troubleshooting**: `/docs/support/nesting-issues.md`

---

**Documento generato il**: 2024-12-19  
**Versione**: v1.4.10  
**Autore**: Team CarbonPilot  
**Prossimo review**: 2025-01-19 