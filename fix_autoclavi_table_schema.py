#!/usr/bin/env python3
"""
🔧 Fix completo per la tabella autoclavi con schema corretto
"""

import sys
import os

# Cambia directory al backend
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append('.')

from sqlalchemy import text
from models.db import SessionLocal

def fix_autoclavi_table():
    """Ricrea la tabella autoclavi con schema corretto"""
    
    print("🔧 FIX COMPLETO TABELLA AUTOCLAVI")
    print("="*50)
    
    db = SessionLocal()
    try:
        # 1. Verifica schema attuale
        print("📊 Schema attuale tabella autoclavi:")
        result = db.execute(text("PRAGMA table_info(autoclavi)"))
        columns = result.fetchall()
        
        for col in columns:
            pk_status = "PK" if col[5] else ""
            null_status = "NOT NULL" if col[3] else "NULL"
            print(f"   {col[1]}: {col[2]} {null_status} {pk_status}")
        
        # 2. Rimuovi tabella esistente (i dati erano problematici)
        print(f"\n🗑️ Rimozione tabella autoclavi esistente...")
        db.execute(text("DROP TABLE IF EXISTS autoclavi"))
        
        # 3. Ricrea tabella con schema corretto
        print(f"📝 Creazione nuova tabella autoclavi...")
        db.execute(text("""
            CREATE TABLE autoclavi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                codice VARCHAR(50) UNIQUE,
                lunghezza FLOAT,
                larghezza_piano FLOAT,
                temperatura_max FLOAT,
                pressione_max FLOAT,
                max_load_kg FLOAT DEFAULT 1000.0,
                num_linee_vuoto INTEGER,
                stato VARCHAR(12) NOT NULL DEFAULT 'DISPONIBILE',
                produttore VARCHAR(100),
                anno_produzione INTEGER,
                note TEXT,
                use_secondary_plane BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 4. Crea indici
        print(f"🔗 Creazione indici...")
        db.execute(text("CREATE UNIQUE INDEX idx_autoclavi_nome ON autoclavi (nome)"))
        db.execute(text("CREATE INDEX idx_autoclavi_codice ON autoclavi (codice)"))
        db.execute(text("CREATE INDEX idx_autoclavi_stato ON autoclavi (stato)"))
        
        # 5. Aggiungi autoclavi di test
        print(f"🧪 Aggiunta autoclavi di test...")
        
        # Inserimento semplificato con valori diretti
        db.execute(text("""
            INSERT INTO autoclavi (
                nome, codice, lunghezza, larghezza_piano, 
                temperatura_max, pressione_max, max_load_kg, 
                num_linee_vuoto, stato, produttore, anno_produzione
            ) VALUES 
            ('Autoclave Alpha', 'ALP-001', 2000.0, 1200.0, 200.0, 8.0, 1000.0, 10, 'DISPONIBILE', 'MantaGroup', 2024),
            ('Autoclave Beta', 'BET-002', 1800.0, 1000.0, 180.0, 7.0, 800.0, 8, 'DISPONIBILE', 'MantaGroup', 2023),
            ('Autoclave Gamma', 'GAM-003', 2200.0, 1400.0, 220.0, 9.0, 1200.0, 12, 'DISPONIBILE', 'MantaGroup', 2024)
        """))
        
        db.commit()
        print(f"✅ Tabella ricreata con successo!")
        
        # 6. Verifica risultato
        print(f"\n🔍 Verifica nuova tabella:")
        result = db.execute(text("SELECT id, nome, codice, stato FROM autoclavi"))
        autoclavi_final = result.fetchall()
        
        for autoclave in autoclavi_final:
            print(f"   ✅ ID: {autoclave[0]} | Nome: {autoclave[1]} | Codice: {autoclave[2]} | Stato: {autoclave[3]}")
        
        print(f"\n📊 Schema finale:")
        result = db.execute(text("PRAGMA table_info(autoclavi)"))
        columns = result.fetchall()
        
        for col in columns:
            pk_status = "PK" if col[5] else ""
            null_status = "NOT NULL" if col[3] else "NULL"
            print(f"   {col[1]}: {col[2]} {null_status} {pk_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il fix: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_autoclavi_table()
    sys.exit(0 if success else 1) 