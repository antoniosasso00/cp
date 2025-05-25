# 🧹 Piano di Pulizia File Superflui - CarbonPilot

## 📋 File da Rimuovere dalla Root

### File di Test Temporanei
- `test_nesting_quick.py` - Test temporaneo appena creato
- `test_nesting_cicli_cura.py` - Test specifico per cicli di cura
- `check_nesting_states.py` - Check temporaneo stati nesting
- `test_frontend_connectivity.py` - Test connettività frontend
- `test_nesting_complete.py` - Test completo nesting
- `test_endpoints.py` - Test endpoint generici
- `test_nesting_assignment.py` - File vuoto (1 byte)
- `test_nesting_system.py` - Test sistema nesting
- `test_manual_nesting.py` - Test manuale nesting
- `check_implementation.py` - Check implementazione
- `test_endpoint.py` - Test endpoint singolo
- `debug_reports.py` - Debug report
- `test_fixes_complete.py` - File vuoto (1 byte)
- `test_fixes.py` - Test fix generici

### File JSON di Test
- `test_report_request.json`
- `test_report_produzione.json`
- `test_report.json`

### File di Documentazione Temporanea
- `NESTING_FIX_SUMMARY.md` - Riassunto fix (ora integrato)
- `FIX_APPLICATI.md` - Fix applicati (ora integrato)
- `MIGLIORAMENTI_ODL_COMPLETATI.md` - Miglioramenti completati
- `CORREZIONI_APPLICATE.md` - Correzioni applicate
- `debug_fix_log.md` - Log debug fix
- `MIGRATION_GUIDE.md` - Guida migrazione (duplicata)
- `README_DASHBOARD_DINAMICA.md` - README specifico dashboard
- `README_SCHEDULING_COMPLETE.md` - README scheduling
- `Cursor Prompts V1 Beta.md` - Prompts Cursor
- `project_structure.md` - Struttura progetto (1.9MB - molto grande)

### File di Sviluppo Temporanei
- `start_dev_fixed.bat` - Script batch di sviluppo

## 📁 File da Rimuovere da tools/

### File di Debug e Test
- `debug_local.py` - Debug locale
- `debug_status.py` - Debug status
- `test_odl_improvements.py` - Test miglioramenti ODL
- `test_autoclave.py` - Test autoclave
- `test_crud_endpoints.py` - Test CRUD endpoints
- `check_parti_issue.py` - Check issue parti
- `fix_parti_catalogo.py` - Fix parti catalogo (completato)

### File di Migrazione Temporanei
- `apply_schema_changes.py` - Applicazione schema changes
- `run_migration.py` - Esecuzione migrazioni
- `reset_alembic_version.py` - Reset versione Alembic
- `drop_all_tables.py` - Drop tabelle
- `MIGRATION_GUIDE.md` - Duplicato della root

### File di Utilità Temporanee
- `snapshot_structure.py` - Snapshot struttura
- `describe_models.py` - Descrizione modelli
- `inspect_models.py` - Ispezione modelli
- `push_git.py` - Push git automatico

## 📁 File da Mantenere

### Root
- `README.md` - Documentazione principale
- `docker-compose.yml` - Configurazione Docker
- `requirements.txt` - Dipendenze Python
- `carbonpilot.db` - Database principale
- `.gitignore`, `.gitattributes` - Configurazione Git
- `carbonpilot.code-workspace` - Workspace VS Code
- Directory: `backend/`, `frontend/`, `docs/`, `.git/`, `.venv/`, `.docker-cache/`

### tools/
- `seed_test_data.py` - Seeding dati di test (utile)
- `seed_demo_data.py` - Seeding dati demo (utile)
- `reset_database.py` - Reset database (utile per sviluppo)
- `setup_db.py` - Setup database
- `clean_pycache.py` - Pulizia cache Python

## 🎯 Azioni da Eseguire

1. **Backup**: Creare backup dei file importanti prima della rimozione
2. **Rimozione Graduale**: Rimuovere file in gruppi per verificare che non ci siano dipendenze
3. **Test**: Verificare che il sistema funzioni dopo ogni gruppo di rimozioni
4. **Aggiornamento Git**: Commit delle modifiche di pulizia

## 📊 Statistiche Pulizia

- **File da rimuovere dalla root**: ~20 file
- **File da rimuovere da tools/**: ~15 file
- **Spazio liberato stimato**: ~5-10 MB (principalmente project_structure.md)
- **File mantenuti**: File essenziali per il funzionamento del progetto 