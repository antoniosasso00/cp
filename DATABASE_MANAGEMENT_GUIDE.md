# 🗄️ Guida alla Gestione Database - CarbonPilot

## 📋 Panoramica

Le funzioni di gestione database sono state implementate nel frontend di CarbonPilot per permettere agli amministratori di gestire facilmente i dati del sistema. Queste funzionalità sono accessibili dalla sezione **Admin > Impostazioni** del dashboard.

## 🎯 Funzionalità Disponibili

### 📤 Export Database
**Scopo**: Creare un backup completo del database in formato JSON

**Come utilizzare**:
1. Naviga su `Dashboard > Admin > Impostazioni`
2. Scorri fino alla sezione "Gestione Database"
3. Clicca su "Esporta Database"
4. Il file verrà scaricato automaticamente con nome `carbonpilot_backup_YYYYMMDD_HHMMSS.json`

**Cosa include**:
- Tutti i dati di tutte le tabelle
- Metadati di export (timestamp, tipo database)
- Struttura completa del database
- Conteggio record per tabella

### 📥 Import Database
**Scopo**: Ripristinare il database da un file di backup JSON

**Come utilizzare**:
1. Naviga su `Dashboard > Admin > Impostazioni`
2. Scorri fino alla sezione "Gestione Database"
3. Clicca su "Importa Database"
4. Seleziona un file JSON di backup
5. Verifica le informazioni del file mostrate
6. Clicca "Importa" per confermare

**⚠️ Attenzione**:
- Questa operazione **sovrascrive** tutti i dati esistenti
- Assicurati di avere un backup aggiornato prima di procedere
- L'operazione non può essere annullata

### 🗑️ Reset Database
**Scopo**: Svuotare completamente il database eliminando tutti i dati

**Come utilizzare**:
1. Naviga su `Dashboard > Admin > Impostazioni`
2. Scorri fino alla sezione "Gestione Database"
3. Clicca su "Reset Database"
4. Leggi attentamente l'avviso di sicurezza
5. Digita "reset" nel campo di conferma
6. Clicca "Conferma Reset"

**⚠️ ATTENZIONE**:
- Questa operazione è **IRREVERSIBILE**
- Elimina TUTTI i dati: ODL, autoclavi, parti, tool, cicli di cura, dati storici
- Utilizzare solo per reset completo del sistema
- Assicurati di avere un backup prima di procedere

## 🔧 Dettagli Tecnici

### 🌐 Endpoint Backend Utilizzati

| Operazione | Endpoint | Metodo | Descrizione |
|------------|----------|--------|-------------|
| Export | `/api/admin/backup` | GET | Scarica backup completo JSON |
| Import | `/api/admin/restore` | POST | Carica file backup e ripristina |
| Reset | `/api/admin/database/reset` | POST | Svuota tutte le tabelle |
| Info | `/api/admin/database/info` | GET | Ottieni statistiche database |
| Status | `/api/admin/database/status` | GET | Verifica salute database |

### 🎨 Componenti UI Utilizzati

- **Card**: Container principale per le sezioni
- **Dialog**: Modali per conferme e selezione file
- **Button**: Azioni principali con stati di loading
- **Alert**: Messaggi informativi e di warning
- **Input**: Selezione file e conferma operazioni
- **Toast**: Notifiche di successo/errore

### 🔒 Sicurezza e Validazioni

#### Export Database
- ✅ Nessuna validazione richiesta (operazione sicura)
- ✅ Feedback immediato con nome file generato
- ✅ Gestione errori con messaggi descrittivi

#### Import Database
- ✅ Validazione formato file (.json only)
- ✅ Preview informazioni file (nome, dimensione)
- ✅ Conferma esplicita richiesta
- ✅ Validazione struttura JSON lato backend

#### Reset Database
- ✅ Doppia conferma richiesta
- ✅ Parola chiave "reset" obbligatoria
- ✅ Alert di warning prominente
- ✅ Disabilitazione pulsante fino a conferma valida

## 📊 Informazioni Database

La sezione mostra in tempo reale:
- **Tipo database**: SQLite (Sviluppo) / PostgreSQL (Produzione)
- **Stato connessione**: Indicatore visivo dello stato
- **Tabelle totali**: Numero di tabelle nel database
- **Record totali**: Numero totale di record in tutte le tabelle

Le informazioni vengono aggiornate automaticamente dopo ogni operazione.

## 🚨 Scenari d'Uso Comuni

### 🔄 Backup Periodico
```
1. Export Database (settimanale/mensile)
2. Archiviare file in location sicura
3. Verificare integrità backup periodicamente
```

### 🔧 Migrazione Dati
```
1. Export Database dal sistema sorgente
2. Import Database nel sistema destinazione
3. Verificare integrità dati post-migrazione
```

### 🧪 Reset per Testing
```
1. Export Database (backup sicurezza)
2. Reset Database (pulizia completa)
3. Caricamento dati di test
4. Import Database (ripristino se necessario)
```

### 🆘 Ripristino d'Emergenza
```
1. Identificare backup più recente
2. Reset Database (se necessario)
3. Import Database dal backup
4. Verificare funzionalità sistema
```

## ⚠️ Best Practices

### 📅 Backup
- **Frequenza**: Backup settimanali minimi, giornalieri consigliati
- **Archiviazione**: Conservare backup in location multiple
- **Naming**: I file hanno timestamp automatico per identificazione
- **Verifica**: Testare periodicamente il processo di restore

### 🔒 Sicurezza
- **Accesso**: Solo utenti ADMIN possono accedere a queste funzioni
- **Conferme**: Sempre richiedere conferma per operazioni distruttive
- **Audit**: Tutte le operazioni vengono loggate nel sistema
- **Backup pre-operazione**: Sempre fare backup prima di import/reset

### 🚀 Performance
- **File size**: I backup possono essere grandi con molti dati
- **Timeout**: Operazioni su database grandi possono richiedere tempo
- **Memoria**: Import di file grandi richiede memoria sufficiente
- **Rete**: Upload di file grandi richiede connessione stabile

## 🐛 Troubleshooting

### ❌ Errori Comuni

#### "Errore HTTP: 500"
- **Causa**: Problema lato server
- **Soluzione**: Verificare log backend, riavviare servizi se necessario

#### "File JSON non valido"
- **Causa**: File corrotto o formato errato
- **Soluzione**: Utilizzare solo file generati dall'export del sistema

#### "Parola chiave di conferma non valida"
- **Causa**: Non è stato digitato esattamente "reset"
- **Soluzione**: Digitare "reset" (minuscolo, senza spazi)

#### "Nessun file selezionato"
- **Causa**: Tentativo di import senza selezionare file
- **Soluzione**: Selezionare un file .json valido prima di procedere

### 🔍 Debug

#### Verificare Stato Backend
```bash
curl http://localhost:8000/api/v1/admin/database/status
```

#### Verificare Informazioni Database
```bash
curl http://localhost:8000/api/v1/admin/database/info
```

#### Log Backend
Controllare i log del backend per errori dettagliati durante le operazioni.

## 📞 Supporto

Per problemi o domande relative alla gestione database:

1. **Verificare** questa documentazione
2. **Controllare** log di sistema per errori
3. **Testare** endpoint backend direttamente
4. **Contattare** il team di sviluppo con dettagli specifici

---

**Versione**: v1.4.1  
**Ultimo aggiornamento**: 2025-01-27  
**Compatibilità**: CarbonPilot v1.4.0+ 