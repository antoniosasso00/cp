# Test Interfaccia Nesting Manuale - Guida Completa

## 📋 Panoramica

Questa guida fornisce istruzioni dettagliate per testare l'interfaccia di selezione ODL per nesting manuale, inclusi tutti i casi di test per validazione, gestione errori e debug avanzato.

## 🚀 Setup Iniziale

### 1. Avvio Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Avvio Frontend
```bash
cd frontend
npm run dev
```

### 3. Creazione Dati di Test
```bash
cd backend
python seed_test_data_simple.py
```

Il script verificherà automaticamente:
- ✅ Backend raggiungibile
- ✅ Parti e tool disponibili
- ✅ Creazione ODL di test se necessari

## 🎯 Accesso all'Interfaccia

1. **Vai su**: http://localhost:3000
2. **Seleziona ruolo**: RESPONSABILE o ADMIN
3. **Naviga a**: Dashboard → Nesting
4. **Clicca**: "Nesting Manuale" nella sezione azioni

## 🧪 Test Cases

### Test 1: Caricamento Iniziale
**Obiettivo**: Verificare caricamento corretto ODL in attesa

**Passi**:
1. Aprire l'interfaccia di nesting manuale
2. Verificare che appaia il loading spinner
3. Attendere caricamento dati

**Risultato Atteso**:
- ✅ Loading spinner visibile durante caricamento
- ✅ Tabella ODL popolata con dati
- ✅ Conteggio ODL corretto nell'header
- ✅ Nessun errore in console

### Test 2: Selezione ODL Singolo
**Obiettivo**: Testare selezione di un singolo ODL

**Passi**:
1. Cliccare checkbox di un ODL in stato "Attesa Cura"
2. Verificare aggiornamento statistiche
3. Controllare abilitazione pulsante "Crea Nesting"

**Risultato Atteso**:
- ✅ Checkbox selezionato
- ✅ Riga evidenziata
- ✅ Alert statistiche mostra "1 ODL selezionato"
- ✅ Pulsante "Crea Nesting (1)" abilitato

### Test 3: Selezione Multipla
**Obiettivo**: Testare selezione di più ODL

**Passi**:
1. Selezionare 3-5 ODL diversi
2. Verificare aggiornamento conteggi
3. Usare "Seleziona tutti" e "Deseleziona tutti"

**Risultato Atteso**:
- ✅ Tutti gli ODL selezionati evidenziati
- ✅ Conteggio corretto in statistiche
- ✅ Totale valvole calcolato correttamente
- ✅ Checkbox "Seleziona tutti" funzionante

### Test 4: Filtri e Ricerca
**Obiettivo**: Testare funzionalità di filtro

**Passi**:
1. Inserire testo nella barra di ricerca (es. "CPX")
2. Selezionare filtro priorità specifica
3. Verificare aggiornamento risultati
4. Cancellare filtri

**Risultato Atteso**:
- ✅ Risultati filtrati correttamente
- ✅ Conteggio "ODL Filtrati" aggiornato
- ✅ Selezioni mantenute durante filtro
- ✅ Reset filtri funzionante

### Test 5: Validazione Lato Client
**Obiettivo**: Testare controlli di validazione

**Passi**:
1. Tentare creazione nesting senza selezioni
2. Selezionare troppi ODL (>50 se possibile)
3. Verificare messaggi di errore

**Risultato Atteso**:
- ✅ Pulsante disabilitato senza selezioni
- ✅ Alert di validazione per errori
- ✅ Messaggi di errore specifici e chiari
- ✅ Suggerimenti per risoluzione

### Test 6: Creazione Nesting Valido
**Obiettivo**: Testare creazione nesting con successo

**Passi**:
1. Selezionare 2-3 ODL validi
2. Aggiungere note opzionali
3. Cliccare "Crea Nesting"
4. Confermare nel dialog

**Risultato Atteso**:
- ✅ Dialog di conferma con dettagli corretti
- ✅ Loading durante creazione
- ✅ Toast di successo
- ✅ Lista ODL aggiornata automaticamente
- ✅ Form resettato

### Test 7: Gestione Errori API
**Obiettivo**: Testare gestione errori server

**Passi per simulare errori**:
1. **Errore 422**: Selezionare ODL già assegnati (se disponibili)
2. **Errore connessione**: Spegnere backend durante operazione
3. **Errore 500**: Forzare errore server (se possibile)

**Risultato Atteso**:
- ✅ Messaggi di errore specifici per ogni tipo
- ✅ Suggerimenti per risoluzione
- ✅ Nessun crash dell'interfaccia
- ✅ Possibilità di riprovare

### Test 8: Modalità Debug
**Obiettivo**: Testare funzionalità debug avanzate

**Passi**:
1. Attivare modalità debug (pulsante "Debug OFF" → "Debug ON")
2. Verificare pannello informazioni debug
3. Eseguire operazioni e controllare cronologia errori
4. Verificare logging in console browser

**Risultato Atteso**:
- ✅ Pannello debug visibile
- ✅ Statistiche corrette (ODL totali, filtrati, selezionati)
- ✅ Cronologia errori funzionante
- ✅ Dettagli richieste in console
- ✅ Informazioni tecniche dettagliate

### Test 9: UI Responsiva
**Obiettivo**: Testare interfaccia su diversi dispositivi

**Passi**:
1. Testare su desktop (>1200px)
2. Testare su tablet (768-1200px)
3. Testare su mobile (<768px)
4. Verificare usabilità su ogni formato

**Risultato Atteso**:
- ✅ Layout adattivo per ogni dimensione
- ✅ Tabella scrollabile su mobile
- ✅ Pulsanti accessibili
- ✅ Testo leggibile
- ✅ Interazioni touch-friendly

### Test 10: Refresh e Aggiornamenti
**Obiettivo**: Testare aggiornamento dati

**Passi**:
1. Cliccare pulsante refresh
2. Verificare aggiornamento lista ODL
3. Controllare mantenimento filtri
4. Verificare reset selezioni se ODL non più disponibili

**Risultato Atteso**:
- ✅ Loading durante refresh
- ✅ Dati aggiornati
- ✅ Filtri mantenuti
- ✅ Selezioni validate automaticamente

## 🐛 Debug e Troubleshooting

### Console Browser
Aprire Developer Tools (F12) e monitorare:
- **Console**: Log dettagliati delle operazioni
- **Network**: Richieste API e risposte
- **Application**: LocalStorage per ruolo utente

### Errori Comuni

#### "Nessun ODL in attesa di nesting"
**Causa**: Database vuoto o ODL non in stato corretto
**Soluzione**: Eseguire `python seed_test_data_simple.py`

#### "Backend non raggiungibile"
**Causa**: Server FastAPI non avviato
**Soluzione**: Avviare backend con `uvicorn main:app --reload`

#### "Errore 422 - ODL già assegnato"
**Causa**: ODL selezionato già in un nesting attivo
**Soluzione**: Selezionare altri ODL o verificare stato nesting esistenti

#### "Errore di validazione"
**Causa**: Dati non validi o vincoli non rispettati
**Soluzione**: Verificare selezione e stato ODL

### Log Dettagliati
Con modalità debug attiva, ogni operazione genera log dettagliati:
```javascript
🔍 [Creazione Nesting Manuale] Errore dettagliato - 2024-12-25T10:30:00.000Z
Error object: {...}
Request data: {...}
Response data: {...}
HTTP Status: 422
```

## ✅ Checklist Finale

Prima di considerare il test completato, verificare:

- [ ] Caricamento iniziale funzionante
- [ ] Selezione singola e multipla ODL
- [ ] Filtri e ricerca operativi
- [ ] Validazione lato client attiva
- [ ] Creazione nesting con successo
- [ ] Gestione errori API robusta
- [ ] Modalità debug funzionante
- [ ] UI responsiva su tutti i dispositivi
- [ ] Refresh e aggiornamenti corretti
- [ ] Nessun errore critico in console

## 📊 Metriche di Successo

L'interfaccia è considerata funzionante se:
- ✅ **Usabilità**: Workflow intuitivo senza confusione
- ✅ **Affidabilità**: Gestione errori senza crash
- ✅ **Performance**: Caricamento < 2 secondi
- ✅ **Accessibilità**: Funzionante su tutti i dispositivi
- ✅ **Debug**: Informazioni tecniche complete per sviluppatori

## 🎉 Conclusione

Questa interfaccia fornisce un sistema completo per la selezione degli ODL per nesting manuale con:
- Validazione robusta lato client e server
- Gestione errori avanzata con suggerimenti specifici
- Modalità debug per sviluppatori
- UI responsiva e intuitiva
- Feedback visivo in tempo reale

Il sistema è pronto per l'uso in produzione e fornisce tutti gli strumenti necessari per una gestione efficace del nesting manuale. 