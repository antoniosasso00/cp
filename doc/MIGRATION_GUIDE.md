# Guida alle Migrazioni del Database CarbonPilot

Questa guida spiega come utilizzare gli strumenti creati per gestire le migrazioni del database in CarbonPilot.

## 📋 Prerequisiti

Prima di iniziare, assicurati di avere:

1. Python 3.8+ installato
2. Ambiente virtuale attivato (`.venv`)
3. PostgreSQL in esecuzione localmente
4. Database `carbonpilot` creato

## 🛠️ Strumenti Disponibili

### 1. Script Principale: `tools/run_migration.py`

Questo è lo script principale per gestire le migrazioni. Supporta sia l'ambiente locale che Docker.

#### Utilizzo Base
```bash
# Attiva l'ambiente virtuale
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Esegui lo script
python tools/run_migration.py "descrizione della migrazione"
```

#### Funzionalità
- Verifica automatica della connessione al database
- Gestione delle variabili d'ambiente
- Supporto per migrazioni locali e Docker
- Gestione degli errori e rollback automatico

### 2. Script di Supporto: `tools/apply_schema_changes.py`

Utilizzato per applicare modifiche manuali al database quando necessario.

#### Utilizzo
```bash
python tools/apply_schema_changes.py
```

## 🔄 Processo di Migrazione

### 1. Preparazione
1. Verifica che il database sia accessibile
2. Assicurati di avere un backup del database
3. Attiva l'ambiente virtuale

### 2. Creazione della Migrazione
```bash
python tools/run_migration.py "descrizione chiara della modifica"
```

### 3. Verifica della Migrazione
1. Controlla il file di migrazione generato in `backend/migrations/versions/`
2. Verifica che le modifiche siano corrette
3. Testa la migrazione in un ambiente di sviluppo

### 4. Applicazione della Migrazione
```bash
# La migrazione viene applicata automaticamente da run_migration.py
# Se necessario, puoi applicarla manualmente:
alembic upgrade head
```

## ⚠️ Gestione degli Errori

### Problemi Comuni

1. **Errore di Connessione**
   - Verifica che PostgreSQL sia in esecuzione
   - Controlla le credenziali in `alembic.ini`
   - Assicurati che il database esista

2. **Errore nella Migrazione**
   - Controlla il log per dettagli
   - Usa `alembic downgrade -1` per tornare indietro
   - Se necessario, usa `apply_schema_changes.py` per correzioni manuali

3. **Conflitti di Revisione**
   - Verifica lo storico delle migrazioni con `alembic history`
   - Assicurati che le revisioni siano in sequenza
   - Se necessario, crea una nuova migrazione di correzione

## 🔧 Configurazione

### File di Configurazione

1. **alembic.ini**
   - Configurazione principale di Alembic
   - URL del database e altre impostazioni

2. **env.py**
   - Configurazione dell'ambiente di migrazione
   - Gestione delle connessioni al database

### Variabili d'Ambiente

Le variabili d'ambiente vengono gestite automaticamente da `run_migration.py`:

```python
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "carbonpilot"
```

## 📝 Best Practices

1. **Naming delle Migrazioni**
   - Usa nomi descrittivi e chiari
   - Includi il tipo di modifica (add, remove, modify)
   - Esempio: "add_user_roles" o "remove_unused_fields"

2. **Struttura delle Migrazioni**
   - Mantieni le migrazioni atomiche
   - Includi sempre le funzioni `upgrade()` e `downgrade()`
   - Documenta le modifiche nei commenti

3. **Testing**
   - Testa sempre le migrazioni in un ambiente di sviluppo
   - Verifica il rollback con `downgrade()`
   - Controlla l'integrità dei dati dopo la migrazione

## 🔍 Debugging

### Comandi Utili

```bash
# Visualizza lo storico delle migrazioni
alembic history

# Verifica lo stato corrente
alembic current

# Visualizza la prossima migrazione
alembic next

# Visualizza la migrazione precedente
alembic prev
```

### Logging

- I log delle migrazioni vengono salvati in `backend/migrations/logs/`
- Usa `--verbose` per log più dettagliati
- Controlla sempre i log in caso di errori

## 📚 Risorse Aggiuntive

- [Documentazione Alembic](https://alembic.sqlalchemy.org/)
- [Documentazione SQLAlchemy](https://docs.sqlalchemy.org/)
- [Best Practices PostgreSQL](https://www.postgresql.org/docs/current/)

---

_Questa guida è stata creata per il progetto CarbonPilot e viene aggiornata regolarmente._ 