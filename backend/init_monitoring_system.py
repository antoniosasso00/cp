#!/usr/bin/env python3
"""
Script per inizializzare il sistema di monitoraggio ODL
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import random

# Aggiungi il percorso del backend al PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_odl_logs_table():
    """Crea la tabella odl_logs se non esiste"""
    
    db_path = "carbonpilot.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} non trovato")
        return False
    
    # SQL per creare la tabella odl_logs
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS odl_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        odl_id INTEGER NOT NULL,
        evento VARCHAR(100) NOT NULL,
        stato_precedente VARCHAR(50),
        stato_nuovo VARCHAR(50) NOT NULL,
        descrizione TEXT,
        responsabile VARCHAR(100),
        nesting_id INTEGER,
        autoclave_id INTEGER,
        schedule_entry_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (odl_id) REFERENCES odl(id),
        FOREIGN KEY (nesting_id) REFERENCES nesting_results(id),
        FOREIGN KEY (autoclave_id) REFERENCES autoclavi(id),
        FOREIGN KEY (schedule_entry_id) REFERENCES schedule_entries(id)
    );
    """
    
    # Indici per migliorare le performance
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_odl_id ON odl_logs(odl_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_timestamp ON odl_logs(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_nesting_id ON odl_logs(nesting_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_autoclave_id ON odl_logs(autoclave_id);",
        "CREATE INDEX IF NOT EXISTS idx_odl_logs_schedule_entry_id ON odl_logs(schedule_entry_id);"
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crea la tabella
        cursor.execute(create_table_sql)
        print("✅ Tabella odl_logs creata")
        
        # Crea gli indici
        for index_sql in create_indexes_sql:
            cursor.execute(index_sql)
        print("✅ Indici creati")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def create_sample_logs():
    """Crea log di esempio per ODL esistenti"""
    
    db_path = "carbonpilot.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ottieni tutti gli ODL esistenti
        cursor.execute("SELECT id, status, created_at FROM odl ORDER BY id")
        odl_list = cursor.fetchall()
        
        if not odl_list:
            print("⚠️ Nessun ODL trovato nel database")
            return
        
        print(f"📋 Trovati {len(odl_list)} ODL")
        
        # Verifica se ci sono già log
        cursor.execute("SELECT COUNT(*) FROM odl_logs")
        existing_logs = cursor.fetchone()[0]
        
        if existing_logs > 0:
            print(f"⚠️ Trovati {existing_logs} log esistenti. Vuoi continuare? (y/n)")
            response = input().lower()
            if response != 'y':
                print("❌ Operazione annullata")
                return
        
        # Responsabili di esempio
        responsabili = ["Sistema", "Mario Rossi", "Luca Bianchi", "Anna Verdi", "Paolo Neri"]
        
        # Eventi possibili per stato
        eventi_per_stato = {
            "Preparazione": ["creato", "priorita_modificata", "note_aggiornate"],
            "Laminazione": ["cambio_stato_laminazione", "avvio_laminazione"],
            "In Coda": ["cambio_stato_in_coda", "in_attesa_nesting"],
            "Attesa Cura": ["cambio_stato_attesa_cura", "pronto_per_nesting"],
            "Cura": ["assegnato_nesting", "avvio_cura", "caricato_autoclave"],
            "Finito": ["completato_cura", "finito"]
        }
        
        logs_creati = 0
        
        for odl_id, status, created_at in odl_list:
            # Crea log di creazione
            timestamp_creazione = created_at
            cursor.execute("""
                INSERT INTO odl_logs (odl_id, evento, stato_nuovo, descrizione, responsabile, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                odl_id,
                "creato",
                "Preparazione",
                "ODL creato nel sistema",
                random.choice(responsabili),
                timestamp_creazione
            ))
            logs_creati += 1
            
            # Simula progressione attraverso gli stati
            stati_progressione = ["Preparazione", "Laminazione", "In Coda", "Attesa Cura"]
            if status in ["Cura", "Finito"]:
                stati_progressione.extend(["Cura"])
            if status == "Finito":
                stati_progressione.append("Finito")
            
            # Crea log per ogni transizione di stato
            current_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            stato_precedente = None
            
            for i, stato in enumerate(stati_progressione[1:], 1):
                if stato == status or i <= stati_progressione.index(status):
                    # Aggiungi tempo casuale tra le transizioni (1-24 ore)
                    current_time += timedelta(hours=random.randint(1, 24))
                    
                    # Scegli evento appropriato
                    eventi_possibili = eventi_per_stato.get(stato, ["cambio_stato"])
                    evento = random.choice(eventi_possibili)
                    
                    # Descrizione basata sull'evento
                    if evento.startswith("cambio_stato"):
                        descrizione = f"Cambio stato da '{stati_progressione[i-1]}' a '{stato}'"
                    elif evento == "assegnato_nesting":
                        descrizione = f"ODL assegnato al nesting per autoclave"
                    elif evento == "avvio_cura":
                        descrizione = f"Avviato ciclo di cura"
                    elif evento == "completato_cura":
                        descrizione = f"Completato ciclo di cura"
                    else:
                        descrizione = f"Evento: {evento}"
                    
                    cursor.execute("""
                        INSERT INTO odl_logs (odl_id, evento, stato_precedente, stato_nuovo, descrizione, responsabile, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        odl_id,
                        evento,
                        stati_progressione[i-1] if i > 0 else None,
                        stato,
                        descrizione,
                        random.choice(responsabili),
                        current_time.isoformat()
                    ))
                    logs_creati += 1
                    
                    # Aggiungi eventi intermedi casuali
                    if random.random() < 0.3:  # 30% di probabilità
                        current_time += timedelta(minutes=random.randint(30, 180))
                        evento_intermedio = random.choice(["note_aggiornate", "priorita_modificata"])
                        cursor.execute("""
                            INSERT INTO odl_logs (odl_id, evento, stato_nuovo, descrizione, responsabile, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            odl_id,
                            evento_intermedio,
                            stato,
                            f"Evento intermedio: {evento_intermedio}",
                            random.choice(responsabili),
                            current_time.isoformat()
                        ))
                        logs_creati += 1
        
        conn.commit()
        print(f"✅ Creati {logs_creati} log di esempio")
        
        # Mostra statistiche
        cursor.execute("""
            SELECT evento, COUNT(*) as count 
            FROM odl_logs 
            GROUP BY evento 
            ORDER BY count DESC
        """)
        stats = cursor.fetchall()
        
        print("\n📊 Statistiche log creati:")
        for evento, count in stats:
            print(f"  - {evento}: {count}")
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dei log: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def main():
    """Funzione principale"""
    print("🚀 Inizializzazione sistema di monitoraggio ODL...")
    
    # Step 1: Crea tabella odl_logs
    print("\n📋 Step 1: Creazione tabella odl_logs")
    if not create_odl_logs_table():
        print("❌ Errore nella creazione della tabella")
        return
    
    # Step 2: Crea log di esempio
    print("\n📋 Step 2: Creazione log di esempio")
    create_sample_logs()
    
    print("\n✅ Inizializzazione completata!")
    print("\n🔗 Ora puoi:")
    print("  1. Avviare il backend: cd backend && python -m uvicorn main:app --reload")
    print("  2. Avviare il frontend: cd frontend && npm run dev")
    print("  3. Visitare: http://localhost:3000/dashboard/odl/monitoring")

if __name__ == "__main__":
    main() 