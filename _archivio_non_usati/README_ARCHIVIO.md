# 📁 Archivio File Non Utilizzati - CarbonPilot

Questa cartella contiene file che sono stati rimossi dal progetto principale durante la pulizia del **26/05/2025**.

## 📂 Struttura Archivio

### `/root_files/`
File di test e debug che erano nel root del progetto:
- `check_logs_db.py` - Script per verificare i log del database
- `check_database.py` - Script per verificare lo stato del database  
- `test_logging_system.py` - Sistema di test per il logging
- `test_backup.json` - File di backup di test (99KB)
- `test_api.py` - Script di test per le API

### `/tools/`
Script della cartella tools che non sono più necessari:
- `push_git.py` - Script per push automatico su git
- `README_SEED.md` - Documentazione per il seed (1 byte)
- `reset_database.py` - Script per reset completo del database
- `setup_db.py` - Script di setup database
- `run_migration.py` - Script per eseguire migrazioni
- `seed_test_data.py` - Versione obsoleta del seed (sostituita con quella aggiornata)

### `/frontend/`
File di test e debug del frontend:
- `test_role_page.html` - Pagina HTML di test per i ruoli
- `test_role_logic.js` - Logica JavaScript di test per i ruoli
- `test_sidebar_roles.html` - Test HTML per la sidebar dei ruoli
- `test_select_fix.md` - Documentazione per fix del componente select
- `test-select.tsx` - Componente React di test

### `/backend/`
File di test e debug del backend:
- `create_system_logs_table.py` - Script per creare tabella log di sistema
- `clean_logs.py` - Script per pulizia log
- `create_test_logs_v2.py` - Creazione log di test v2
- `check_db_logs.py` - Verifica log database
- `test_create_logs.py` - Test creazione log
- `test_logging.py` - Test sistema logging
- `test_two_level_nesting_api.py` - Test API nesting a due livelli
- `test_two_level_nesting.py` - Test nesting a due livelli
- `check_db.py` - Verifica database
- `frontend/` - Cartella frontend duplicata nel backend
- `inspect_models.py` - Script per ispezionare i modelli
- `update_version.py` - Script per aggiornare versioni

## 🎯 Struttura Finale Cartella `/tools/`

Dopo la pulizia, la cartella `tools/` contiene solo i 3 script fondamentali:
1. `snapshot_structure.py` - Genera snapshot della struttura del progetto
2. `seed_test_data.py` - Popola il database con dati di test (versione aggiornata)
3. `debug_local.py` - Utilities per debug locale (nuovo)

## ⚠️ Note Importanti

- **NON ELIMINARE** questa cartella senza aver verificato che tutti i file siano effettivamente inutili
- Alcuni script potrebbero tornare utili per debug futuri o per la versione 1.1+
- La versione di `seed_test_data.py` in archivio è quella meno aggiornata (19KB vs 20KB)
- I file HTML di test potrebbero essere utili per testing manuale futuro

## 🔄 Possibili Recuperi

Se dovessi aver bisogno di recuperare qualche file:
1. Copia il file dalla cartella archivio alla posizione originale
2. Verifica che non ci siano conflitti con la versione attuale
3. Aggiorna eventuali import o riferimenti

## 📊 Statistiche Pulizia

- **File spostati**: ~25 file
- **Spazio liberato**: ~150KB di file di test
- **Cartelle consolidate**: tools/ ora ha solo 3 script essenziali
- **Duplicati rimossi**: frontend/ dal backend, versioni obsolete di script

---
*Archivio creato durante la pulizia del progetto - Prompt Cursor 10* 