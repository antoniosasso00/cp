# 🛠️ Tools - Strumenti di Sviluppo CarbonPilot

Questa directory contiene strumenti utili per lo sviluppo e la manutenzione del progetto CarbonPilot.

## 📋 Script Disponibili

### 🧠 `print_schema_summary.py` - Riassunto Schema Database

Script per generare un riassunto completo dello schema del database, utile per:
- Avere una visione d'insieme di tutti i modelli
- Verificare relazioni e foreign keys
- Supportare lo sviluppo con informazioni precise sui campi
- Documentazione automatica dello schema

#### 🚀 Utilizzo

```bash
# Stampa il riassunto a schermo (con emoji)
python tools/print_schema_summary.py

# Salva in un file con formato compatto (senza emoji)
python tools/print_schema_summary.py --output docs/schema_summary.txt --compact

# Mostra le opzioni disponibili
python tools/print_schema_summary.py --help
```

#### 📊 Output

Lo script mostra per ogni modello:
- **Nome del modello** e tabella corrispondente
- **Campi**: nome, tipo, vincoli (PK, FK, UNIQUE, INDEX, NOT NULL)
- **Foreign Keys**: relazioni con altre tabelle
- **Relazioni**: relationship SQLAlchemy con cardinalità
- **Documentazione**: commenti sui campi (se presenti)

#### 🎯 Esempio Output

```
📄 Modello: ODL
   Tabella: odl
   📋 Campi:
      • id: Integer | PK | INDEX | NOT NULL
      • parte_id: Integer | INDEX | NOT NULL | FK -> parti.id
        📝 ID della parte associata all'ordine di lavoro
      • tool_id: Integer | INDEX | NOT NULL | FK -> tools.id
        📝 ID del tool utilizzato per l'ordine di lavoro
      • status: Enum(Preparazione, Laminazione, In Coda, Attesa Cura, Cura, Finito)
        📝 Stato corrente dell'ordine di lavoro
   🔗 Relazioni:
      • parte: one-to-one -> Parte (bidirectional)
      • tool: one-to-one -> Tool (bidirectional)
      • logs: one-to-many -> ODLLog (bidirectional)
```

### 🌱 Altri Script

- **`seed_test.py`**: Popola il database con dati di test
- **`seed_full.py`**: Popola il database con un dataset completo
- **`debug_local.py`**: Strumenti di debug per sviluppo locale
- **`snapshot_structure.py`**: Crea snapshot della struttura del progetto

## 🔧 Requisiti

Tutti gli script richiedono:
- Python 3.8+
- Dipendenze del progetto installate (`pip install -r requirements.txt`)
- Essere eseguiti dalla directory root del progetto

## 📝 Note per Sviluppatori

- Gli script sono progettati per essere eseguiti dalla directory root del progetto
- Utilizzano il path relativo `backend/` per importare i modelli
- Gestiscono automaticamente l'importazione dei modelli SQLAlchemy
- Sono compatibili sia con SQLite (sviluppo) che PostgreSQL (produzione)

## 🚀 Aggiungere Nuovi Script

Quando aggiungi nuovi script in questa directory:

1. **Documenta** l'uso nel README
2. **Aggiungi commenti** esplicativi nel codice
3. **Gestisci gli errori** in modo appropriato
4. **Testa** con diversi scenari
5. **Segui** le convenzioni di naming del progetto 