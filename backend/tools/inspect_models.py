#!/usr/bin/env python
"""
Utility per ispezionare e testare i modelli del database CarbonPilot.
Questo script verifica che tutti i modelli siano correttamente definiti 
e che le migrazioni siano state applicate correttamente.
"""

import os
import sys
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Aggiungi la cartella principale al PATH per importare i moduli
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Importa i modelli
from models import (
    Base, Catalogo, Parte, Tool, Autoclave, CicloCura, 
    parte_tool_association
)
from schemas.autoclave import StatoAutoclaveEnum

# Configura la connessione al database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non definito nel file .env")

# Rimuovi il driver asyncpg per usare psycopg2
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def print_header(title):
    """Stampa un'intestazione formattata."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def inspect_table(model):
    """Ispeziona una tabella del database."""
    print_header(f"Tabella: {model.__tablename__}")
    
    inspector = inspect(engine)
    
    # Verifica se la tabella esiste
    if not inspector.has_table(model.__tablename__):
        print(f"ERRORE: La tabella '{model.__tablename__}' non esiste nel database!")
        return
    
    # Ottieni le colonne della tabella
    columns = inspector.get_columns(model.__tablename__)
    
    print(f"Numero di colonne: {len(columns)}")
    print("\nDettaglio colonne:")
    
    for column in columns:
        nullable = "NULL" if column["nullable"] else "NOT NULL"
        default = f", DEFAULT: {column['default']}" if column["default"] else ""
        print(f"  - {column['name']} ({column['type']}) {nullable}{default}")
    
    # Verifica le chiavi primarie
    primary_keys = inspector.get_pk_constraint(model.__tablename__)
    print(f"\nChiavi primarie: {', '.join(primary_keys['constrained_columns'])}")
    
    # Verifica le chiavi esterne (solo per i modelli che ne hanno)
    if model.__tablename__ not in ['cataloghi', 'tools', 'autoclavi', 'cicli_cura']:
        foreign_keys = inspector.get_foreign_keys(model.__tablename__)
        print("\nChiavi esterne:")
        for fk in foreign_keys:
            print(f"  - {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")


def test_create_records():
    """Testa la creazione di record per ogni modello."""
    print_header("Test di creazione record")
    
    try:
        # Crea un record per Catalogo
        catalogo = Catalogo(
            part_number="PN12345",
            descrizione="Parte di test",
            categoria="Test",
            attivo=True,
            note="Nota di test"
        )
        session.add(catalogo)
        session.flush()
        print("✅ Catalogo creato con successo")
        
        # Crea un record per CicloCura
        ciclo_cura = CicloCura(
            nome="Ciclo Test",
            temperatura_max=180.0,
            pressione_max=6.0,
            temperatura_stasi1=160.0,
            pressione_stasi1=5.0,
            durata_stasi1=60,
            attiva_stasi2=True,
            temperatura_stasi2=120.0,
            pressione_stasi2=3.0,
            durata_stasi2=30,
            descrizione="Ciclo di test"
        )
        session.add(ciclo_cura)
        session.flush()
        print("✅ CicloCura creato con successo")
        
        # Crea un record per Tool
        tool = Tool(
            codice="T001",
            descrizione="Tool di test",
            lunghezza_piano=1000.0,
            larghezza_piano=500.0,
            disponibile=True,
            in_manutenzione=False,
            max_temperatura=200.0,
            max_pressione=7.0,
            note="Note tool di test"
        )
        session.add(tool)
        session.flush()
        print("✅ Tool creato con successo")
        
        # Crea un record per Autoclave
        autoclave = Autoclave(
            nome="Autoclave Test",
            codice="A001",
            lunghezza=3000.0,
            larghezza_piano=1200.0,
            num_linee_vuoto=4,
            temperatura_max=200.0,
            pressione_max=8.0,
            stato=StatoAutoclaveEnum.DISPONIBILE,
            in_manutenzione=False,
            produttore="TestManufacturer",
            anno_produzione=2025,
            note="Note autoclave di test"
        )
        session.add(autoclave)
        session.flush()
        print("✅ Autoclave creata con successo")
        
        # Crea un record per Parte
        parte = Parte(
            part_number=catalogo.part_number,
            descrizione_breve="Parte di test",
            peso=1500.0,
            spessore=2.5,
            num_valvole_richieste=2,
            ciclo_cura_id=ciclo_cura.id,
            note_produzione="Note produzione di test",
            cliente="Cliente Test"
        )
        parte.tools.append(tool)
        session.add(parte)
        session.flush()
        print("✅ Parte creata con successo")
        
        # Esegui query per verificare le relazioni
        parte_recuperata = session.query(Parte).filter_by(id=parte.id).first()
        print(f"\nRelazioni per Parte id={parte.id}:")
        print(f"  - Catalogo: {parte_recuperata.catalogo.part_number}")
        print(f"  - CicloCura: {parte_recuperata.ciclo_cura.nome}")
        print(f"  - Tools: {', '.join([t.codice for t in parte_recuperata.tools])}")
        
        # Esegui rollback per non salvare realmente i dati nel database
        session.rollback()
        print("\n⚠️ Rollback eseguito: nessun dato è stato salvato nel database")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERRORE durante il test: {e}")
        raise


def main():
    """Funzione principale."""
    print_header("Ispezione Modelli CarbonPilot")
    
    # Ispeziona tutte le tabelle
    inspect_table(Catalogo)
    inspect_table(CicloCura)
    inspect_table(Tool)
    inspect_table(Autoclave)
    inspect_table(Parte)
    
    # Testa la creazione di record
    test_create_records()
    
    print("\nIspezione completata.")


if __name__ == "__main__":
    main() 