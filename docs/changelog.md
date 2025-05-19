# Changelog del Progetto CarbonPilot

## Versioni

### [19/05/2025 - v0.2.0] Modelli Database e Schemi

#### Modelli Database
- **Catalogo**: Modello per i Part Number univoci dell'azienda con descrizione, categoria e stato attivo.
- **Parte**: Modello per le parti associate a un PN del catalogo, con descrizione, peso, spessore, e informazioni sui cicli di cura e tool necessari.
- **Tool**: Modello per gli stampi utilizzati nella produzione, con dimensioni, disponibilità e specifiche tecniche.
- **Autoclave**: Modello per le autoclavi con dimensioni, capacità, specifiche tecniche e stato operativo.
- **CicloCura**: Modello per i cicli di cura con temperatura, pressione e impostazioni delle stasi.

#### Schemi Pydantic
- Creati schemi per ogni modello:
  - Schema base per le proprietà comuni
  - Schema di creazione con campi obbligatori 
  - Schema di aggiornamento con campi opzionali
  - Schema di risposta completo per le API

#### Migrazioni
- Creata migrazione manuale con Alembic per l'inizializzazione di tutte le tabelle del database.
- Configurata la relazione tra Parte e Catalogo (Foreign Key).
- Configurata la relazione tra Parte e CicloCura (Foreign Key).
- Configurata la relazione molti-a-molti tra Parte e Tool con tabella associativa.

### [17/05/2025 - v0.1.0] Setup Iniziale del Progetto

- Creata struttura del progetto con Next.js (frontend) e FastAPI (backend)
- Configurato Docker Compose per l'orchestrazione
- Impostati modelli base e configurazione delle migrazioni
- Inizializzato il database PostgreSQL
- Configurata l'API di base con autenticazione

---

_Il formato di questo changelog è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/)._ 