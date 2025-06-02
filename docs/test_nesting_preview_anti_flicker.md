# 🧪 Test Plan - Preview Nesting Anti-Sfarfallio v2.0

## 📋 Obiettivo Test
Verificare che i miglioramenti anti-sfarfallio della preview nesting funzionino correttamente e che l'esperienza utente sia fluida.

## 🎯 Scenari di Test

### 1. 🔄 Test Debounce Ottimizzato

#### Scenario: Trascinamento Slider Parametri
1. **Setup:** Vai a `/dashboard/curing/nesting/preview`
2. **Azione:** Seleziona autoclave e alcuni ODL
3. **Test:** Trascina rapidamente lo slider "Padding tra tool"
4. **Aspettativa:** 
   - ✅ Nessun aggiornamento durante il trascinamento
   - ✅ Aggiornamento solo dopo 2.5s dall'ultimo movimento
   - ✅ Preview precedente rimane visibile durante l'attesa

#### Scenario: Modifiche Rapide Multiple
1. **Azione:** Cambia rapidamente padding, poi distanza bordi, poi selezione ODL
2. **Aspettativa:**
   - ✅ Solo un aggiornamento finale dopo 2.5s dall'ultima modifica
   - ✅ Timeout precedenti cancellati automaticamente

### 2. 📱 Test Stale-While-Revalidate

#### Scenario: Aggiornamento Automatico
1. **Setup:** Preview già generata e visibile
2. **Azione:** Modifica un parametro (es. padding da 20mm a 30mm)
3. **Aspettativa:**
   - ✅ Preview precedente rimane visibile
   - ✅ Indicatore sottile "Aggiornamento in corso..."
   - ✅ Transizione fluida alla nuova preview
   - ❌ NO sfarfallio o schermo bianco

#### Scenario: Aggiornamento Manuale
1. **Azione:** Clicca "Aggiorna Ora" manualmente
2. **Aspettativa:**
   - ✅ Preview viene resettata (comportamento normale)
   - ✅ Spinner di loading visibile
   - ✅ Toast di conferma al completamento

### 3. 🎛️ Test Toggle Controllo Utente

#### Scenario: Disabilitazione Auto-Update
1. **Azione:** Disattiva il toggle "Aggiornamento Automatico"
2. **Test:** Modifica parametri
3. **Aspettativa:**
   - ✅ Nessun aggiornamento automatico
   - ✅ Pulsante diventa "Genera Anteprima"
   - ✅ Messaggio cambia in "usa il pulsante per generare manualmente"

#### Scenario: Riabilitazione Auto-Update
1. **Azione:** Riattiva il toggle
2. **Test:** Modifica un parametro
3. **Aspettativa:**
   - ✅ Auto-update riprende dopo 2.5s
   - ✅ Pulsante diventa "Aggiorna Ora"

### 4. 🎨 Test Indicatori Visivi

#### Scenario: Stati Pulsante Dinamico
1. **Toggle OFF:** Pulsante = "Genera Anteprima" (default style)
2. **Toggle ON + Idle:** Pulsante = "Aggiorna Ora" (default style)
3. **Toggle ON + Auto-updating:** Pulsante = "Auto-Update Attivo" (outline style)
4. **Loading:** Pulsante = "Generazione in corso..." (spinner)

#### Scenario: Indicatore Sottile
1. **Aspettativa:** Durante auto-update, banner sottile blu con bordo sinistro
2. **Contenuto:** Spinner piccolo + "Aggiornamento in corso..."
3. **Posizione:** Sopra il pulsante, meno invasivo del banner precedente

### 5. ⚡ Test Performance

#### Scenario: Conteggio Chiamate API
1. **Setup:** Apri DevTools → Network tab
2. **Test:** Trascina slider per 10 secondi continuamente
3. **Aspettativa:** 
   - ✅ Massimo 1-2 chiamate a `/api/v1/batch_nesting/solve`
   - ✅ Non 10+ chiamate come nella versione precedente

#### Scenario: Smoothness Visiva
1. **Test:** Modifica parametri mentre osservi la preview
2. **Aspettativa:**
   - ✅ Nessun "flash" o scomparsa improvvisa
   - ✅ Transizioni fluide
   - ✅ Feedback continuo per l'utente

## 🚨 Regressioni da Verificare

### ❌ Comportamenti da NON vedere
1. **Sfarfallio:** Preview che scompare e riappare
2. **Aggiornamenti Aggressivi:** Chiamate API ogni 1s durante drag
3. **Perdita Stato:** Preview che si resetta durante auto-update
4. **Banner Invasivo:** Card grande che copre troppo spazio
5. **Toggle Ignorato:** Auto-update che continua anche se disabilitato

### ✅ Comportamenti da Mantenere
1. **Funzionalità Core:** Nesting algorithm funziona correttamente
2. **Errori Gestiti:** Toast errori per aggiornamenti manuali
3. **Validazione:** Controlli su selezioni incomplete
4. **Metriche:** KPI e statistiche visualizzate correttamente

## 📊 Metriche di Successo

### Quantitative
- **API Calls:** < 2 chiamate per sessione di configurazione tipica
- **Debounce Time:** 2.5s misurabili tra modifica e chiamata
- **UI Updates:** Smooth 60fps, no frame drops

### Qualitative  
- **User Experience:** Fluida, senza interruzioni visive
- **Cognitive Load:** Ridotto, controlli intuitivi
- **Feedback:** Chiaro ma non invasivo

## 🔧 Debug Tools

### Console Logs da Monitorare
```javascript
// Dovrebbe apparire solo dopo 2.5s dall'ultima modifica
'🔄 Auto-aggiornamento preview per cambio parametri/selezioni'

// Stato toggle
'🎛️ Auto-update enabled: true/false'

// Pattern stale-while-revalidate
'📱 Maintaining previous preview during automatic update'
```

### DevTools Checks
1. **Network:** Verifica frequenza chiamate API
2. **Performance:** Monitora frame rate durante aggiornamenti
3. **Console:** Controlla log di debug per timing

---

*Test Plan v2.0 - Verifica miglioramenti anti-sfarfallio completata* 