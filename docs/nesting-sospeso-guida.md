# 📋 Guida Utente: Gestione Nesting in Sospeso

## 🎯 Panoramica

La funzionalità di **Gestione Nesting in Sospeso** permette agli autoclavisti di gestire i nesting che sono stati creati automaticamente dal sistema ma non ancora confermati per l'avvio del processo di cura.

## 👤 Ruoli e Permessi

### Autoclavista
- ✅ **Può visualizzare** tutti i nesting in stato "SOSPESO"
- ✅ **Può confermare** nesting in sospeso (avvia processo di cura)
- ✅ **Può eliminare** nesting in sospeso (libera risorse)

### Responsabile
- ✅ **Può visualizzare** tutti i nesting (inclusi quelli sospesi)
- ✅ **Può gestire** nesting con funzionalità estese

## 🔄 Stati del Nesting

### SOSPESO
- **Descrizione**: Nesting creato automaticamente ma non ancora confermato
- **Caratteristiche**:
  - Autoclave è riservata (stato IN_USO)
  - ODL sono ancora in "Attesa Cura"
  - Può essere confermato o eliminato

### ATTIVO
- **Descrizione**: Nesting confermato e in corso di esecuzione
- **Caratteristiche**:
  - Processo di cura avviato
  - ODL passati in stato "Cura"
  - Non può essere modificato

## 🎮 Come Utilizzare la Funzionalità

### 1. Visualizzazione Nesting Sospesi

1. **Accedi alla dashboard autoclavista**
   - Vai su: `Dashboard > Autoclavista > Nesting`

2. **Filtra per nesting sospesi**
   - I nesting in stato "SOSPESO" sono evidenziati
   - Icona: ⏸️ (pausa)
   - Colore: Arancione/Giallo

### 2. Confermare un Nesting

#### Quando Confermare:
- ✅ Il carico è stato fisicamente inserito nell'autoclave
- ✅ L'autoclave è pronta per iniziare il ciclo di cura
- ✅ Tutti i controlli di sicurezza sono stati effettuati

#### Procedura:
1. **Individua il nesting** da confermare nella lista
2. **Clicca sul bottone "Conferma Carico"** 🟢
3. **Conferma l'azione** nel dialog che appare
4. **Verifica il risultato**:
   - Nesting passa a stato "ATTIVO"
   - ODL passano in stato "Cura"
   - Toast di conferma appare

#### Cosa Succede:
```
PRIMA:
├── Nesting: SOSPESO
├── ODL: Attesa Cura
└── Autoclave: IN_USO

DOPO:
├── Nesting: ATTIVO
├── ODL: Cura
└── Autoclave: IN_USO (continua)
```

### 3. Eliminare un Nesting

#### Quando Eliminare:
- ❌ Il carico non può essere inserito nell'autoclave
- ❌ L'autoclave ha problemi tecnici
- ❌ È necessario riorganizzare la produzione
- ❌ Gli ODL hanno cambiato priorità

#### Procedura:
1. **Individua il nesting** da eliminare nella lista
2. **Clicca sul bottone "Elimina Nesting"** 🔴
3. **Conferma l'eliminazione** nel dialog di avviso
4. **Verifica il risultato**:
   - Nesting viene rimosso dalla lista
   - ODL tornano disponibili per altri nesting
   - Autoclave viene liberata (se non ci sono altri nesting)
   - Toast di conferma appare

#### Cosa Succede:
```
PRIMA:
├── Nesting: SOSPESO
├── ODL: Attesa Cura (riservati)
└── Autoclave: IN_USO

DOPO:
├── Nesting: ELIMINATO
├── ODL: Attesa Cura (disponibili)
└── Autoclave: DISPONIBILE*

* Solo se non ci sono altri nesting attivi
```

## ⚠️ Validazioni e Limitazioni

### Conferma Nesting
- ❌ **Non possibile se**:
  - Nesting non è in stato SOSPESO
  - Autoclave è GUASTA o SPENTA
  - ODL non sono più in "Attesa Cura"

### Eliminazione Nesting
- ❌ **Non possibile se**:
  - Nesting non è in stato SOSPESO
  - Nesting è già ATTIVO o COMPLETATO

## 🔍 Monitoraggio e Log

### Tracciamento Operazioni
Tutte le operazioni sui nesting sospesi vengono registrate nei log di sistema:

- **Conferma**: `Nesting #123 confermato da autoclavista`
- **Eliminazione**: `Nesting #123 eliminato da autoclavista`
- **Dettagli**: ID autoclave, ODL coinvolti, timestamp

### Visualizzazione Log
- **Responsabile**: Può visualizzare tutti i log in `Dashboard > Responsabile > Log`
- **Autoclavista**: Può vedere le proprie operazioni

## 🚨 Gestione Errori

### Errori Comuni e Soluzioni

#### "Nesting non trovato"
- **Causa**: Il nesting è stato eliminato da un altro utente
- **Soluzione**: Aggiorna la pagina e riprova

#### "Autoclave non disponibile"
- **Causa**: L'autoclave è passata in stato GUASTO o SPENTA
- **Soluzione**: Verifica lo stato dell'autoclave e contatta la manutenzione

#### "ODL non più validi"
- **Causa**: Gli ODL sono stati modificati da un altro processo
- **Soluzione**: Aggiorna la pagina e verifica lo stato degli ODL

#### "Errore di connessione"
- **Causa**: Problemi di rete o backend non disponibile
- **Soluzione**: Verifica la connessione e riprova

## 💡 Best Practices

### Per Autoclavisti

1. **Controllo Fisico**
   - Verifica sempre che il carico sia correttamente posizionato prima di confermare
   - Controlla che l'autoclave sia pronta per il ciclo

2. **Gestione Priorità**
   - Conferma prima i nesting con ODL ad alta priorità
   - Elimina nesting che non possono essere processati tempestivamente

3. **Comunicazione**
   - Informa il responsabile di eventuali problemi
   - Documenta motivi di eliminazione nei log

### Per Responsabili

1. **Monitoraggio**
   - Controlla regolarmente i log per identificare pattern
   - Verifica che i nesting sospesi non rimangano troppo a lungo

2. **Ottimizzazione**
   - Analizza le eliminazioni frequenti per migliorare l'algoritmo di nesting
   - Coordina con gli autoclavisti per ottimizzare i flussi

## 📱 Interfaccia Utente

### Indicatori Visivi

| Stato | Icona | Colore | Azioni Disponibili |
|-------|-------|--------|-------------------|
| SOSPESO | ⏸️ | 🟡 Giallo | Conferma, Elimina |
| ATTIVO | ▶️ | 🟢 Verde | Visualizza |
| COMPLETATO | ✅ | 🔵 Blu | Visualizza, Report |

### Bottoni Azione

- **🟢 Conferma Carico**: Avvia il processo di cura
- **🔴 Elimina Nesting**: Rimuove il nesting e libera risorse
- **👁️ Visualizza**: Mostra dettagli del nesting

## 🔧 Risoluzione Problemi

### Problema: Bottoni non visibili
- **Verifica**: Sei loggato come autoclavista?
- **Verifica**: Il nesting è in stato SOSPESO?

### Problema: Conferma non funziona
- **Controlla**: Stato dell'autoclave
- **Controlla**: Stato degli ODL
- **Controlla**: Connessione di rete

### Problema: Eliminazione non funziona
- **Verifica**: Il nesting è ancora in stato SOSPESO?
- **Riprova**: Aggiorna la pagina e riprova

## 📞 Supporto

Per problemi tecnici o domande:
- **Responsabile di produzione**: Per questioni operative
- **Amministratore sistema**: Per problemi tecnici
- **Log di sistema**: Per tracciare operazioni e errori

---

**Versione documento**: 1.0  
**Ultimo aggiornamento**: 2024-01-XX  
**Autore**: Sistema CarbonPilot 