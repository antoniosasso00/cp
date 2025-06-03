# 🧪 Edge Cases Test Report - CarbonPilot v1.4.17-DEMO

**📋 Iter #2 – v1.4.17**  
**Modifiche implementate:**
- ✅ Endpoint `/api/v1/nesting/solve` attivo (forward a batch_nesting)
- ✅ Nuova formula efficienza: `0.5×area + 0.3×vacuum + 0.2×placement_success`  
- ✅ Fix gestione Scenario A: fallimento atteso per pezzo gigante (non più critical error)
- ✅ Scripts edge-test aggiornati con nuovo parsing campi risposta

**Timestamp:** 2025-06-02 22:31:02  
**Test Harness:** EdgeTestHarness v1.0  
**Scenari Testati:** 5

---

## 📊 Riepilogo Risultati

| Scenario | Descrizione | Successo | Efficienza % | Tempo (ms) | Fallback | Pezzi Pos. | Pezzi Escl. |
|----------|-------------|----------|--------------|------------|----------|------------|-------------|
| A | Pezzo Gigante | ❌ | 0.0 | 4 | 🚀 | 0 | 1 |
| B | Overflow Vacuum | ✅ | 59.2 | 9 | 🔄 | 5 | 1 |
| C | Stress Performance | ✅ | 74.4 | 142 | 🔄 | 12 | 38 |
| D | Bassa Efficienza | ✅ | 78.2 | 116 | 🔄 | 7 | 3 |
| E | Happy Path | ✅ | 58.2 | 51 | 🔄 | 7 | 8 |

---

## 🔴 Problemi Critici

- **Scenario B**: Efficienza molto bassa (59.2%)
- **Scenario E**: Efficienza molto bassa (58.2%)

---

## 📋 Comportamenti Attesi vs Reali

**Scenario A**: ✅ ATTESO - Fallimento corretto  
└─ *Pezzo gigante - DEVE fallire (oversize)*  

**Scenario B**: ✅ ATTESO - Successo  
└─ *Overflow vacuum - può fallire o usare fallback*  

**Scenario C**: ✅ ATTESO - Successo corretto  
└─ *Stress performance - deve completare (anche con timeout)*  

**Scenario D**: ✅ ATTESO - Successo corretto  
└─ *Bassa efficienza - deve completare con efficienza < 50%*  

**Scenario E**: ✅ ATTESO - Successo corretto  
└─ *Happy path - DEVE sempre funzionare*  


---

## 🌐 Test Frontend

**Status:** ❌ ERRORE  
**Tempo Caricamento:** 0ms  
**Canvas Visibile:** ❌  

**Errori Console JavaScript:**
- `Playwright non installato`

---

## 📋 Dettagli Scenari

### Scenario A: Pezzo Gigante

**Risultato:** ❌ Fallimento  
**Algoritmo:** NO_VALID_TOOLS  
**Tempo Solver:** 4ms  
**Efficienza:** 0.0%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 0.0%  
**Pezzi Totali:** 1  
**Pezzi Posizionati:** 0  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- Dimensioni eccessive

### Scenario B: Overflow Linee Vuoto

**Risultato:** ✅ Successo  
**Algoritmo:** FALLBACK_GREEDY  
**Tempo Solver:** 9ms  
**Efficienza:** 59.2%  
**Utilizzo Area:** 25.0%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 6  
**Pezzi Posizionati:** 5  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- placement_failed

### Scenario C: Stress Performance

**Risultato:** ✅ Successo  
**Algoritmo:** FALLBACK_GREEDY  
**Tempo Solver:** 142ms  
**Efficienza:** 74.4%  
**Utilizzo Area:** 79.2%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 50  
**Pezzi Posizionati:** 12  
**Pezzi Esclusi:** 38  

**Motivi Esclusione:**
- placement_failed

### Scenario D: Bassa Efficienza

**Risultato:** ✅ Successo  
**Algoritmo:** FALLBACK_GREEDY  
**Tempo Solver:** 116ms  
**Efficienza:** 78.2%  
**Utilizzo Area:** 86.4%  
**Utilizzo Vacuum:** 70.0%  
**Pezzi Totali:** 10  
**Pezzi Posizionati:** 7  
**Pezzi Esclusi:** 3  

**Motivi Esclusione:**
- placement_failed

### Scenario E: Happy Path

**Risultato:** ✅ Successo  
**Algoritmo:** FALLBACK_GREEDY  
**Tempo Solver:** 51ms  
**Efficienza:** 58.2%  
**Utilizzo Area:** 37.7%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 15  
**Pezzi Posizionati:** 7  
**Pezzi Esclusi:** 8  

**Motivi Esclusione:**
- placement_failed

---

## 💡 Raccomandazioni Quick-Fix

- ⚠️  **Scenario B**: Overflow vacuum dovrebbe fallire o usare fallback. Verificare vincoli linee vuoto.
- 🎯 **Scenario D**: Efficienza troppo alta con padding elevato. Verificare calcolo efficienza.
- 🌐 **Frontend**: Pagina nesting non carica. Verificare connessione backend e build frontend.
