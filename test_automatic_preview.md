# 🧪 Test Plan - Aggiornamento Automatico Preview Nesting

## 📋 Scenari di Test

### ✅ Test 1: Aggiornamento per Cambio Parametri

**Passi:**
1. Apri `/dashboard/curing/nesting/preview`
2. Seleziona un'autoclave dal dropdown
3. Seleziona alcuni ODL dalla lista
4. **Modifica il parametro "Padding tra tool"** usando lo slider
5. **Aspetta 1 secondo**

**Risultato Atteso:**
- Appare banner blu "Aggiornamento automatico in corso..."
- Dopo ~1-3 secondi la preview si aggiorna con nuovo layout
- Banner scompare
- Nessun toast di notifica
- Console log: `🔄 Auto-aggiornamento preview per cambio parametri/selezioni`

---

### ✅ Test 2: Aggiornamento per Cambio Distanza Bordi

**Passi:**
1. Con preview già visualizzata dal Test 1
2. **Modifica "Distanza dai bordi"** usando lo slider
3. **Cambia più volte rapidamente** (test debounce)
4. **Aspetta 1 secondo dall'ultima modifica**

**Risultato Atteso:**
- Solo l'ultimo cambiamento viene processato (debounce)
- Banner "Aggiornamento automatico..." appare
- Preview si aggiorna una volta sola
- Nessun toast multipli

---

### ✅ Test 3: Aggiornamento per Selezione ODL

**Passi:**
1. Con preview già visualizzata
2. **Deseleziona alcuni ODL** cliccando su di essi
3. **Aspetta 1 secondo**
4. **Clicca "Tutti"** per selezionare tutti gli ODL
5. **Aspetta 1 secondo**

**Risultato Atteso:**
- Ad ogni modifica: banner + aggiornamento automatico
- Layout si adatta al numero di ODL selezionati
- Metriche KPI si aggiornano correttamente

---

### ✅ Test 4: Aggiornamento per Cambio Autoclave

**Passi:**
1. Con preview già visualizzata
2. **Cambia autoclave** dal dropdown
3. **Aspetta 1 secondo**

**Risultato Atteso:**
- Preview si rigenera per la nuova autoclave
- Dimensioni canvas cambiano
- Posizionamento tool si adatta alle nuove dimensioni

---

### ✅ Test 5: Reset Automatico per Selezioni Incomplete

**Passi:**
1. Con preview già visualizzata
2. **Deseleziona tutti gli ODL** (clicca "Nessuno")
3. **Aspetta 1 secondo**

**Risultato Atteso:**
- Preview scompare automaticamente
- Appare messaggio "Seleziona un'autoclave e degli ODL..."
- Nessun banner di aggiornamento
- Nessun errore console

---

### ✅ Test 6: Aggiornamento Manuale Sempre Disponibile

**Passi:**
1. Con preview già visualizzata
2. **Clicca "Aggiorna Manualmente"**

**Risultato Atteso:**
- Preview si rigenera immediatamente
- **Toast di conferma appare:** "✅ Anteprima Generata"
- Pulsante torna a "Aggiorna Manualmente"

---

### ✅ Test 7: Gestione Errori Automatici vs Manuali

**Passi:**
1. **Disconnetti backend** temporaneamente
2. **Modifica un parametro** (trigger automatico)
3. **Aspetta 1 secondo**
4. **Riconnetti backend**
5. **Clicca "Aggiorna Manualmente"**

**Risultato Atteso:**
- **Errore automatico:** Nessun toast, solo log console
- **Errore manuale:** Toast rosso di errore visibile

---

### ✅ Test 8: Prevenzione Auto-Update Durante Generazione

**Passi:**
1. **Clicca "Aggiorna Manualmente"** 
2. **Subito dopo, modifica un parametro** (prima che la generazione finisca)
3. **Aspetta**

**Risultato Atteso:**
- Primo aggiornamento completa normalmente
- Secondo aggiornamento **non si attiva** durante il primo
- Dopo che il primo finisce, se parametri sono cambiati, parte il secondo

---

### ✅ Test 9: UI Indicatori Corretti

**Passi:**
1. **Osserva il pulsante** in vari stati
2. **Modifica parametri** per attivare auto-update

**Risultato Atteso:**
- **Normale:** "Aggiorna Manualmente" (blu)
- **Auto-Update:** "Aggiornamento Automatico" + icona Clock (outline)
- **Generazione:** "Generazione in corso..." + spinner (blu)

---

### ✅ Test 10: Performance e Responsività

**Passi:**
1. **Trascina velocemente** lo slider del padding avanti e indietro
2. **Continua per ~5 secondi**
3. **Ferma e aspetta 1 secondo**

**Risultato Atteso:**
- Nessun lag nell'UI durante il trascinamento
- Solo 1 chiamata API dopo l'ultimo trascinamento
- Browser rimane reattivo

---

## 🔧 Setup Test Environment

### Prerequisiti
```bash
# Backend attivo
cd backend && uvicorn main:app --reload

# Frontend attivo  
cd frontend && npm run dev

# Browser con DevTools aperto per monitorare:
# - Console logs
# - Network requests
# - Performance
```

### Dati di Test Necessari
- **Almeno 1 autoclave** con stato "DISPONIBILE"
- **Almeno 3-5 ODL** con stato "Preparazione"
- **Tools associati** con dimensioni realistiche

### Metriche da Monitorare
- **Tempo risposta API:** < 3 secondi per nesting semplice
- **Debounce effectiveness:** 1 sola chiamata API per multiple modifiche rapide
- **Memory usage:** Nessun memory leak in tab browser
- **Error rate:** 0% errori per scenari validi

---

## 🚨 Segnalazione Bug

Se riscontri comportamenti diversi da quelli attesi:

1. **Apri DevTools → Console** e copia logs
2. **Apri DevTools → Network** e verifica chiamate API
3. **Documenta:** Browser, OS, tempo riproduzione
4. **Screenshot/Video** del comportamento anomalo

### Template Bug Report
```markdown
**Test Fallito:** [Nome Test]
**Browser:** [Chrome 119, Firefox 120, etc.]
**Comportamento Atteso:** [Descrizione]
**Comportamento Attuale:** [Descrizione]
**Console Logs:** [Copia logs]
**Network Logs:** [Status codes API calls]
**Screenshot:** [Allega se pertinente]
```

---

*Creato per versione v1.4.13 - Aggiornamento Automatico Preview* 