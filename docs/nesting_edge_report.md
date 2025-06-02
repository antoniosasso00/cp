# 🧪 Edge Cases Test Report - CarbonPilot v1.4.13-DEMO

**Timestamp:** 2025-06-02 22:06:20  
**Test Harness:** EdgeTestHarness v1.0  
**Scenari Testati:** 5

---

## 📊 Riepilogo Risultati

| Scenario | Descrizione | Successo | Efficienza % | Tempo (ms) | Fallback | Pezzi Pos. | Pezzi Escl. |
|----------|-------------|----------|--------------|------------|----------|------------|-------------|
| A | Pezzo Gigante | ❌ | 0.0 | 9 | 🚀 | 0 | 1 |
| B | Overflow Vacuum | ✅ | 59.2 | 9 | 🔄 | 5 | 1 |
| C | Stress Performance | ✅ | 74.4 | 139 | 🔄 | 12 | 1 |
| D | Bassa Efficienza | ✅ | 78.2 | 75 | 🔄 | 7 | 1 |
| E | Happy Path | ✅ | 58.2 | 43 | 🔄 | 7 | 1 |

---

## 🔴 Problemi Critici

- **Scenario A**: Solver failure completo - UNKNOWN
- **Scenario B**: Efficienza molto bassa (59.2%)
- **Scenario E**: Efficienza molto bassa (58.2%)

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
**Algoritmo:** UNKNOWN  
**Tempo Solver:** 9ms  
**Efficienza:** 0.0%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 0.0%  
**Pezzi Totali:** 1  
**Pezzi Posizionati:** 0  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- 1

### Scenario B: Overflow Linee Vuoto

**Risultato:** ✅ Successo  
**Algoritmo:** UNKNOWN  
**Tempo Solver:** 9ms  
**Efficienza:** 59.2%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 6  
**Pezzi Posizionati:** 5  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- 1

### Scenario C: Stress Performance

**Risultato:** ✅ Successo  
**Algoritmo:** UNKNOWN  
**Tempo Solver:** 139ms  
**Efficienza:** 74.4%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 50  
**Pezzi Posizionati:** 12  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- 38

### Scenario D: Bassa Efficienza

**Risultato:** ✅ Successo  
**Algoritmo:** UNKNOWN  
**Tempo Solver:** 75ms  
**Efficienza:** 78.2%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 70.0%  
**Pezzi Totali:** 10  
**Pezzi Posizionati:** 7  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- 3

### Scenario E: Happy Path

**Risultato:** ✅ Successo  
**Algoritmo:** UNKNOWN  
**Tempo Solver:** 43ms  
**Efficienza:** 58.2%  
**Utilizzo Area:** 0.0%  
**Utilizzo Vacuum:** 100.0%  
**Pezzi Totali:** 15  
**Pezzi Posizionati:** 7  
**Pezzi Esclusi:** 1  

**Motivi Esclusione:**
- 8

---

## 💡 Raccomandazioni Quick-Fix

- ⚠️  **Scenario B**: Overflow vacuum dovrebbe fallire o usare fallback. Verificare vincoli linee vuoto.
- 🎯 **Scenario D**: Efficienza troppo alta con padding elevato. Verificare calcolo efficienza.
- 🌐 **Frontend**: Pagina nesting non carica. Verificare connessione backend e build frontend.
