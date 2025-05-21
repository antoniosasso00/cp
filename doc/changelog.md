# Changelog CarbonPilot

## [21/05/2025 - Sistema di Monitoraggio Tempi di Produzione]

### Funzionalità Aggiunte
- **Monitoraggio Tempi**: Implementato sistema di tracciamento dei tempi per fasi di laminazione, attesa cura e cura
- **Previsioni Automatiche**: Sistema intelligente di previsione basato sullo storico per stimare tempi di lavorazione
- **Dashboard Avanzata**: Nuovi grafici statistici per visualizzare i tempi medi per fase
- **Interfaccia ODL Migliorata**: Aggiunto pannello "Avanzamento Fasi" per gestire il flusso di lavoro

### Modifiche Tecniche
- Nuovo modello `TempoFase` con relazione verso `ODL`
- API REST completa con endpoint dedicato alle previsioni
- Interfaccia grafica per la gestione dei tempi con visualizzazione statistiche
- Sistema di calcolo automatico della durata fasi

### Impatti sul Database
- Nuova tabella `tempo_fasi` per tracciare i tempi di produzione 
- Enum personalizzato `tipo_fase` per limitare i valori possibili

### Note di Rilascio
Le previsioni diventano più accurate con l'accumularsi dei dati storici. Si consiglia di compilare i dati per almeno 10 cicli produttivi completi per ottenere previsioni significative.

## versione 0.6.1 - Correzioni visualizzazione tempi fasi
- Correzione dashboard: aggiunto widget per visualizzazione tempi medi di produzione con grafico
- Miglioramento monitoraggio tempo: visualizzazione dettagliata per ogni fase 
- Correzioni bug nella visualizzazione delle previsioni tempi di fase
- Ottimizzazione interfaccia utente per la gestione dei tempi

## versione 0.6.2 - Monitoraggio automatico tempi + interfaccia operatore
- **Automazione tempi**: Implementato monitoraggio automatico che registra tempi di fase ad ogni cambio di stato ODL
- **Interfaccia operatore**: Creata interfaccia dedicata `/dashboard/odl/[id]/avanza` per switch guidato di stato
- **Tracciamento completo**: Storico visibile dello stato dell'ODL con tempi registrati per fase
- **Seed avanzato**: Aggiornato sistema di seed con dati realistici per il monitoraggio tempi
- **Controllo coerenza**: Validazione automatica per evitare fasi sovrapposte e dati inconsistenti 